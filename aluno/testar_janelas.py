#!/usr/bin/env python3
"""Embeddar em janelas e tirar a média — o teste que ficou pendente.

O viés de comprimento do bge-m3 é de VOLUME: texto longo carrega mais conteúdo
num vetor só, e "mais coisa" vira semelhança. Truncar resolve cortando sentido;
limpar palavras não resolve (corta proporcionalmente). A hipótese aqui: partir
o texto em janelas de mesmo tamanho, embeddar cada uma e tirar a média. Nada é
descartado, e a média de dez janelas não é "maior" que a de uma.

Risco conhecido: a média de muitas janelas pode puxar tudo para o centro.

Quatro provas:
  A. portão     1.816 textos com portão julgado (os mesmos da comparação de
                embedders) — mas NENHUM passa de 1.500 caracteres
  B. coletivo   40 "sonhei que o twitter voltou": fração dos 40 vizinhos de cada
                um que são do grupo (não cosseno cru — escalas mudam por método)
  C. metades    400 relatos longos (>1.500) partidos ao meio: a metade B acha a
                própria metade A entre as 400? Mede se o vetor carrega o
                conteúdo ESPECÍFICO do texto inteiro, não só a abertura
  D. espalhado  1.200 relatos estratificados por tamanho (300 por faixa):
                viés de comprimento onde ele existe de fato, e se os longos
                caem no centro (correlação tamanho × cosseno com a média)
"""
import json
import re
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

DB = Path(__file__).parent.parent / 'arquivo' / 'arquivo.db'
MODELO = 'bge-m3'
CACHE = {}


def _embed_lote(textos):
    req = urllib.request.Request(
        'http://localhost:11434/api/embed',
        data=json.dumps({'model': MODELO, 'input': textos,
                         'options': {'num_ctx': 8192}}).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)['embeddings']


def embed_strings(strs, lote=32):
    falta = list(dict.fromkeys(s for s in strs if s not in CACHE))
    for i in range(0, len(falta), lote):
        for s, v in zip(falta[i:i + lote], _embed_lote(falta[i:i + lote])):
            v = np.array(v, dtype='float64')
            CACHE[s] = v / max(np.linalg.norm(v), 1e-9)
    return [CACHE[s] for s in strs]


def janelas(texto, w):
    """Pedaços de ~w caracteres, cortados em espaço; o último, se curto demais,
    cola no anterior (uma janela de 15 caracteres pesaria igual a uma cheia)."""
    palavras, pedacos, atual = texto.split(), [], ''
    for p in palavras:
        if atual and len(atual) + 1 + len(p) > w:
            pedacos.append(atual)
            atual = p
        else:
            atual = f'{atual} {p}' if atual else p
    if atual:
        if pedacos and len(atual) < w / 3:
            pedacos[-1] += ' ' + atual
        else:
            pedacos.append(atual)
    return pedacos or [texto]


def metodo_cru(ts):
    return np.array(embed_strings(ts))


def metodo_trunc(n):
    return lambda ts: np.array(embed_strings([t[:n] for t in ts]))


def metodo_janela(w):
    def f(ts):
        partes = [janelas(t, w) for t in ts]
        vs = embed_strings([p for ps in partes for p in ps])
        X, k = [], 0
        for ps in partes:
            m = np.mean(vs[k:k + len(ps)], axis=0)
            X.append(m / max(np.linalg.norm(m), 1e-9))
            k += len(ps)
        return np.array(X)
    return f


MU = {}


def metodo_janela_centrada(w, amostra):
    """Tira de cada janela a direção comum a todas antes da média. Sem isso, a
    média de muitas janelas converge para essa direção comum — o centro."""
    def f(ts):
        if w not in MU:
            # média POR TEXTO, não por janela: por janela, os longos (com
            # dezenas de janelas) dominam a direção comum e os curtos viram o
            # desvio — o viés volta pela porta dos fundos.
            MU[w] = np.mean([np.mean(embed_strings(janelas(t, w)), axis=0)
                             for t in amostra], axis=0)
        partes = [janelas(t, w) for t in ts]
        vs = embed_strings([p for ps in partes for p in ps])
        X, k = [], 0
        for ps in partes:
            m = np.mean(vs[k:k + len(ps)], axis=0) - MU[w]
            X.append(m / max(np.linalg.norm(m), 1e-9))
            k += len(ps)
        return np.array(X)
    return f


def metodo_cru_centrado(amostra):
    def f(ts):
        if 'cru' not in MU:
            MU['cru'] = np.mean(embed_strings(amostra), axis=0)
        X = np.array(embed_strings(ts)) - MU['cru']
        return X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-9)
    return f


