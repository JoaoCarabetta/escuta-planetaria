#!/usr/bin/env python3
"""Os 15 mil de AFETO (28/09, madrugada) — para ensinar ao aluno o que ele
ainda não lê: carga, despertar e atribuição.

Por que sorteado e não pescado: o aluno v3.5 errou os valores raros porque
aprendeu com bolsas pescadas por pista (afeto, atribuição), e o arquivo real
é outra população. Aqui o sorteio é UNIFORME entre os sonhos dormidos — a
proporção que ele vai encontrar. Soma-se uma fatia dos mais indecisos (menor
margem do portão), onde cada anotação ensina mais (aprendizado ativo).

  13.500  sorteio uniforme entre p_literal ≥ 0,5 (canônicos)
   1.500  os de menor margem do portão com p_literal ≥ 0,3

Fora: tudo o que já foi anotado (anotacoes_v3, v3.5, prova, revisão cega),
qualquer texto escondido pelo cuidado (conferência de risco ou bandeira do
aluno). Anotador: Sonnet (teste de 27/09: 90% de acordo com o Opus na carga,
contra 82% do aluno e 51% do Haiku). Semente 2809.

  python3 lotes_afeto15k.py  →  rubrica/lotes/afeto15k/a_<k>.jsonl (200 cada)
"""
import glob
import json
import sqlite3
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
SAIDA = AQUI / 'lotes' / 'afeto15k'


def ids_jsonl(padrao, campo='id'):
    s = set()
    for f in glob.glob(str(AQUI / 'lotes' / padrao), recursive=True):
        for l in open(f):
            try: s.add(json.loads(l)[campo])
            except Exception: pass
    return s


def main():
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    fora = {r[0] for r in con.execute('SELECT relato_id FROM anotacoes_v3')}
    fora |= {r[0] for r in con.execute('SELECT relato_id FROM amostra_prova')}
    fora |= ids_jsonl('v3*/**/*.jsonl') | ids_jsonl('revisao_cega_fitipe.jsonl') | ids_jsonl('cuidado_manual.jsonl')
    for f in glob.glob(str(AQUI / 'lotes' / 'risco*' / '*conferid*.jsonl')) + glob.glob(str(AQUI / 'lotes' / 'risco_conferidos*.jsonl')):
        for l in open(f):
            x = json.loads(l)
            if x.get('bandeira'): fora.add(x['id'])
    linhas = con.execute("""SELECT p.relato_id, p.p_literal, p.margem_portao, p.bandeira
        FROM predicoes_v35 p JOIN relatos r ON r.id = p.relato_id
        WHERE r.canonico_de IS NULL AND p.p_literal >= 0.3""").fetchall()
    base = [(i, pl, m) for i, pl, m, b in linhas if i not in fora and not b]
    rng = np.random.default_rng(2809)
    lit = [x for x in base if x[1] >= 0.5]
    sorteio = [lit[i][0] for i in rng.permutation(len(lit))[:13500]]
    ja = set(sorteio)
    indecisos = [x[0] for x in sorted(base, key=lambda x: x[2] if x[2] is not None else 9) if x[0] not in ja][:1500]
    esc = [(i, 'sorteio') for i in sorteio] + [(i, 'indeciso') for i in indecisos]
    esc = [esc[i] for i in rng.permutation(len(esc))]
    tx = {}
    ids = [e[0] for e in esc]
    for k in range(0, len(ids), 900):
        pedaco = ids[k:k + 900]
        tx.update(con.execute(f"SELECT id, texto FROM relatos WHERE id IN ({','.join('?' * len(pedaco))})", pedaco))
    SAIDA.mkdir(parents=True, exist_ok=True)
    for j in range(0, len(esc), 200):
        with open(SAIDA / f'a_{j // 200 + 1}.jsonl', 'w') as f:
            for i, via in esc[j:j + 200]:
                f.write(json.dumps({'id': i, 'via': via, 'texto': tx[i]}, ensure_ascii=False) + '\n')
    print(f'{len(lit)} literais elegíveis · sorteio {len(sorteio)} · indecisos {len(indecisos)} · '
          f'{(len(esc) + 199) // 200} lotes')


if __name__ == '__main__':
    main()
