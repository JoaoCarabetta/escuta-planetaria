#!/usr/bin/env python3
"""Liga cada comentário (e continuação) ao post de onde ele saiu, quando esse
post também está no arquivo.

Bluesky: pai e raiz vêm de bluesky_forma (preenchida por
coleta/forma_bluesky.py a partir do record.reply).
Reddit: o payload do comentário traz link_id (o post, 't3_…') e parent_id
(o post ou outro comentário, 't1_…').

Grava na tabela `vinculos` (uma linha por comentário/continuação):
  relato_id, fonte, pai_ref, raiz_ref, pai_relato_id, raiz_relato_id
*_ref é o identificador original (URI at:// ou t3_/t1_); *_relato_id só
existe quando aquele texto está no arquivo. Idempotente: pode rodar de novo
depois de cada coleta.

  python3 vincular_conversas.py
"""
import json
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / 'arquivo.db'


def main():
    con = sqlite3.connect(DB, timeout=300)
    con.execute('PRAGMA busy_timeout=300000')
    con.execute("""CREATE TABLE IF NOT EXISTS vinculos (
        relato_id TEXT PRIMARY KEY, fonte TEXT, pai_ref TEXT, raiz_ref TEXT,
        pai_relato_id TEXT, raiz_relato_id TEXT)""")

    # identificador original → relato. Reddit guarda post sem prefixo
    # ('xidrid') e comentário com ('t1_…'); normaliza os dois para t3_/t1_.
    ref = {}
    for rid, orig, fonte in con.execute(
            "SELECT id, interno_id_original, fonte FROM relatos WHERE interno_id_original IS NOT NULL"):
        if fonte == 'reddit' and not orig.startswith('t1_'):
            orig = 't3_' + orig
        ref.setdefault(orig, rid)

    linhas = []
    for rid, uri, pai, raiz in con.execute(
            "SELECT relato_id, uri, pai, raiz FROM bluesky_forma WHERE forma IN ('comentario','continuacao')"):
        linhas.append((rid, 'bluesky', pai, raiz, ref.get(pai), ref.get(raiz)))

    brutos = {}
    for payload, in con.execute("SELECT payload FROM fila_brutos WHERE lote LIKE 'reddit_c:%'"):
        p = json.loads(payload)
        brutos[p['id']] = (p.get('parent_id'), p.get('link_id'))
    for rid, orig in con.execute(
            "SELECT id, interno_id_original FROM relatos WHERE fonte='reddit' AND forma='comentario'"):
        pai, raiz = brutos.get(orig, (None, None))
        linhas.append((rid, 'reddit', pai, raiz, ref.get(pai), ref.get(raiz)))

    with con:
        con.executemany("INSERT OR REPLACE INTO vinculos VALUES (?,?,?,?,?,?)", linhas)
    for r in con.execute("""SELECT fonte, COUNT(*), SUM(raiz_relato_id IS NOT NULL),
            SUM(pai_relato_id IS NOT NULL) FROM vinculos GROUP BY fonte"""):
        print(f'{r[0]}: {r[1]} comentários · raiz no arquivo {r[2]} · pai no arquivo {r[3]}')


if __name__ == '__main__':
    main()
