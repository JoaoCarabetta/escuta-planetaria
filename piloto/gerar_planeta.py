#!/usr/bin/env python3
"""Gera planeta.json: embeddings bge-m3 dos 491 do piloto -> esfera unitaria.

Geometria vem SO da semantica (proximidade = afinidade de conteudo).
Nada mais significa: sem relevo, sem alegoria.
"""
import json
import urllib.request
import numpy as np

OLLAMA = "http://localhost:11434/api/embed"
CATS = {1: 'onirico', 2: 'desejo', 3: 'pesadelo_angustia', 4: 'idiomatico',
        5: 'ruido_comercial', 6: 'indecidivel', 7: 'meta'}

STOP = set("""a o e de da do das dos em um uma que com para por nao não mais eu me minha meu
se ela ele isso essa esse las los sua seu vc você ja já como mas ou foi era ser ter tem
tinha muito muita quando sempre pra pro tambem também depois ate até anos ano dia hoje
the a an and of to in that i my was it is for with me on had this at as be are you we
he she they them his her so but not have has было my dreams dream sonho sonhos sonhei
sonhar what about just like really them then there when out up all one dont im ive
significa significado quê q eh tô to tá ta mesmo coisa coisas vida pessoa pessoas
gente tempo sei fazer faz vou ser estou meus minhas suas seus tenho tinha tive sinto
tudo nada aqui ali onde nunca antes agora ainda vez vezes outra outro dela dele
were where some from your very there their they what night last back look looked
feel felt got get going went woke wake sleep asleep dreamed dreamt dreaming know
would could should thing things time first while other people them being make made
started levar podem pode alguém algum alguma qualquer então estava estavam foram
queria quero quer sendo mim contra entre sobre desde toda todo todos todas""".split())


def embed_batch(texts):
    req = urllib.request.Request(
        OLLAMA,
        data=json.dumps({"model": "bge-m3", "input": texts}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["embeddings"]


def top_words(texts, k=3):
    from collections import Counter
    c = Counter()
    for t in texts:
        for w in t.lower().replace(',', ' ').replace('.', ' ').replace('?', ' ').split():
            w = w.strip('"\'!()[]:;|#*')
            if len(w) > 3 and w not in STOP and not w.isdigit():
                c[w] += 1
    return [w for w, _ in c.most_common(k)]


def tokens(t):
    for w in t.lower().replace(',', ' ').replace('.', ' ').replace('?', ' ').split():
        w = w.strip('"\'!()[]:;|#*—…')
        if len(w) > 3 and w not in STOP and not w.isdigit():
            yield w


def keywords_por_doc(texts, k=3):
    """TF-IDF simples: as k palavras mais distintivas de cada relato."""
    import math
    from collections import Counter
    df = Counter()
    docs = []
    for t in texts:
        c = Counter(tokens(t))
        docs.append(c)
        df.update(c.keys())
    N = len(texts)
    out = []
    for c in docs:
        scored = sorted(c.items(), key=lambda wv: -wv[1] * math.log(N / df[wv[0]]))
        out.append([w for w, _ in scored[:k]])
    return out


def nomear_cluster(amostras):
    """Ollama batiza o continente lendo uma amostra de relatos."""
    prompt = (
        "Você nomeia territórios de um mapa de sonhos coletivos. "
        "Leia os trechos abaixo (podem estar em português ou inglês) e responda "
        "APENAS um nome curto e evocativo de 1 a 3 palavras EM PORTUGUÊS, sem aspas, "
        "sem explicação, que capture o tema comum entre eles.\n\n"
        + "\n---\n".join(a[:220] for a in amostras))
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps({"model": "llama3.1:8b", "prompt": prompt, "stream": False,
                         "options": {"temperature": 0.3, "num_predict": 20}}).encode(),
        headers={"Content-Type": "application/json"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)["response"].strip()
            # limpa preâmbulos tipo "Aqui está o nome: X" ou listas
            for linha in resp.split('\n'):
                linha = linha.strip().strip('"\'.*-• ').split(':')[-1].strip().strip('"\'')
                if linha and len(linha) <= 36 and not linha.lower().startswith(('aqui', 'nome', 'o tema')):
                    return linha
        except Exception as e:
            print(f"  (ollama falhou: {e})")
            return None
    return None


def kmeans(X, k=14, iters=60, seed=2015):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), k, replace=False)].copy()
    for _ in range(iters):
        d = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        lab = d.argmin(1)
        for j in range(k):
            if (lab == j).any():
                C[j] = X[lab == j].mean(0)
    return lab, C


def main():
    items = [json.loads(l) for l in open('piloto_candidatos.jsonl')]
    verdicts = {}
    for tok in open('vereditos.txt').read().split():
        n, c = tok.split(':')
        verdicts[int(n)] = int(c)

    import os
    if os.path.exists('embeddings.npy'):
        X = np.load('embeddings.npy')
        print(f"embeddings carregados do cache ({X.shape})")
    else:
        print(f"embedding {len(items)} textos via bge-m3...")
        vecs = []
        B = 24
        for i in range(0, len(items), B):
            vecs += embed_batch([it['text'][:400] for it in items[i:i + B]])
            print(f"  {min(i + B, len(items))}/{len(items)}")
        X = np.array(vecs, dtype=np.float64)
        np.save('embeddings.npy', X)

    # PCA -> 3D -> esfera unitaria
    Xc = X - X.mean(0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    P3 = Xc @ Vt[:3].T
    sphere = P3 / np.linalg.norm(P3, axis=1, keepdims=True)

    # clusters no espaco original (nao na projecao) p/ rotulos honestos
    P20 = Xc @ Vt[:20].T
    lab, C = kmeans(P20 / np.linalg.norm(P20, axis=1, keepdims=True))

    kws = keywords_por_doc([it['text'] for it in items])

    import random as _r
    _r.seed(2015)
    clusters = []
    for j in sorted(set(lab)):
        idx = np.where(lab == j)[0]
        cen3 = sphere[idx].mean(0)
        cen3 /= np.linalg.norm(cen3)
        words = top_words([items[i]['text'] for i in idx])
        amostras = [items[i]['text'] for i in _r.sample(list(idx), min(8, len(idx)))]
        nome = nomear_cluster(amostras)
        clusters.append({"id": int(j), "n": len(idx),
                         "c": [round(float(v), 4) for v in cen3],
                         "words": words, "nome": nome})
        print(f"cluster {j}: {len(idx):3d} itens — {nome!r} ({' / '.join(words)})")

    out = []
    for i, it in enumerate(items):
        out.append({
            "n": it['n'],
            "p": [round(float(v), 4) for v in sphere[i]],
            "cat": verdicts[it['n']],
            "cl": int(lab[i]),
            "b": it['batch'],
            "d": it['date'],
            "t": it['text'][:240],
            "kw": kws[i],
        })

    json.dump({"pontos": out, "clusters": clusters, "cats": CATS},
              open('planeta.json', 'w'), ensure_ascii=False)
    print(f"planeta.json gerado: {len(out)} pontos, {len(clusters)} clusters")


if __name__ == '__main__':
    main()
