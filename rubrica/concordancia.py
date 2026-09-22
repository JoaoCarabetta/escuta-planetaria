#!/usr/bin/env python3
"""Concordância entre julgadores nos 491 do piloto (Ollama vs triagem manual Claude)."""
import sqlite3
from pathlib import Path
from collections import Counter, defaultdict

DB = Path(__file__).parent.parent / 'arquivo' / 'arquivo.db'
CATS = {1: 'onírico', 2: 'desejo', 3: 'pesad/ang', 4: 'idiom', 5: 'ruído', 6: 'indec', 7: 'meta'}
A = 'claude:fable-sessao-manual'
B = 'ollama:llama3.1-8b'

con = sqlite3.connect(DB)
pares = con.execute("""
    SELECT ja.relato_id, ja.categoria, jb.categoria, jb.confianca
    FROM julgamentos ja JOIN julgamentos jb ON ja.relato_id = jb.relato_id
    WHERE ja.julgador = ? AND jb.julgador = ?""", (A, B)).fetchall()

n = len(pares)
iguais = sum(1 for _, a, b, _ in pares if a == b)
print(f'pares comparados: {n}')
print(f'CONCORDÂNCIA GLOBAL: {iguais}/{n} = {100*iguais/n:.1f}%\n')

# por categoria (do julgador manual, referência)
por_cat = defaultdict(lambda: [0, 0])
for _, a, b, _ in pares:
    por_cat[a][1] += 1
    if a == b:
        por_cat[a][0] += 1
print('por categoria (referência = triagem manual):')
for c in sorted(por_cat):
    ac, tot = por_cat[c]
    print(f'  {c} {CATS[c]:10s} {ac:3d}/{tot:3d} = {100*ac/tot:.0f}%')

# faixa de confiança do Ollama
alta = [(a, b) for _, a, b, cf in pares if (cf or 0) >= 0.7]
baixa_n = n - len(alta)
if alta:
    ok_alta = sum(1 for a, b in alta if a == b)
    print(f'\nconfiança ≥0.7 (Ollama decide sozinho): {len(alta)} casos, '
          f'concordância {100*ok_alta/len(alta):.1f}%')
print(f'confiança <0.7 (subiria p/ camada 2): {baixa_n} casos ({100*baixa_n/n:.0f}%)')

# matriz de confusão (linhas = manual, colunas = ollama)
print('\nmatriz de confusão (linha=manual, coluna=ollama):')
print('        ' + ''.join(f'{c:>6d}' for c in sorted(CATS)))
matriz = Counter((a, b) for _, a, b, _ in pares)
for a in sorted(CATS):
    linha = ''.join(f'{matriz.get((a, b), 0):>6d}' for b in sorted(CATS))
    print(f'  {a} {CATS[a]:6s}{linha}')

# maiores confusões
print('\nmaiores divergências (manual→ollama):')
divs = [((a, b), k) for (a, b), k in matriz.items() if a != b]
for (a, b), k in sorted(divs, key=lambda x: -x[1])[:8]:
    print(f'  {CATS[a]} → {CATS[b]}: {k}')
