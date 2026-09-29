#!/usr/bin/env python3
"""Congela os CANDIDATOS a bandeira (regra v3.5.1) em lotes para conferência.

Junta as duas vias — `risco_palavras.py` (termos de alta precisão) e
`risco_sonda_v351.py` (sonda logística no embedding) — num conjunto único
de relatos NÃO conferidos, em ordem de prioridade:

  1 ambas      sonda p ≥ P_AMBAS e ≥1 termo       (validação cruzada nos
               conferidos: precisão ~0,75, revocação ~0,75)
  2 sonda      sonda p ≥ P_SONDA, nenhum termo   (~0,4: a sonda sozinha erra
               mais — pega sofrimento sem risco)
  3 palavras   ≥ K_PALAVRAS termos distintos, sonda abaixo de P_AMBAS
               (sem a sonda a precisão cai muito: palavra sozinha pega a
               hipérbole, "vou me matar kkk")

Os ~50 mil comentários que ainda NÃO estão na página nunca passaram por
filtro nenhum (a página esconde só o que foi conferido); para eles o corte
é mais baixo (P_AMBAS_NOVO, P_SONDA_NOVO): errar para mais custa uma
leitura; errar para menos publica um texto de risco quando a V3 os levar.

Por que estes cortes: o pedido era ~1.500-4.000 candidatos. As medidas de
precisão são nos conferidos (enriquecidos pela sonda antiga, 15% de
positivos) — no arquivo aberto, onde o topo da sonda antiga já foi tirado,
a precisão será menor. A fila COMPLETA (abaixo dos cortes, até p ≥ 0,05
com termo, p ≥ 0,2 sem termo, ou 1 termo) vai ordenada em
`fila_completa.jsonl` para as rodadas seguintes.

Textos idênticos (mesmo texto normalizado, contas diferentes) viram UM
candidato; os outros ids vão em `iguais` — a decisão vale para todos.

  python3 risco_candidatos_v351.py  →  rubrica/lotes/risco_v351/cand_<k>.jsonl
                                       (id, texto, forma, na_pagina, via,
                                        prioridade, p_sonda, termos, iguais)
                                       rubrica/lotes/risco_v351/fila_completa.jsonl
Não altera o banco nem o cuidado.json.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import risco_rotulos as R
from risco_palavras import SCRATCH, normalizar

SAIDA = Path(__file__).parent / 'lotes' / 'risco_v351'
POR_ARQUIVO = 200
P_AMBAS, P_AMBAS_NOVO = 0.20, 0.10
P_SONDA, P_SONDA_NOVO = 0.50, 0.30
K_PALAVRAS = 3
# fila completa (além do corte)
P_AMBAS_FILA, P_SONDA_FILA, K_FILA = 0.05, 0.20, 1


def main():
    con = R.conectar()
    rotulo, conferidos, info = R.carregar(con)
    pag = R.ids_da_pagina()
    p = dict(zip(open(SCRATCH / 'sonda_ids.txt').read().split('\n'), np.load(SCRATCH / 'sonda_p.npy').tolist()))
    termos = {}
    for l in open(SCRATCH / 'palavras_batidas.jsonl'):
        x = json.loads(l); termos[x['id']] = x['termos']

    def classe(rid):
        """(no_corte, prioridade, via) ou None se nem na fila completa."""
        pr, k, novo = p.get(rid, 0.0), len(termos.get(rid, [])), rid not in pag
        if k >= 1 and pr >= (P_AMBAS_NOVO if novo else P_AMBAS):
            return True, 1, 'ambas'
        if k == 0 and pr >= (P_SONDA_NOVO if novo else P_SONDA):
            return True, 2, 'sonda'
        if k >= K_PALAVRAS and pr < P_AMBAS:
            return True, 3, 'palavras'
        if k >= 1 and pr >= P_AMBAS_FILA:
            return False, 4, 'ambas'
        if k == 0 and pr >= P_SONDA_FILA:
            return False, 5, 'sonda'
        if k >= K_FILA:
            return False, 6, 'palavras'
        return None

    fila = []
    for rid, texto, forma in con.execute('SELECT id, texto, forma FROM relatos WHERE canonico_de IS NULL'):
        if rid in conferidos:
            continue
        c = classe(rid)
        if c:
            fila.append(dict(id=rid, texto=texto, forma=forma, na_pagina=rid in pag, via=c[2],
                             prioridade=c[1], no_corte=c[0], p_sonda=round(p.get(rid, 0.0), 4),
                             termos=termos.get(rid, [])))
    # dentro da prioridade: sonda mais alta primeiro; empate → mais termos
    fila.sort(key=lambda d: (d['prioridade'], -d['p_sonda'], -len(d['termos']), d['id']))

    # idênticos viram um só (o primeiro da fila fica; os outros vão em `iguais`)
    vistos, unica = {}, []
    for d in fila:
        chave = ' '.join(normalizar(d['texto']).split())
        if chave in vistos:
            vistos[chave]['iguais'].append(d['id']); continue
        d['iguais'] = []; vistos[chave] = d; unica.append(d)

    SAIDA.mkdir(parents=True, exist_ok=True)
    for f in SAIDA.glob('cand_*.jsonl'):
        f.unlink()                       # regerar do zero (congelamento é esta saída)
    corte = [d for d in unica if d['no_corte']]
    campos = ('id', 'texto', 'forma', 'na_pagina', 'via', 'prioridade', 'p_sonda', 'termos', 'iguais')
    for k in range(0, len(corte), POR_ARQUIVO):
        with open(SAIDA / f'cand_{k // POR_ARQUIVO + 1}.jsonl', 'w') as f:
            for d in corte[k:k + POR_ARQUIVO]:
                f.write(json.dumps({c: d[c] for c in campos}, ensure_ascii=False) + '\n')
    with open(SAIDA / 'fila_completa.jsonl', 'w') as f:
        for d in unica:
            f.write(json.dumps({c: d[c] for c in campos if c != 'texto'} | {'no_corte': d['no_corte']},
                               ensure_ascii=False) + '\n')

    n_arq = (len(corte) + POR_ARQUIVO - 1) // POR_ARQUIVO
    print(f'rótulos: {info["positivos"]} positivos · {info["negativos"]} negativos · {info["conferidos"]} conferidos')
    print(f'fila completa {len(unica)} (idênticos juntados: {len(fila) - len(unica)}) · '
          f'no corte {len(corte)} → {n_arq} arquivos cand_*.jsonl')
    for pr in range(1, 7):
        s = [d for d in unica if d['prioridade'] == pr]
        print(f'  prioridade {pr} ({s[0]["via"] if s else "-"}): {len(s)} · fora da página {sum(not d["na_pagina"] for d in s)}')
    print('  formas no corte:', dict(Counter(d['forma'] for d in corte)))


if __name__ == '__main__':
    main()
