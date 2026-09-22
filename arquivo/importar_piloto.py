#!/usr/bin/env python3
"""Cria a oficina (arquivo.db) e importa os 491 do piloto como primeiros registros."""
import json
import sqlite3
import numpy as np
from pathlib import Path

AQUI = Path(__file__).parent
PILOTO = AQUI.parent / 'piloto'

con = sqlite3.connect(AQUI / 'arquivo.db')
con.executescript(open(AQUI / 'schema.sql').read())

itens = {json.loads(l)['n']: json.loads(l) for l in open(PILOTO / 'piloto_candidatos.jsonl')}
planeta = json.load(open(PILOTO / 'planeta.json'))
pontos = {p['n']: p for p in planeta['pontos']}
X = np.load(PILOTO / 'embeddings.npy').astype(np.float32)

PT_BATCHES = ('r_sonhos', 'desabafos_sonhei', 'desabafos_meusonho')
DATA_COLETA = '2026-09-17'

# timestamp completo a partir dos brutos
import hashlib, re, glob, datetime
ts_lookup = {}
for f in glob.glob(str(PILOTO / 'raw' / 'as_*.json')):
    try:
        data = json.load(open(f))['data']
    except Exception:
        continue
    if not data:
        continue
    for p in data:
        text = ((p.get('title') or '') + '\n' + (p.get('selftext') or '')).strip()
        text = re.sub(r'\s+', ' ', text)
        if len(text) < 15 or p.get('selftext') in ('[removed]', '[deleted]'):
            continue
        h = hashlib.sha256((p.get('id') or text).encode()).hexdigest()[:10]
        ts = p.get('created_utc')
        if ts:
            ts_lookup[h] = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')

ins_r, ins_j = 0, 0
for n, it in itens.items():
    pt = pontos[n]
    eh_pt = it['batch'] in PT_BATCHES
    texto = pt.get('tf') or it['text']
    tem_midia = 1 if pt.get('midia') else 0
    con.execute(
        """INSERT OR REPLACE INTO relatos
           (id, natureza, fonte, comunidade, data_relato, precisao_data, data_coleta,
            idioma, texto, tem_midia, midia_extraida, categoria, julgador,
            keywords, embedding, geo_pais, geo_metodo, geo_confianca,
            interno_url, interno_id_original)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (it['pid'], 'escrito', 'reddit', it['sub'],
         ts_lookup.get(it['pid'], it['date']),
         'hora' if it['pid'] in ts_lookup else 'dia', DATA_COLETA,
         'pt' if eh_pt else 'en', texto, tem_midia, tem_midia,
         pt['cat'], 'humano-assistido:claude-fable-sessao',
         json.dumps(pt.get('kw', []), ensure_ascii=False),
         X[n - 1].tobytes(),
         'BR' if eh_pt else None, 'comunidade', 0.7 if eh_pt else 0.3,
         pt.get('u'), it['pid']))
    ins_r += 1
    con.execute(
        """INSERT INTO julgamentos (relato_id, julgador, versao, categoria, criado_em)
           VALUES (?,?,?,?,?)""",
        (it['pid'], 'claude:fable-sessao-manual', 'rubrica-v0-piloto', pt['cat'], DATA_COLETA))
    ins_j += 1

for c in planeta['clusters']:
    con.execute(
        """INSERT OR REPLACE INTO continentes (id, rodada, nome_ollama, centroid, n_membros)
           VALUES (?,?,?,?,?)""",
        (c['id'], 'piloto-2026-09-18', c.get('nome'),
         json.dumps(c['c']), c['n']))

con.commit()
print(f"relatos: {ins_r} | julgamentos: {ins_j} | continentes: {len(planeta['clusters'])}")
for row in con.execute(
        "SELECT categoria, COUNT(*) FROM relatos GROUP BY categoria ORDER BY categoria"):
    print(f"  cat {row[0]}: {row[1]}")
print("tamanho:", (AQUI / 'arquivo.db').stat().st_size // 1024, "KB")
