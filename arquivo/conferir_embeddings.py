#!/usr/bin/env python3
"""Conferência completa: reembedda TODOS os relatos e compara com o gravado.

Só lê — não escreve no banco. A validação de 24/09 foi por amostra (300/300
idênticos) e deixou passar 202 do piloto, feitos por outro script; esta é a
conferência sem amostra. Relatório em arquivo/conferencia_embeddings.txt.
"""
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import embedder  # noqa: E402

con = sqlite3.connect(f'file:{AQUI / "arquivo.db"}?mode=ro', uri=True, timeout=300)
ids = [r[0] for r in con.execute("SELECT id FROM relatos ORDER BY id")]
saida = open(AQUI / 'conferencia_embeddings.txt', 'w')
t0, diferentes, conferidos = time.time(), 0, 0
for i in range(0, len(ids), 256):
    lote = con.execute(f"""SELECT id, texto, embedding FROM relatos WHERE id IN
        ({','.join('?' * len(ids[i:i + 256]))})""", ids[i:i + 256]).fetchall()
    curtos = [l for l in lote if len(l[1] or '') <= 4000]
    longos = [l for l in lote if len(l[1] or '') > 4000]
    novos = {}
    for j in range(0, len(curtos), 32):
        parte = curtos[j:j + 32]
        for l, v in zip(parte, embedder.embeddar_lote([x[1] or ' ' for x in parte])):
            novos[l[0]] = v
    for l in longos:
        novos[l[0]] = embedder.embeddar(l[1])[0]
    for rid, texto, emb in lote:
        a = np.frombuffer(emb, dtype='float32').astype('float64')
        b = np.frombuffer(novos[rid], dtype='float32').astype('float64')
        c = float(a @ b / max(np.linalg.norm(a) * np.linalg.norm(b), 1e-12))
        conferidos += 1
        if c < 0.999:
            diferentes += 1
            saida.write(f'{rid}\t{c:.4f}\t{len(texto or "")}\n')
    saida.flush()
    if (i // 256) % 40 == 0:
        r = conferidos / (time.time() - t0)
        print(f'{conferidos}/{len(ids)} · diferentes {diferentes} · {r:.0f}/s · '
              f'~{(len(ids) - conferidos) / r / 60:.0f} min', flush=True)
saida.write(f'# FIM: {conferidos} conferidos, {diferentes} diferentes (cos < 0,999)\n')
print(f'★ {conferidos} conferidos, {diferentes} diferentes')
