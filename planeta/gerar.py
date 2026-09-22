#!/usr/bin/env python3
"""Gera os dados do planeta v1 — campo de densidade, não coleção de pontos.

Princípios (acordados 2026-09-20/22):
  - posição vem SÓ da semântica (embedding), nada mais significa
  - sem continentes fixos: os nomes emergem da vizinhança onde se olha
  - campo-base = relatos com sonho ou desejo; resto são camadas acendíveis
  - três resoluções: densidade → pontos → texto

Saída: planeta/dados/pontos.bin (posições+marcadores) e textos.json
"""
import json
import re
import sqlite3
import struct
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
SAIDA = AQUI / 'dados'
SAIDA.mkdir(exist_ok=True)

QUALIDADES = ['recorrente', 'lucido', 'premonitorio', 'visita_de_morto', 'paralisia', 'erotico']
MAX_TEXTO = 40000        # sem corte: no GitHub Pages nao ha o teto de 64MB do Artifacts
STOP = set("""a o e de da do das dos em um uma que com para por nao não mais eu me minha meu se
ela ele isso essa esse sua seu você vc ja já como mas ou foi era ser ter tem tinha muito muita
quando sempre pra pro também depois até anos ano dia hoje ontem noite the a an and of to in that
i my was it is for with me on had this at as be are you we he she they them his her so but not
have has sonho sonhos sonhei sonhar sonhando dream dreams dreamt dreaming pesadelo nightmare
tudo nada aqui ali onde nunca antes agora ainda vez vezes outra outro dela dele meus minhas
seus suas tenho tinha tive sinto acho sei fazer faz vou estou está sou era são foi fui
dont im ive really just like then there when out up all one about what would could should
gente coisa coisas vida pessoa pessoas tempo casa pq porque então""".split())


