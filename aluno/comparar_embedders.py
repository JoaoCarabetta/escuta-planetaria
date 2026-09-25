#!/usr/bin/env python3
"""Qual embedder serve melhor a este arquivo — medido, não escolhido.

O `bge-m3` foi adotado no começo do projeto e nunca comparado com nada. E ele
carrega um defeito medido: os vizinhos são ~47% mais parecidos em COMPRIMENTO
do que o acaso. Medimos e o efeito não é artefato de densidade — sobrevive à
normalização por vizinhança local —, o que sugere que é semântico: comprimento
correlaciona com gênero, e gênero é sentido. Mas isso é hipótese sobre ESTE
embedder, e só a comparação separa.

A régua é a única verdade externa que temos: **1.700 textos com o portão
julgado à mão**. Um embedder bom põe literal perto de literal.

  vizinho concorda  quanto o vizinho mais próximo compartilha o portão
  viés comprimento  quanto os vizinhos se parecem em tamanho (menos é melhor)
  viés fonte        quanto os vizinhos vêm da mesma fonte (menos é melhor)
"""
import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

DB = Path(__file__).parent.parent / 'arquivo' / 'arquivo.db'
MODELOS = ['bge-m3', 'snowflake-arctic-embed2', 'granite-embedding:278m',
           'qwen3-embedding:0.6b']


def embeddar(modelo, textos, lote=16):
    saida = []
    for i in range(0, len(textos), lote):
        req = urllib.request.Request(
            'http://localhost:11434/api/embed',
            data=json.dumps({'model': modelo,
                             'input': [t[:2000] for t in textos[i:i + lote]]}).encode(),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=300) as r:
            saida += json.load(r)['embeddings']
    X = np.array(saida, dtype='float64')
    return X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-9)


def medir(X, portoes, tams, fontes, rng):
    S = X @ X.T
    np.fill_diagonal(S, -9)
    viz = S.argmax(1)
    concorda = np.mean([portoes[i] == portoes[viz[i]] for i in range(len(X))])
    dif = np.abs(tams - tams[viz]).mean()
    acaso = np.abs(tams - tams[rng.permutation(len(tams))]).mean()
    mesma = np.mean([fontes[i] == fontes[viz[i]] for i in range(len(X))])
    acaso_f = np.mean([fontes[i] == fontes[j] for i, j in
                       zip(range(len(X)), rng.permutation(len(X)))])
    return concorda, 1 - dif / acaso, (mesma - acaso_f) / max(1 - acaso_f, 1e-9)


def main():
    con = sqlite3.connect(DB, timeout=300)
    linhas = con.execute("""SELECT r.texto, a.tem_literal, a.tem_figurado,
               length(r.texto), r.fonte
        FROM anotacoes_v3 a JOIN relatos r ON r.id = a.relato_id
        WHERE a.anotador LIKE 'claude:v3%' AND r.canonico_de IS NULL
        GROUP BY a.relato_id ORDER BY a.relato_id""").fetchall()
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 800
    linhas = linhas[:n]
    textos = [l[0] for l in linhas]
    portoes = [(bool(l[1]), bool(l[2])) for l in linhas]
    tams = np.array([l[3] for l in linhas], dtype='float64')
    fontes = [l[4] for l in linhas]
    rng = np.random.default_rng(2015)
    print(f'{len(textos)} textos com portão julgado à mão\n')
    print(f"{'modelo':26s} {'dims':>5s} {'vizinho concorda':>17s} "
          f"{'viés compr.':>12s} {'viés fonte':>11s} {'tempo':>7s}")
    for m in MODELOS:
        try:
            t0 = time.time()
            X = embeddar(m, textos)
            c, vc, vf = medir(X, portoes, tams, fontes, rng)
            print(f'{m:26s} {X.shape[1]:5d} {100*c:16.1f}% {100*vc:11.0f}% '
                  f'{100*vf:10.0f}% {time.time()-t0:6.0f}s')
        except Exception as e:
            print(f'{m:26s} falhou: {type(e).__name__}: {str(e)[:60]}')


if __name__ == '__main__':
    main()
