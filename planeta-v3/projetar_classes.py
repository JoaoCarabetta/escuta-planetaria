#!/usr/bin/env python3
"""[V3] Uma projeção por classe: literal, figurado, incerto (Fitipe, 28/09).

Cada classe é reprojetada SÓ com os próprios pontos, pelos mesmos embeddings e
o mesmo UMAP do planeta-v2/projetar.py (3D, cosseno, raio por posto). Para a
página poder animar de uma para outra, cada projeção:
  - começa das posições que os pontos têm hoje no planeta "todos" (init);
  - é girada no fim (Procrustes) para ficar o mais perto possível delas —
    sem isso a classe nasceria virada ao acaso e a transição seria um
    redemoinho sem significado.

A classe vem da própria página (pontos.bin, bits 0-2 de quem é relato), para
bater exatamente com "o sonho é". Os 680 literal+figurado entram nas duas
(decisão do Fitipe). Camadas (meta, idiomático, propaganda) ficam fora.

Página → embedding: o gerar.py não grava a ordem dos ids, mas a posição de
cada ponto em pontos.bin é cópia exata (float32) de uma linha de
dados/projecao.npy, cujos ids estão em projecao_ids.txt. Casamos por posição,
com assert de que todos casaram e sem repetição.

Saída: dados/classe_{literal,figurado,incerto}.bin — só os membros, na ordem
da página, x y z em int16 (±1 → ±32767). A página baixa cada um só quando o
botão é apertado.

Uso: python3 projetar_classes.py [literal figurado incerto]
"""
import sqlite3
import struct
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
DADOS = AQUI / 'dados'
DB = AQUI.parent / 'arquivo' / 'arquivo.db'


def ler_pontos():
    b = open(DADOS / 'pontos.bin', 'rb').read()
    n = struct.unpack_from('<I', b, 0)[0]
    reg = np.dtype([('pos', '<f4', 3), ('nat', 'u1'), ('fonte', 'u1'), ('com', 'u1'),
                    ('ano', '<u2'), ('mes', 'u1'), ('bits', '<u2'), ('pl', 'u1'), ('pf', 'u1'),
                    ('rot', '<u4')])
    assert reg.itemsize == 26
    r = np.frombuffer(b, dtype=reg, count=n, offset=4)
    return r['pos'].copy(), r['nat'].copy(), r['bits'].copy()


def membros(nat, bits, classe):
    rel = nat == 0
    inc = (bits & 4) != 0
    if classe == 'literal':
        return rel & ~inc & ((bits & 1) != 0)
    if classe == 'figurado':
        return rel & ~inc & ((bits & 2) != 0)
    return rel & inc


def regua(X, P, rng):
    """Mesma régua do projetar.py: quanto da semelhança sobreviveu."""
    idx = rng.choice(len(X), min(3000, len(X)), replace=False)
    Xa, Pa = X[idx].astype('float64'), P[idx].astype('float64')
    d = ((Pa[:, None, :] - Pa[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(d, 9e9)
    viz = d.argmin(1)
    sim = np.mean([Xa[i] @ Xa[viz[i]] for i in range(len(idx))])
    Dv = Xa @ Xa.T
    np.fill_diagonal(Dv, -9)
    teto = Dv.max(1).mean()
    acaso = np.mean(np.sum(Xa * Xa[rng.permutation(len(Xa))], axis=1))
    return (sim - acaso) / (teto - acaso)


def bola(P):
    """Direção do UMAP, raio por posto (densidade pareja) — como no projetar.py."""
    P = P - np.median(P, axis=0)
    r = np.linalg.norm(P, axis=1)
    direcao = P / np.maximum(r, 1e-9)[:, None]
    posto = np.argsort(np.argsort(r))
    raio = ((posto + 0.5) / len(r)) ** (1 / 3)
    return direcao * raio[:, None]


def alinhar(P, alvo):
    """Rotação (e reflexão, se ajudar) que leva P para perto de alvo."""
    U, _, Vt = np.linalg.svd(P.T @ alvo)
    R = U @ Vt
    return P @ R


def ids_da_pagina(pos):
    """Id de cada ponto da página, casado pela posição exata em projecao.npy."""
    N = len(pos)
    proj = np.load(DADOS / 'projecao.npy')
    pids = [i for i in open(DADOS / 'projecao_ids.txt').read().split('\n') if i]
    assert len(pids) == len(proj)
    linha = {proj[k].astype('<f4').tobytes(): k for k in range(len(proj))}
    assert len(linha) == len(proj), 'posições repetidas na projeção: casar por posição não vale'
    k_de = np.array([linha.get(pos[i].tobytes(), -1) for i in range(N)])
    assert (k_de >= 0).all(), f'{(k_de < 0).sum()} pontos da página sem linha na projeção'
    assert len(set(k_de.tolist())) == N
    print('página ↔ projeção: todos casaram', flush=True)
    return [pids[k] for k in k_de]


def main():
    classes = sys.argv[1:] or ['incerto', 'literal', 'figurado']
    pos, nat, bits = ler_pontos()
    N = len(pos)
    print(f'página: {N} pontos', flush=True)
    ids = ids_da_pagina(pos)

    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=600)
    con.execute('PRAGMA busy_timeout=600000')
    from umap import UMAP

    for classe in classes:
        m = membros(nat, bits, classe)
        idx = np.nonzero(m)[0]
        print(f'\n— {classe}: {len(idx)} pontos — lendo embeddings…', flush=True)
        X = np.empty((len(idx), 1024), dtype='float32')
        alvo_ids = [ids[i] for i in idx]
        for a in range(0, len(alvo_ids), 900):
            lote = alvo_ids[a:a + 900]
            got = dict(con.execute(f"SELECT id, embedding FROM relatos WHERE id IN ({','.join('?' * len(lote))})", lote))
            for j, rid in enumerate(lote):
                X[a + j] = np.frombuffer(got[rid], dtype='float32')
        X /= np.linalg.norm(X, axis=1, keepdims=True)
        assert np.isfinite(X).all()

        init = pos[idx].astype('float64')
        t0 = time.time()
        P = UMAP(n_neighbors=15, min_dist=0.0, metric='cosine', n_components=3,
                 n_epochs=200, init=init, random_state=2015, verbose=True).fit_transform(X)
        print(f'UMAP levou {(time.time() - t0) / 60:.1f} min', flush=True)
        B = alinhar(bola(P.astype('float64')), init)
        assert np.isfinite(B).all() and np.abs(B).max() <= 1.0001, 'projeção com NaN ou fora da bola'
        desloc = np.linalg.norm(B - init, axis=1)
        rng = np.random.default_rng(2015)
        print(f'régua (sinal preservado): na classe {regua(X, B, rng):.0%} · '
              f'posições de hoje, só a classe {regua(X, init, rng):.0%}')
        print(f'deslocamento até a posição nova: mediana {np.median(desloc):.2f} · '
              f'p90 {np.percentile(desloc, 90):.2f} (raio da bola = 1)')
        q = np.clip(np.round(B / max(1.0, np.abs(B).max()) * 32767), -32767, 32767).astype('<i2')
        q.tofile(DADOS / f'classe_{classe}.bin')
        print(f'dados/classe_{classe}.bin salvo ({q.nbytes / 1e6:.1f} MB)', flush=True)


if __name__ == '__main__':
    main()
