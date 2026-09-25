#!/usr/bin/env python3
"""Reprojeções de FATIAS do arquivo — material para a reorganização (V2.5→V3).

Cada fatia ganha o próprio UMAP: sozinhos, os literais (ou os figurados) se
espalham pelo que os distingue ENTRE SI, um mapa interno que no planeta
inteiro fica espremido numa região. Mesmos parâmetros da V2 (init PCA, bola
com raio por posto). Saída local em dados_fatias/ — não publicada.
"""
import json
import sqlite3
import time
from pathlib import Path

import numpy as np
from umap import UMAP

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
SAIDA = AQUI / 'dados_fatias'
SAIDA.mkdir(exist_ok=True)
FATIAS = {'literal': "p.portao LIKE '%\"literal\"%'",
          'figurado': "p.portao LIKE '%\"figurado\"%' AND p.portao NOT LIKE '%\"literal\"%'"}

con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=300)
for nome, cond in FATIAS.items():
    t0 = time.time()
    linhas = con.execute(f"""SELECT r.id, r.embedding FROM relatos r
        JOIN predicoes_v32 p ON p.relato_id = r.id
        WHERE r.embedding IS NOT NULL AND r.canonico_de IS NULL AND {cond}""").fetchall()
    ids = [l[0] for l in linhas]
    X = np.stack([np.frombuffer(l[1], dtype='float32') for l in linhas])
    X /= np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-9)
    P = UMAP(n_neighbors=15, min_dist=0.0, metric='cosine', n_components=3,
             n_epochs=200, random_state=2015, init='pca').fit_transform(X).astype('float64')
    P -= np.median(P, axis=0)
    r = np.linalg.norm(P, axis=1)
    posto = np.argsort(np.argsort(r))
    bola = (P / np.maximum(r, 1e-9)[:, None] * (((posto + 0.5) / len(r)) ** (1 / 3))[:, None])
    np.save(SAIDA / f'projecao_{nome}.npy', bola.astype('float32'))
    (SAIDA / f'projecao_{nome}_ids.txt').write_text('\n'.join(ids))
    print(f'{nome}: {len(ids)} pontos em {(time.time() - t0) / 60:.1f} min', flush=True)
print('★ fatias prontas')
