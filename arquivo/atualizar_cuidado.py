#!/usr/bin/env python3
"""Recalcula planeta-v2/dados/cuidado.json: TODO relato com bandeira — das
anotações (claude:sab*) e das conferências da sonda de risco
(rubrica/lotes/risco_conferidos*.jsonl) — fica fora da página pública até o
Fitipe ler e decidir. Só acrescenta (nunca tira um índice já escondido).
Mapeia id → posição na página pelo texto+data publicados."""
import glob, json, sqlite3
from collections import defaultdict
from pathlib import Path
RAIZ = Path(__file__).parent.parent
D = RAIZ / 'planeta-v2' / 'dados'
meta = json.load(open(D / 'meta.json'))
por_texto, quando = defaultdict(list), []
for b in range(meta['arquivos_texto']):
    bl = json.load(open(D / f'textos{b}.json'))
    for k, t in enumerate(bl['textos']):
        por_texto[t].append(bl['i0'] + k); quando.append(bl['quando'][k])
c = sqlite3.connect(f'file:{RAIZ}/arquivo/arquivo.db?mode=ro', uri=True)
ids = {r[0] for r in c.execute("""SELECT relato_id FROM anotacoes_v3 WHERE anotador LIKE 'claude:sab%'
                                   AND json_extract(extra,'$.bandeira')=1""")}
for f in glob.glob(str(RAIZ / 'rubrica' / 'lotes' / 'risco_conferidos*.jsonl')):
    for l in open(f):
        x = json.loads(l)
        if x.get('bandeira') is True: ids.add(x['id'])
tx = {r: (t, d) for r, t, d in c.execute(
    f"SELECT id, texto, data_relato FROM relatos WHERE id IN ({','.join('?'*len(ids))})", list(ids))}
idx = set(json.load(open(D / 'cuidado.json'))); antes = len(idx); fora = 0
for rid in ids:
    if rid not in tx: fora += 1; continue
    t, d = tx[rid]
    cands = [i for i in por_texto.get(t[:40000], []) if quando[i] in (d or '', '')] or por_texto.get(t[:40000], [])
    if cands: idx.update(cands)
    else: fora += 1          # ex.: comentário novo, ainda não está na página
json.dump(sorted(idx), open(D / 'cuidado.json', 'w'))
print(f'relatos com bandeira: {len(ids)} · escondidos {antes} → {len(idx)} · fora da página: {fora}')