def normalizar(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def palavras(texto):
    for w in re.findall(r"[a-zà-ú']{4,}", normalizar(texto)):
        if w not in STOP:
            yield w


def main():
    con = sqlite3.connect(DB, timeout=300)
    con.execute('PRAGMA busy_timeout=300000')
    print('lendo o arquivo…')
    linhas = con.execute("""
        SELECT r.id, r.embedding, r.texto, r.fonte, r.comunidade, r.data_relato,
               a.natureza_texto, a.tem_sonho_dormido, a.tem_desejo, a.tem_sofrimento,
               a.qualidades, r.interno_url IS NOT NULL
        FROM relatos r JOIN anotacoes a ON a.relato_id = r.id
        WHERE a.versao='v2.1' AND a.anotador LIKE 'ollama%' AND r.embedding IS NOT NULL
        ORDER BY r.data_relato""").fetchall()
    print(f'{len(linhas)} relatos com anotação e embedding')

    X = np.stack([np.frombuffer(l[1], dtype='float32') for l in linhas]).astype('float32')
    norma = np.linalg.norm(X, axis=1, keepdims=True)
    val = norma[:, 0] > 0
    X, linhas = X[val], [l for l, v in zip(linhas, val) if v]
    X /= norma[val]
    print(f'{len(linhas)} com embedding válido · projetando…')

    # PCA incremental (102k × 1024 cabe, mas centramos sem copiar tudo)
    media = X.mean(0)
    Xc = X - media
    # SVD randomizado: 3 componentes bastam para a esfera
    rng = np.random.default_rng(2015)
    Xc = np.nan_to_num(Xc, nan=0.0, posinf=0.0, neginf=0.0).astype('float64')
    Q = rng.standard_normal((Xc.shape[1], 12))
    for _ in range(4):                       # iterações de potência: estabiliza
        Q, _ = np.linalg.qr(Xc.T @ (Xc @ Q))
    B = Xc @ Q
    U, S, Vt = np.linalg.svd(B, full_matrices=False)
    P3 = B @ Vt[:3].T
    n3 = np.linalg.norm(P3, axis=1, keepdims=True)
    bom = (n3[:, 0] > 1e-9) & np.isfinite(P3).all(1)
    X, linhas, P3, n3 = X[bom], [l for l, v in zip(linhas, bom) if v], P3[bom], n3[bom]
    esfera = (P3 / n3).astype('float32')
    print(f'{len(linhas)} pontos válidos na esfera')
    print(f'variância nos 3 eixos: {100*(S[:3]**2).sum()/(S**2).sum():.1f}% dos 12 calculados')

    # ————— empacota posições e marcadores em binário —————
    NAT = {'relato': 0, 'meta': 1, 'idiomatico': 2, 'ruido': 3}
    FONTES, COMUNIDADES = {}, {}
    registros, textos, anos = [], [], []
    conta_palavra = Counter()
    docs_palavras = []

    for i, l in enumerate(linhas):
        (_id, _emb, texto, fonte, com, data, nat, sonho, desejo, sofr, quals, _u) = l
        qs = set(json.loads(quals or '[]'))
        f = FONTES.setdefault(fonte or '?', len(FONTES))
        c = COMUNIDADES.setdefault(com or '?', len(COMUNIDADES))
        # o Bluesky deixa forjar createdAt: datas fora da janela real são grampeadas
        ano = int((data or '2015')[:4]) if data else 2015
        mes = int((data or '2015-01')[5:7]) if data and len(data) > 6 else 1
        if ano < 2015: ano, mes = 2015, 1
        if ano > 2026: ano, mes = 2026, 12
        bits = ((sonho or 0) | ((desejo or 0) << 1) | ((sofr or 0) << 2))
        for j, q in enumerate(QUALIDADES):
            bits |= (1 << (3 + j)) if q in qs else 0
        registros.append((esfera[i], NAT.get(nat, 0), f, c, ano, mes, bits))
        textos.append(texto[:MAX_TEXTO])
        ps = set(palavras(texto[:600]))
        docs_palavras.append(ps)
        conta_palavra.update(ps)
        if i % 20000 == 0 and i:
            print(f'  {i}…')

    # ————— palavras distintivas por ponto (base dos nomes emergentes) —————
    # guarda, por ponto, os índices das 3 palavras mais raras que ele contém:
    # a raridade global é o que torna uma palavra distintiva de uma vizinhança.
    vocab = [w for w, n in conta_palavra.items() if 12 <= n <= len(linhas) // 25]
    idx_vocab = {w: i for i, w in enumerate(vocab)}
    print(f'vocabulário distintivo: {len(vocab)} palavras')
    palavras_por_ponto = []
    for ps in docs_palavras:
        cand = sorted((conta_palavra[w], idx_vocab[w]) for w in ps if w in idx_vocab)[:3]
        palavras_por_ponto.append([i for _, i in cand])

    with open(SAIDA / 'pontos.bin', 'wb') as f:
        f.write(struct.pack('<I', len(registros)))
        for (pos, nat, fo, co, ano, mes, bits) in registros:
            f.write(struct.pack('<3f', *[float(v) for v in pos]))
            f.write(struct.pack('<BBBHBH', nat, fo, co, ano, mes, bits))
        for pp in palavras_por_ponto:
            f.write(struct.pack('<B', len(pp)))
            for i in pp:
                f.write(struct.pack('<I', i))

    # blocos de tamanho fixo em número de itens: a página calcula qual buscar
    POR_ARQ = 8000
    n_arq = 0
    for i0 in range(0, len(textos), POR_ARQ):
        json.dump({'i0': i0, 'textos': textos[i0:i0 + POR_ARQ]},
                  open(SAIDA / f'textos{n_arq}.json', 'w'), ensure_ascii=False)
        n_arq += 1
    json.dump({
        'n': len(registros),
        'fontes': [k for k, _ in sorted(FONTES.items(), key=lambda x: x[1])],
        'comunidades': [k for k, _ in sorted(COMUNIDADES.items(), key=lambda x: x[1])],
        'qualidades': QUALIDADES,
        'vocab': vocab,
        'ano_min': min(r[4] for r in registros), 'ano_max': max(r[4] for r in registros),
        'arquivos_texto': n_arq, 'por_arquivo': POR_ARQ,
    }, open(SAIDA / 'meta.json', 'w'), ensure_ascii=False)

    mb = lambda p: (SAIDA / p).stat().st_size / 1e6
    maior = max(mb(f'textos{i}.json') for i in range(n_arq))
    print(f"\npontos.bin {mb('pontos.bin'):.1f}MB · {n_arq} blocos de texto "
          f"(maior: {maior:.1f}MB)")
    print(f"campo-base (relato c/ sonho ou desejo): "
          f"{sum(1 for r in registros if r[1]==0 and (r[6] & 3))}")


if __name__ == '__main__':
    main()
