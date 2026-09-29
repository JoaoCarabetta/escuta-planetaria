#!/usr/bin/env python3
"""Roda o afeto v2 (`afeto_v2.pt`, treinado só em literais) SÓ nos relatos que o
portão da página chama de literal, e grava em `predicoes_afeto_v2` (tabela nova;
predicoes_v35/v36 não são tocadas). Derivado de inferir_v36.py.

Literal = portão v3.5 com `literal`; sem v3.5, p_literal do v3.6 acima do corte
calibrado (aluno/limiar_portao_v36.json) — a mesma regra do planeta-v3/gerar.py.

O afeto v2 não tem opinião sobre portão nem bandeira (peso zero no treino): essas
colunas ficam NULL. Figura também fica NULL — figura continua do v3.6 (o v2
quebra nela). Decisões: carga, conteúdo, despertar sempre (é literal);
tem_atrib; origem só se tem_atrib. Limiar 0,5, como na avaliação.

Duplicatas herdam do canônico. Retomável: pula ids já gravados.

  nohup python3 -u inferir_afeto_v2.py --aparelho=mps > inferencia_afeto_v2.log 2>&1 &
  python3 inferir_afeto_v2.py --n=2000          (teste)
"""
import json
import sqlite3
import sys
import time
from pathlib import Path

import torch
from transformers import AutoTokenizer

from dados_v35 import CARGA, CONTEUDO, DESPERTAR, FIGURA, ORIGEM, PORTAO
from modelo_v35 import BASE, K_INFER, AlunoV35, janelas_de
from treinar_v35 import memoria_livre

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
MODELO = 'afeto_v2'
TABELA = 'predicoes_afeto_v2'
CORTE_LITERAL = json.load(open(Path(__file__).parent / 'limiar_portao_v36.json'))['p_literal']
L = 0.5
FOLGA_MIN = 12
NOMES = dict(portao=PORTAO, carga=CARGA, conteudo=CONTEUDO, despertar=DESPERTAR,
             figura=FIGURA, tem_atrib=['tem_atrib'], origem=ORIGEM, bandeira=['bandeira'])
COLS = ['relato_id', 'modelo', 'p_portao', 'p_carga', 'p_conteudo', 'p_despertar',
        'p_figura', 'p_tem_atrib', 'p_origem', 'p_bandeira', 'p_literal', 'p_figurado',
        'portao', 'carga', 'conteudo', 'despertar', 'figura', 'tem_atrib', 'origem',
        'bandeira', 'margem_portao', 'n_janelas', 'herdado_de']


def criar(con):
    con.execute(f"""CREATE TABLE IF NOT EXISTS {TABELA} (
        relato_id TEXT PRIMARY KEY, modelo TEXT NOT NULL,
        p_portao TEXT, p_carga TEXT, p_conteudo TEXT, p_despertar TEXT, p_figura TEXT,
        p_tem_atrib REAL, p_origem TEXT, p_bandeira REAL,
        p_literal REAL, p_figurado REAL,
        portao TEXT, carga TEXT, conteudo TEXT, despertar TEXT, figura TEXT,
        tem_atrib INTEGER, origem TEXT, bandeira INTEGER,
        margem_portao REAL, n_janelas INTEGER, herdado_de TEXT,
        feito_em TEXT DEFAULT (datetime('now')))""")
    con.commit()


def decidir(rid, p, nj):
    """p: {cabeça: lista de probabilidades} de UM texto (literal) → tupla de colunas."""
    def d(k):
        return {n: round(x, 4) for n, x in zip(NOMES[k], p[k])}
    def lista(k):
        return [n for n, x in zip(NOMES[k], p[k]) if x > L]
    conteudo = CONTEUDO[max(range(2), key=lambda i: p['conteudo'][i])]
    ta = int(p['tem_atrib'][0] > L)
    return (rid, MODELO,
            None, json.dumps(d('carga')), json.dumps(d('conteudo')),
            json.dumps(d('despertar')), None,
            round(p['tem_atrib'][0], 4), json.dumps(d('origem')), None,
            None, None,
            None,
            json.dumps(lista('carga')),
            conteudo,
            json.dumps(lista('despertar')),
            None,
            ta,
            json.dumps(lista('origem')) if ta else None,
            None,
            None, nj, None)


def gravar(con, linhas):
    q = f"INSERT OR REPLACE INTO {TABELA} ({','.join(COLS)}) VALUES ({','.join('?'*len(COLS))})"
    for tent in range(20):
        try:
            con.executemany(q, linhas); con.commit(); return
        except sqlite3.OperationalError as e:
            print(f'  banco ocupado ({e}); tentando de novo em 30 s', flush=True)
            time.sleep(30)
    raise RuntimeError('não consegui gravar')


