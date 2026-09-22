#!/usr/bin/env python3
"""Preenche relatos.interno_autor_hash a partir do payload da fila (hash, nunca o nome).
Idempotente: pode rodar quantas vezes quiser, inclusive com o moinho rodando."""
import sqlite3, json, hashlib
from pathlib import Path
con = sqlite3.connect(Path(__file__).parent / 'arquivo.db', timeout=180)
con.execute('PRAGMA busy_timeout=180000')
n = 0
for rid, oid in con.execute("""SELECT id, interno_id_original FROM relatos
                               WHERE interno_autor_hash IS NULL AND interno_id_original IS NOT NULL"""):
    row = con.execute("SELECT payload FROM fila_brutos WHERE id_original=?", (oid,)).fetchone()
    if not row:
        continue
    autor = (json.loads(row[0]).get('author') or '').strip()
    if not autor or autor in ('[deleted]', 'AutoModerator'):
        continue
    con.execute("UPDATE relatos SET interno_autor_hash=? WHERE id=?",
                (hashlib.sha256(('reddit:' + autor).encode()).hexdigest()[:16], rid))
    n += 1
con.commit()
print(f'{n} hashes de autor gravados')
