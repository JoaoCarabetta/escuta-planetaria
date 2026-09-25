#!/usr/bin/env python3
"""RÉGUA 2 — duplicatas e cópias, com a regra aprovada pelo Fitipe (25/09).

A régua 1 comparava tudo com tudo por embedding. Com 455 mil relatos, quase
todos tuítes curtos, explodiu: "que pesadelo" e "que pesadelo kkk" ficam
≥0,97 no embedding sem serem o mesmo post, e uma conta de sorteio com 343
posts iguais virava 58 mil pares. A regra nova:

  1. MESMA conta + texto normalizado IDÊNTICO (qualquer tamanho, qualquer
     data)                         → duplicata: fica um ponto (o mais antigo)
  2. MESMA conta + texto LONGO (≥200) + embedding ≥0,97
                                   → duplicata (variação de @, hashtag...)
  3. contas DIFERENTES + texto idêntico → NUNCA esconde: grupo de cópia
     (curto <60 → frase_comum · longo ≤45 dias → copy_paste · longo >45 dias
     → circulacao: circulou entre contas por meses — letra de música,
     meme, corrente, lista; semente do detector de obra)
  4. contas DIFERENTES + longo + ≥0,97 → eco_forte: só liga
  5. texto CURTO nunca é comparado por embedding — só pelo texto exato

Sem --aplicar: só conta e mostra amostras de cada regra (nada é gravado).
Com --aplicar: acrescenta canonico_de (não apaga as marcas antigas), refaz
grupos_copia e acrescenta os ecos fortes da regra 4.
"""
import collections
import datetime
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import numpy as np

DB = Path(__file__).parent / 'arquivo.db'
APLICAR = '--aplicar' in sys.argv
LONGO, CURTO_COPIA, LIM, DIAS_OBRA = 200, 60, 0.97, 45


def norm(t):
    t = unicodedata.normalize('NFD', (t or '').lower())
    t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn')
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', t)).strip()


def quando(d):
    return datetime.datetime.fromisoformat(d.replace('Z', '')) if d else None


class Uniao:
    def __init__(self): self.pai = {}
    def raiz(self, x):
        while self.pai.get(x, x) != x:
            self.pai[x] = self.pai.get(self.pai[x], self.pai[x]); x = self.pai[x]
        return x
    def juntar(self, a, b):
        ra, rb = self.raiz(a), self.raiz(b)
        if ra != rb: self.pai[ra] = rb


