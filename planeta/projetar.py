#!/usr/bin/env python3
"""Projeção UMAP para dentro de uma bola — não mais para a casca de uma esfera.

Medimos três vezes a mesma coisa: quanto da semelhança semântica sobrevive
à projeção. A régua compara o vizinho mais próximo NA PROJEÇÃO com o vizinho
verdadeiro (no espaço de 1024 dimensões) e com dois relatos ao acaso.

    PCA  → superfície da esfera ....... 36%
    UMAP → superfície da esfera ....... 40%
    UMAP → 3 dimensões livres ......... 61%
    UMAP → 5 dimensões livres ......... 68%

O gargalo não era o método: a superfície de uma esfera tem DUAS dimensões,
e 1024 não cabem em duas de jeito nenhum. Abrindo para três — uma bola com
miolo, em vez de uma casca — a maior parte do sinal volta. O preço é visual:
o planeta deixa de ser oco. De fora continua um globo; de perto, atravessa-se.

Guarda o resultado em dados/projecao.npy para o gerar.py reaproveitar.
"""
import sqlite3
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
SAIDA = AQUI / 'dados'
SAIDA.mkdir(exist_ok=True)


def regua(X, P, rng, nome):
    """Quanto da semelhança semântica sobreviveu à projeção."""
    idx = rng.choice(len(X), min(3000, len(X)), replace=False)
    Xa, Pa = X[idx].astype('float64'), P[idx].astype('float64')
    d = ((Pa[:, None, :] - Pa[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(d, 9e9)
    viz = d.argmin(1)
    sim = np.mean([Xa[i] @ Xa[viz[i]] for i in range(len(idx))])
    Dv = Xa @ Xa.T
    np.fill_diagonal(Dv, -9)
    real = Dv.max(1).mean()
    aleat = np.mean([Xa[i] @ Xa[rng.integers(len(idx))] for i in range(len(idx))])
    print(f'\n{nome}: vizinhos {sim:.3f} · vizinho verdadeiro {real:.3f} · acaso {aleat:.3f}')
    print(f'sinal preservado: {100*(sim-aleat)/max(real-aleat, 1e-9):.0f}%')


def main():
    con = sqlite3.connect(DB, timeout=600)
    con.execute('PRAGMA busy_timeout=600000')
    print('lendo embeddings…', flush=True)
    linhas = con.execute("""SELECT r.id, r.embedding FROM relatos r
        JOIN anotacoes a ON a.id = (
            -- UMA anotação por relato. Sem isto, os 216 relatos que sobraram
            -- dos testes A/B entre modelos (gemma4, qwen 2b/4b/9b) viravam 2, 3
            -- ou 4 pontos na MESMA posição do planeta — e a régua chegava a
            -- comparar um relato com a própria cópia e marcá-lo como duplicata
            -- de si mesmo, fazendo-o sumir. Prefere o juiz de produção.
            SELECT a2.id FROM anotacoes a2
            WHERE a2.relato_id = r.id AND a2.versao = 'v2.1'
              AND a2.anotador LIKE 'ollama%'
            ORDER BY CASE WHEN a2.anotador = 'ollama:qwen3.5-9b' THEN 0 ELSE 1 END, a2.id
            LIMIT 1)
        WHERE r.embedding IS NOT NULL
          AND r.canonico_de IS NULL     -- repost da mesma pessoa não vira dois pontos
        ORDER BY r.data_relato""").fetchall()
    ids = [l[0] for l in linhas]
    X = np.stack([np.frombuffer(l[1], dtype='float32') for l in linhas])
    n = np.linalg.norm(X, axis=1, keepdims=True)
    bons = (n[:, 0] > 0) & np.isfinite(X).all(1)
    X, ids = (X[bons] / n[bons]).astype('float32'), [i for i, v in zip(ids, bons) if v]
    print(f'{len(X)} relatos · {X.shape[1]} dimensões', flush=True)

    from umap import UMAP
    t0 = time.time()
    print('UMAP (vizinhança → bola)… é o passo caro, preserva quem é vizinho de quem',
          flush=True)
    P = UMAP(
        n_neighbors=15,       # quantos vizinhos definem a vizinhança local
        min_dist=0.0,         # deixa os grupos se fecharem
        metric='cosine',      # a métrica em que os embeddings fazem sentido
        n_components=3,       # três eixos livres: a bola, não a casca
        n_epochs=200,
        random_state=2015,
        verbose=True,
    ).fit_transform(X).astype('float64')
    print(f'levou {(time.time()-t0)/60:.1f} min', flush=True)

    # O UMAP entrega um borrão de forma arbitrária: dois terços dos pontos num
    # caroço no meio e o resto num halo. A DIREÇÃO de cada ponto é o que carrega
    # a semântica; o raio, não. Então guardamos as direções e reescrevemos só os
    # raios por posto, para que a bola fique de densidade pareja (r ∝ posto^⅓).
    # Medido: custa 1 ponto de sinal (59% → 58%) e o planeta deixa de ser um
    # disco chapado.
    P -= np.median(P, axis=0)
    r = np.linalg.norm(P, axis=1)
    direcao = P / np.maximum(r, 1e-9)[:, None]
    posto = np.argsort(np.argsort(r))
    raio = ((posto + 0.5) / len(r)) ** (1 / 3)
    bola = (direcao * raio[:, None]).astype('float32')
    print(f'raios reescritos por posto · mediana {np.median(raio):.2f}')

    np.save(SAIDA / 'projecao.npy', bola)
    with open(SAIDA / 'projecao_ids.txt', 'w') as f:
        f.write('\n'.join(ids))
    print(f'projecao.npy salvo ({len(bola)} pontos)', flush=True)

    regua(X, bola, np.random.default_rng(2015), 'bola 3D')


if __name__ == '__main__':
    main()