def lotes_por_janela(itens, max_jan):
    """itens: [(rid, janelas)] já ordenados por tamanho → lotes com até max_jan janelas."""
    lote, n = [], 0
    for it in itens:
        k = len(it[1])
        if lote and n + k > max_jan:
            yield lote; lote, n = [], 0
        lote.append(it); n += k
    if lote:
        yield lote


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    ap = arg.get('--aparelho', 'mps')
    limite = int(arg.get('--n', 0))
    max_jan = int(arg.get('--janelas', 64))
    bloco = int(arg.get('--bloco', 2000))
    torch.set_num_threads(4)

    con = sqlite3.connect(DB, timeout=900)
    con.execute('PRAGMA busy_timeout=900000')
    criar(con)
    feitos = {r[0] for r in con.execute(f'SELECT relato_id FROM {TABELA}')}
    todos = [r[0] for r in con.execute('''SELECT r.id FROM relatos r
        LEFT JOIN predicoes_v35 a ON a.relato_id = r.id
        LEFT JOIN predicoes_v36 b ON b.relato_id = r.id
        WHERE r.canonico_de IS NULL
          AND (a.portao LIKE '%"literal"%' OR (a.relato_id IS NULL AND b.p_literal > ?))
        ORDER BY r.id''', (CORTE_LITERAL,))]
    if '--orfas' in sys.argv:
        todos = [r[0] for r in con.execute(f'''SELECT r.id FROM relatos r WHERE r.canonico_de IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM {TABELA} p WHERE p.relato_id = r.canonico_de
                                 AND p.herdado_de IS NULL)
            ORDER BY r.id''')]
        limite = limite or len(todos) + 1
    falta = [i for i in todos if i not in feitos]
    if limite:
        falta = falta[:limite]
    print(f'{len(todos)} canônicos · {len(feitos)} já feitos · {len(falta)} a classificar', flush=True)

    tk = AutoTokenizer.from_pretrained(BASE)
    cls, sep, pad = tk.cls_token_id, tk.sep_token_id, tk.pad_token_id
    modelo = AlunoV35().to(ap)
    modelo.load_state_dict(torch.load(AQUI / 'afeto_v2.pt', map_location=ap))
    modelo.eval()

    t0, n_feito, n_jan = time.time(), 0, 0
    for b0 in range(0, len(falta), bloco):
        ids = falta[b0:b0 + bloco]
        q = ','.join('?' * len(ids))
        tx = dict(con.execute(f'SELECT id, texto FROM relatos WHERE id IN ({q})', ids))
        itens = []
        for rid in ids:
            tok = tk(tx[rid] or '', add_special_tokens=False)['input_ids']
            itens.append((rid, janelas_de(tok, tk, K_INFER) or [[]]))
        itens.sort(key=lambda it: (len(it[1]), max(len(j) for j in it[1])))
        saida = []
        with torch.no_grad():
            for lote in lotes_por_janela(itens, max_jan):
                jans, dono = [], []
                for n, (_, js) in enumerate(lote):
                    for j in js:
                        jans.append([cls] + j + [sep]); dono.append(n)
                T = max(len(j) for j in jans)
                idt = torch.full((len(jans), T), pad, dtype=torch.long)
                mas = torch.zeros((len(jans), T), dtype=torch.long)
                for w, j in enumerate(jans):
                    idt[w, :len(j)] = torch.tensor(j); mas[w, :len(j)] = 1
                s = modelo(idt.to(ap), mas.to(ap), torch.tensor(dono).to(ap), len(lote))
                pr = {k: (torch.softmax(v, -1) if k == 'conteudo' else torch.sigmoid(v)).cpu().tolist()
                      for k, v in s.items()}
                for n, (rid, js) in enumerate(lote):
                    saida.append(decidir(rid, {k: pr[k][n] for k in pr}, len(js)))
                n_jan += len(jans)
        gravar(con, saida)
        n_feito += len(ids)
        if ap == 'mps':
            torch.mps.empty_cache()
        dt = time.time() - t0
        ritmo = n_feito / dt
        livre = memoria_livre()
        print(f'  {n_feito}/{len(falta)} · {ritmo:.1f} textos/s · {n_jan/dt:.1f} janelas/s · '
              f'ETA {(len(falta)-n_feito)/ritmo/3600:.2f} h · livre {livre}%', flush=True)
        if livre < FOLGA_MIN:
            print('  memória apertada: pausando 30 s', flush=True)
            time.sleep(30)

    if limite:
        print(f'teste · {n_feito} em {(time.time()-t0)/60:.1f} min', flush=True)
        return
    # duplicatas herdam do canônico
    n = con.execute(f"""INSERT OR IGNORE INTO {TABELA} ({','.join(COLS)})
        SELECT r.id, p.modelo, p.p_portao, p.p_carga, p.p_conteudo, p.p_despertar, p.p_figura,
               p.p_tem_atrib, p.p_origem, p.p_bandeira, p.p_literal, p.p_figurado,
               p.portao, p.carga, p.conteudo, p.despertar, p.figura, p.tem_atrib, p.origem,
               p.bandeira, p.margem_portao, p.n_janelas, r.canonico_de
        FROM relatos r JOIN {TABELA} p ON p.relato_id = r.canonico_de
        WHERE r.canonico_de IS NOT NULL""").rowcount
    con.commit()
    orfas = con.execute(f"""SELECT count(*) FROM relatos r WHERE r.canonico_de IS NOT NULL
        AND r.canonico_de IN (SELECT relato_id FROM {TABELA})
        AND NOT EXISTS (SELECT 1 FROM {TABELA} p WHERE p.relato_id = r.id)""").fetchone()[0]
    print(f'duplicatas herdadas: {n} · sem canônico predito: {orfas}', flush=True)
    if orfas:
        print('  rode de novo com --orfas para classificá-las pelo próprio texto', flush=True)
    print(f'fim · {n_feito} classificados em {(time.time()-t0)/3600:.2f} h', flush=True)


if __name__ == '__main__':
    main()