METODOS = [('texto cru', metodo_cru), ('truncado 120', metodo_trunc(120)),
           ('truncado 300', metodo_trunc(300)), ('janelas 200', metodo_janela(200)),
           ('janelas 400', metodo_janela(400)), ('janelas 800', metodo_janela(800))]


def vies_comprimento(X, tams, rng):
    S = X @ X.T
    np.fill_diagonal(S, -9)
    viz = S.argmax(1)
    lt = np.log(tams)  # log: 60→120 e 3000→6000 são a mesma distância
    dif = np.abs(lt - lt[viz]).mean()
    acaso = np.abs(lt - lt[rng.permutation(len(lt))]).mean()
    return 1 - dif / acaso, viz


def main():
    con = sqlite3.connect(DB, timeout=300)
    rng = np.random.default_rng(2015)

    # A
    la = con.execute("""SELECT r.texto, a.tem_literal, a.tem_figurado, r.fonte
        FROM anotacoes_v3 a JOIN relatos r ON r.id = a.relato_id
        WHERE a.anotador LIKE 'claude:v3%' AND r.canonico_de IS NULL
        GROUP BY a.relato_id ORDER BY a.relato_id""").fetchall()
    ta = [l[0] for l in la]
    port = [(bool(l[1]), bool(l[2])) for l in la]
    tama = np.array([len(t) for t in ta], dtype='float64')

    # B
    col = [r[0] for r in con.execute("""SELECT texto FROM relatos
        WHERE (texto LIKE '%sonhei que o twitter voltou%'
            OR texto LIKE '%sonhei que o twitter tinha voltado%')
          AND canonico_de IS NULL""")]
    col = list(dict.fromkeys(col))
    col = [col[i] for i in rng.choice(len(col), 40, replace=False)]

    # C
    lon = [r[0] for r in con.execute("""SELECT texto FROM relatos
        WHERE fonte='reddit' AND length(texto) > 1500 AND canonico_de IS NULL""")]
    lon = [lon[i] for i in rng.choice(len(lon), 400, replace=False)]
    metA, metB = [], []
    for t in lon:
        p = t.split()
        metA.append(' '.join(p[:len(p) // 2]))
        metB.append(' '.join(p[len(p) // 2:]))

    # D
    esp = []
    for lo, hi in [(0, 100), (100, 400), (400, 1500), (1500, 10**7)]:
        ids = [r[0] for r in con.execute(f"""SELECT texto FROM relatos
            WHERE length(texto) >= {lo} AND length(texto) < {hi}
              AND canonico_de IS NULL""")]
        esp += [ids[i] for i in rng.choice(len(ids), 300, replace=False)]
    tamd = np.array([len(t) for t in esp], dtype='float64')

    print(f'A {len(ta)} julgados · B {len(col)} coletivo · C {len(lon)} longos '
          f'(mediana {int(np.median([len(t) for t in lon]))} chars) · D {len(esp)}\n')
    print(f"{'método':14s} {'A concorda':>10s} {'A viés':>7s} {'B junto':>8s} "
          f"{'C acha':>7s} {'C rank':>7s} {'D viés':>7s} {'D centro':>9s} {'tempo':>6s}")
    metodos = METODOS
    if '--centradas' in sys.argv:
        metodos = [('jan200 c/texto', metodo_janela_centrada(200, esp)),
                   ('jan400 c/texto', metodo_janela_centrada(400, esp)),
                   ]
    for nome, f in metodos:
        t0 = time.time()
        XA = f(ta)
        vA, viz = vies_comprimento(XA, tama, rng)
        conc = np.mean([port[i] == port[viz[i]] for i in range(len(ta))])

        XB = f(col + ta)  # os 40 misturados aos 1.816
        S = XB[:40] @ XB.T
        for i in range(40):
            S[i, i] = -9
        junto = np.mean([(np.argsort(-S[i])[:39] < 40).mean() for i in range(40)])

        XCa, XCb = f(metA), f(metB)
        Sc = XCb @ XCa.T
        acha = np.mean(Sc.argmax(1) == np.arange(len(lon)))
        rank = np.median([(Sc[i] > Sc[i, i]).sum() + 1 for i in range(len(lon))])

        XD = f(esp)
        vD, _ = vies_comprimento(XD, tamd, rng)
        c = XD.mean(0)
        c /= np.linalg.norm(c)
        centro = np.corrcoef(np.log(tamd), XD @ c)[0, 1]

        print(f'{nome:14s} {100*conc:9.1f}% {100*vA:6.0f}% {100*junto:7.0f}% '
              f'{100*acha:6.1f}% {rank:7.0f} {100*vD:6.0f}% {centro:+9.2f} '
              f'{time.time()-t0:5.0f}s', flush=True)


if __name__ == '__main__':
    main()
