#!/usr/bin/env python3
"""[V3] Cor por carga no arranjo literal (Fitipe, 28/09 noite).

Para cada ponto literal da página (mesma pertença de projetar_classes.py, na
ordem da página), as 5 probabilidades de carga do afeto v2
(predicoes_afeto_v2.p_carga; sem linha do v2, cai no v3.6 — predicoes_v36) em uint8 (0-255): prazerosa · aflitiva · estranha ·
mista · sem_afeto_dito. Nos LIDOS vale a leitura: 255 nas cargas lidas, 0 nas
outras. A página mistura as cores das cargas na proporção.

ATENÇÃO — são probabilidades brutas, inclusive de classes que a página não
marca como rótulo por taxa baixa (estranha 57%, mista 33% de precisão
medida; ver meta.json 'taxas'). A cor é tendência do aluno, não leitura.

Saída: dados/carga_literal.bin. Refazer sempre que gerar.py rodar.
"""
import json
import sqlite3

import numpy as np

from projetar_classes import DADOS, DB, ids_da_pagina, ler_pontos, membros

CARGAS = ['prazerosa', 'aflitiva', 'estranha', 'mista', 'sem_afeto_dito']


def main():
    pos, nat, bits = ler_pontos()
    ids = ids_da_pagina(pos)
    idx = np.nonzero(membros(nat, bits, 'literal'))[0]
    lidos = {i: l for i, l in json.load(open(DADOS / 'lidos.json'))}
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=600)
    con.execute('PRAGMA busy_timeout=600000')
    alvo = [ids[i] for i in idx]
    pc = {}
    for a in range(0, len(alvo), 900):
        lote = alvo[a:a + 900]
        pc.update(con.execute(f"SELECT b.relato_id, COALESCE(c.p_carga, b.p_carga) FROM predicoes_v36 b "
                            f"LEFT JOIN predicoes_afeto_v2 c ON c.relato_id = b.relato_id "
                            f"WHERE b.relato_id IN ({','.join('?' * len(lote))})", lote))
    out = np.zeros((len(idx), 5), dtype='u1')
    n_lido = n_sem = 0
    for k, i in enumerate(idx):
        L = lidos.get(int(i))
        if L and L.get('carga'):
            out[k] = [255 if c in L['carga'] else 0 for c in CARGAS]
            n_lido += 1
            continue
        p = pc.get(ids[i])
        if not p:
            n_sem += 1
            continue
        d = json.loads(p)
        out[k] = [round(255 * d.get(c, 0)) for c in CARGAS]
    assert n_sem == 0, f'{n_sem} literais sem p_carga'
    out.tofile(DADOS / 'carga_literal.bin')
    media = out[:, :].mean(0) / 255
    print(f'{len(idx)} literais · {n_lido} pela leitura · média ' +
          ' · '.join(f'{c} {m:.0%}' for c, m in zip(CARGAS, media)))


if __name__ == '__main__':
    main()
