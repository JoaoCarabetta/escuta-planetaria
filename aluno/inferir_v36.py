#!/usr/bin/env python3
"""Roda o aluno v3.6 no arquivo inteiro e grava em `predicoes_v36` (tabela nova;
`predicoes_v32` não é tocada).

Guarda as PROBABILIDADES de toda classe de toda cabeça (JSON {classe: p}), não
só a decisão: a página mostra "palpite" ao lado da taxa de acerto medida, e o
aprendizado ativo precisa da margem.

Decisão por cabeça, com os mesmos limiares da avaliação (0,5 em toda sigmoide;
argmax no conteúdo) e as mesmas portas da rubrica:
  portao      classes com p > 0,5 (lista; pode vir vazia)
  carga, conteudo, despertar   só se literal decidido
  figura      só se figurado decidido
  tem_atrib   só se literal ou fala_do_sonhar decidido
  origem      só se tem_atrib decidido
  bandeira    sempre
Onde a porta não abre, a decisão é NULL — a probabilidade fica gravada mesmo
assim.

DUPLICATAS (canonico_de não nulo, 7.965): HERDAM do canônico, com
`herdado_de` preenchido. São o mesmo texto por construção da tabela; rodar de
novo gastaria tempo para produzir o mesmo número. Se o canônico não tiver
predição, a duplicata é classificada pelo próprio texto.

Retomável: pula ids já gravados. Grava a cada ~2.000 relatos.

  nohup python3 -u inferir_v36.py --aparelho=mps > inferencia_v36.log 2>&1 &
  python3 inferir_v36.py --n=2000          (teste)
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
MODELO = 'aluno_v36'
L = 0.5
FOLGA_MIN = 12
NOMES = dict(portao=PORTAO, carga=CARGA, conteudo=CONTEUDO, despertar=DESPERTAR,
             figura=FIGURA, tem_atrib=['tem_atrib'], origem=ORIGEM, bandeira=['bandeira'])
COLS = ['relato_id', 'modelo', 'p_portao', 'p_carga', 'p_conteudo', 'p_despertar',
        'p_figura', 'p_tem_atrib', 'p_origem', 'p_bandeira', 'p_literal', 'p_figurado',
        'portao', 'carga', 'conteudo', 'despertar', 'figura', 'tem_atrib', 'origem',
        'bandeira', 'margem_portao', 'n_janelas', 'herdado_de']


def criar(con):
    con.execute("""CREATE TABLE IF NOT EXISTS predicoes_v36 (
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
    """p: {cabeça: lista de probabilidades} de UM texto → tupla de colunas."""
    def d(k):
        return {n: round(x, 4) for n, x in zip(NOMES[k], p[k])}
    def lista(k):
        return [n for n, x in zip(NOMES[k], p[k]) if x > L]
    portao = lista('portao')
    lit, fig, fal = 'literal' in portao, 'figurado' in portao, 'fala_do_sonhar' in portao
    conteudo = CONTEUDO[max(range(2), key=lambda i: p['conteudo'][i])] if lit else None
    ta = int(p['tem_atrib'][0] > L) if (lit or fal) else None
    return (rid, MODELO,
            json.dumps(d('portao')), json.dumps(d('carga')), json.dumps(d('conteudo')),
            json.dumps(d('despertar')), json.dumps(d('figura')),
            round(p['tem_atrib'][0], 4), json.dumps(d('origem')), round(p['bandeira'][0], 4),
            round(p['portao'][0], 4), round(p['portao'][1], 4),
            json.dumps(portao),
            json.dumps(lista('carga')) if lit else None,
            conteudo,
            json.dumps(lista('despertar')) if lit else None,
            json.dumps(lista('figura')) if fig else None,
            ta,
            json.dumps(lista('origem')) if ta else None,
            int(p['bandeira'][0] > L),
            round(min(abs(x - L) for x in p['portao']), 4), nj, None)


def gravar(con, linhas):
    q = f"INSERT OR REPLACE INTO predicoes_v36 ({','.join(COLS)}) VALUES ({','.join('?'*len(COLS))})"
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
    feitos = {r[0] for r in con.execute('SELECT relato_id FROM predicoes_v36')}
    todos = [r[0] for r in con.execute('SELECT id FROM relatos WHERE canonico_de IS NULL ORDER BY id')]
    if '--orfas' in sys.argv:
        todos = [r[0] for r in con.execute('''SELECT r.id FROM relatos r WHERE r.canonico_de IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM predicoes_v36 p WHERE p.relato_id = r.canonico_de
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
    modelo.load_state_dict(torch.load(AQUI / 'aluno_v36.pt', map_location=ap))
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
    n = con.execute(f"""INSERT OR IGNORE INTO predicoes_v36 ({','.join(COLS)})
        SELECT r.id, p.modelo, p.p_portao, p.p_carga, p.p_conteudo, p.p_despertar, p.p_figura,
               p.p_tem_atrib, p.p_origem, p.p_bandeira, p.p_literal, p.p_figurado,
               p.portao, p.carga, p.conteudo, p.despertar, p.figura, p.tem_atrib, p.origem,
               p.bandeira, p.margem_portao, p.n_janelas, r.canonico_de
        FROM relatos r JOIN predicoes_v36 p ON p.relato_id = r.canonico_de
        WHERE r.canonico_de IS NOT NULL""").rowcount
    con.commit()
    orfas = con.execute("""SELECT count(*) FROM relatos r WHERE r.canonico_de IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM predicoes_v36 p WHERE p.relato_id = r.id)""").fetchone()[0]
    print(f'duplicatas herdadas: {n} · sem canônico predito: {orfas}', flush=True)
    if orfas:
        print('  rode de novo com --orfas para classificá-las pelo próprio texto', flush=True)
    print(f'fim · {n_feito} classificados em {(time.time()-t0)/3600:.2f} h', flush=True)


if __name__ == '__main__':
    main()