def main():
    modo = f'file:{DB}' + ('' if APLICAR else '?mode=ro')
    con = sqlite3.connect(modo, uri=True, timeout=300)
    rows = con.execute("""SELECT r.id, r.texto, r.interno_autor_hash, r.data_relato, r.embedding
        FROM relatos r WHERE r.canonico_de IS NULL AND r.embedding IS NOT NULL""").fetchall()
    ids = [r[0] for r in rows]; txt = [r[1] or '' for r in rows]
    aut = [r[2] for r in rows]; dat = [r[3] for r in rows]
    print(f'{len(rows)} relatos (sem os já marcados como duplicata)')

    dup = Uniao()                       # regras 1 e 2: mesma conta
    # --- regras 1 e 3: texto idêntico
    por_texto = collections.defaultdict(list)
    for i, t in enumerate(txt):
        por_texto[norm(t)].append(i)
    r1 = 0; copias = []
    for k, idx in por_texto.items():
        if len(idx) < 2: continue
        por_autor = collections.defaultdict(list)
        for i in idx: por_autor[aut[i]].append(i)
        for a, js in por_autor.items():
            if a and len(js) > 1:
                for j in js[1:]: dup.juntar(js[0], j)
                r1 += len(js) - 1
        autores = [a for a in por_autor if a]
        if len(autores) > 1:            # regra 3: cópia entre contas
            ds = [quando(dat[i]) for i in idx if dat[i]]
            vao = (max(ds) - min(ds)).days if len(ds) > 1 else 0
            tipo = 'frase_comum' if len(k) < CURTO_COPIA else ('circulacao' if vao > DIAS_OBRA else 'copy_paste')
            copias.append((tipo, idx, vao))
    # --- regras 2 e 4: longos por embedding
    L = [i for i in range(len(rows)) if len(txt[i]) >= LONGO]
    X = np.stack([np.frombuffer(rows[i][4], 'float32') for i in L]).astype('float32')
    X /= np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-9)
    ecos = []
    for a0 in range(0, len(L), 1024):
        S = X[a0:a0 + 1024] @ X.T
        for li, lin in enumerate(S):
            i = a0 + li; lin[:i + 1] = -1
            for j in np.where(lin >= LIM)[0]:
                a, b = L[i], L[int(j)]
                if aut[a] and aut[a] == aut[b]: dup.juntar(a, b)              # regra 2
                else: ecos.append((a, b, float(lin[j])))                      # regra 4
    # grupos de duplicata: fica o mais antigo
    grupos = collections.defaultdict(list)
    for x in list(dup.pai):
        grupos[dup.raiz(x)].append(x)
    for r in list(grupos):
        grupos[r] = sorted(set(grupos[r] + [r]), key=lambda i: dat[i] or '9999')
    esconder = {g[0]: g[1:] for g in grupos.values() if len(g) > 1}
    n_esc = sum(len(v) for v in esconder.values())

    print(f'\nregra 1 (mesma conta, texto idêntico): {r1} repetições')
    print(f'regras 1+2 (mesma conta): {len(esconder)} grupos → {n_esc} pontos escondidos '
          f'(maiores: {sorted((len(v)+1 for v in esconder.values()), reverse=True)[:6]})')
    tc = collections.Counter(t for t, _, _ in copias)
    rc = collections.Counter(); [rc.update({t: len(idx)}) for t, idx, _ in copias]
    print(f'regra 3 (contas diferentes, idêntico — nada escondido): {len(copias)} grupos · '
          + ' · '.join(f'{t} {tc[t]} grupos/{rc[t]} relatos' for t in ('frase_comum', 'copy_paste', 'circulacao')))
    print(f'regra 4 (contas diferentes, longo ≥{LIM}): {len(ecos)} ecos fortes · '
          f'{len({x for a, b, _ in ecos for x in (a, b)})} relatos ligados')

    corta = lambda i: re.sub(r'\s+', ' ', txt[i])[:85]
    print('\n— amostras (5 por regra) —')
    print('[1/2] duplicatas (mesma conta):')
    for c, v in sorted(esconder.items(), key=lambda kv: -len(kv[1]))[:3] + list(esconder.items())[::max(1, len(esconder)//2)][:2]:
        print(f'   {len(v)+1}× {dat[c][:10] if dat[c] else "?"}..{dat[v[-1]][:10] if dat[v[-1]] else "?"} "{corta(c)}"')
    for tipo in ('circulacao', 'copy_paste', 'frase_comum'):
        gs = sorted((g for g in copias if g[0] == tipo), key=lambda g: -len(g[1]))[:5]
        print(f'[3] {tipo}:')
        for _, idx, vao in gs:
            print(f'   {len(idx)} contas, {vao} dias: "{corta(idx[0])}"')
    print('[4] ecos fortes entre contas:')
    for a, b, s in ecos[:: max(1, len(ecos)//5)][:5]:
        print(f'   {s:.3f} "{corta(a)[:60]}" | "{corta(b)[:60]}"')

    if not APLICAR:
        print('\n(sem --aplicar: nada gravado)')
        return
    n = 0
    for c, v in esconder.items():
        for j in v:
            n += con.execute("UPDATE relatos SET canonico_de=? WHERE id=? AND canonico_de IS NULL",
                             (ids[c], ids[j])).rowcount
    con.execute("DELETE FROM grupos_copia")
    for g, (tipo, idx, vao) in enumerate(copias):
        for i in idx:
            con.execute("INSERT OR REPLACE INTO grupos_copia (relato_id, grupo, tipo, copias, dias) "
                        "VALUES (?,?,?,?,?)", (ids[i], g, tipo, len(idx), vao))
    for a, b, s in ecos:
        con.execute("INSERT OR IGNORE INTO ecos (a, b, similaridade, tipo, mesmo_autor, dias_entre) "
                    "VALUES (?,?,?,'eco_forte',0,NULL)", (ids[a], ids[b], s))
    con.commit()
    print(f'\n★ gravado: {n} canonico_de novos · {len(copias)} grupos de cópia · {len(ecos)} ecos fortes')


if __name__ == '__main__':
    main()
