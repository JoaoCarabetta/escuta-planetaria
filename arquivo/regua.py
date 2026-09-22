#!/usr/bin/env python3
"""A RÉGUA DE SIMILARIDADE — ecos e duplicatas, sem fundir sonhos parecidos.

Princípio (Fitipe, 2026-09-20): duas pessoas sonhando quase a mesma coisa é O ACHADO,
não ruído. Só é duplicata quando há evidência de ser a MESMA pessoa repetindo.

  ≥0,97 + mesmo autor + ≤90 dias → duplicata   (marca canonico_de)
  ≥0,97 + autores diferentes     → eco_forte   (liga, não funde)
  0,90–0,97                      → sonho_gemeo (liga — o material precioso)

Uso: python3 regua.py [--aplicar]   (sem --aplicar só relata)
"""
import sqlite3
import sys
import datetime
import numpy as np
from pathlib import Path

DB = Path(__file__).parent / 'arquivo.db'
APLICAR = '--aplicar' in sys.argv
LIM_GEMEO, LIM_FORTE, DIAS_DUP = 0.90, 0.97, 90


def main():
    con = sqlite3.connect(DB, timeout=180)
    con.execute('PRAGMA busy_timeout=180000')
    linhas = con.execute("""SELECT r.id, r.embedding, r.interno_autor_hash, r.data_relato
        FROM relatos r JOIN anotacoes a ON a.relato_id = r.id
        WHERE r.embedding IS NOT NULL AND a.natureza_texto = 'relato'""").fetchall()
    if not linhas:
        print('nenhum relato com embedding ainda'); return
    ids = [l[0] for l in linhas]
    autores = [l[2] for l in linhas]
    datas = [datetime.datetime.fromisoformat((l[3] or '').replace('Z', ''))
             if l[3] else None for l in linhas]
    X = np.stack([np.frombuffer(l[1], dtype='float32') for l in linhas]).astype('float32')
    norma = np.linalg.norm(X, axis=1, keepdims=True)
    validos = norma[:, 0] > 0          # descarta embeddings vazios
    X, norma = X[validos], norma[validos]
    ids = [i for i, v in zip(ids, validos) if v]
    autores = [a for a, v in zip(autores, validos) if v]
    datas = [d for d, v in zip(datas, validos) if v]
    X /= norma
    print(f'{len(ids)} relatos · comparando…')

    achados, B = [], 512
    for i0 in range(0, len(ids), B):
        S = X[i0:i0 + B] @ X.T
        for li, linha in enumerate(S):
            i = i0 + li
            linha[:i + 1] = -1                      # só metade superior
            for j in np.where(linha >= LIM_GEMEO)[0]:
                sim = float(linha[j])
                mesmo = int(bool(autores[i]) and autores[i] == autores[j])
                dias = (abs((datas[i] - datas[j]).days)
                        if datas[i] and datas[j] else None)
                if sim >= LIM_FORTE and mesmo and dias is not None and dias <= DIAS_DUP:
                    tipo = 'duplicata'
                elif sim >= LIM_FORTE:
                    tipo = 'eco_forte'
                else:
                    tipo = 'sonho_gemeo'
                achados.append((ids[i], ids[int(j)], sim, tipo, mesmo, dias))

    from collections import Counter
    c = Counter(a[3] for a in achados)
    print(f"duplicatas {c['duplicata']} · ecos fortes {c['eco_forte']} · sonhos gêmeos {c['sonho_gemeo']}")

    if not APLICAR:
        print('\n(sem --aplicar: nada gravado)  amostra de sonhos gêmeos:')
        for a in [x for x in achados if x[3] == 'sonho_gemeo'][:5]:
            t1 = con.execute('SELECT substr(replace(texto,char(10)," "),1,90) FROM relatos WHERE id=?', (a[0],)).fetchone()[0]
            t2 = con.execute('SELECT substr(replace(texto,char(10)," "),1,90) FROM relatos WHERE id=?', (a[1],)).fetchone()[0]
            print(f'\n  {a[2]:.3f} {"(mesmo autor)" if a[4] else ""}\n   A: {t1}\n   B: {t2}')
        return

    con.executemany("""INSERT OR REPLACE INTO ecos (a,b,similaridade,tipo,mesmo_autor,dias_entre)
                       VALUES (?,?,?,?,?,?)""", achados)
    for a, b, *_ , in [x for x in achados if x[3] == 'duplicata']:
        con.execute("UPDATE relatos SET canonico_de=? WHERE id=? AND canonico_de IS NULL", (a, b))
    con.commit()
    print(f'{len(achados)} ligações gravadas em `ecos`')


if __name__ == '__main__':
    main()
