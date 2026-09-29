#!/usr/bin/env python3
"""Confere os dados da V3 antes de alguém olhar a prévia.

Relê as fontes do cuidado DO ZERO (a conferência de risco pode ter terminado
um lote depois do gerar.py) e verifica, pelo texto publicado, que nenhum
relato com bandeira ficou em arquivo nenhum. Confere também o alinhamento dos
lidos (o índice na página aponta para o texto que Opus/Fitipe leram) e que
nenhum palpite carrega uma classe que a taxa medida não deixa mostrar.
Sai com erro se algo falhar — rode depois de todo gerar.py.
"""
import json
import sqlite3
import sys

import numpy as np

import gerar as G

D = G.SAIDA
falhas = []
con = sqlite3.connect(f'file:{G.DB}?mode=ro', uri=True)

meta = json.load(open(D / 'meta.json'))
textos = []
for b in range(meta['arquivos_texto']):
    textos += json.load(open(D / f'textos{b}.json'))['textos']
n_bin = int(np.frombuffer(open(D / 'pontos.bin', 'rb').read(4), '<u4')[0])
print(f"pontos.bin {n_bin} · textos {len(textos)} · meta {meta['n']}")
if not (n_bin == len(textos) == meta['n']):
    falhas.append('contagens desalinhadas')

# ——— cuidado, relido agora ———
cuidado, por_fonte, _ = G.ids_de_cuidado(con)
canon = con.execute('SELECT id, canonico_de FROM relatos WHERE canonico_de IS NOT NULL').fetchall()
for i, c in canon:
    if i in cuidado: cuidado.add(c)
tx = {t[:G.MAX_TEXTO] for (t,) in con.execute(
    f"SELECT texto FROM relatos WHERE id IN ({','.join('?' * len(cuidado))})", list(cuidado))}
publicados = set(textos)
vazou = tx & publicados
print(f'cuidado relido: {len(cuidado)} ids · {len(tx)} textos distintos · '
      f'publicados com bandeira: {len(vazou)}')
if vazou:
    falhas.append(f'{len(vazou)} textos com bandeira publicados')
if json.load(open(D / 'cuidado.json')):
    print('aviso: cuidado.json não está vazio (escondidos à mão na página)')

# ——— lidos: o índice aponta para um texto lido ———
lidos = json.load(open(D / 'lidos.json'))
ids_lidos = set()
for f in ['v35/final_v35.jsonl', 'v35/prova_1_anotado.jsonl', 'v35/prova_2_anotado.jsonl',
          'revisao_cega_respostas_fitipe.jsonl']:
    ids_lidos |= {x['id'] for x in G.jsonl(G.LOTES / f)}
ids_lidos |= {c for i, c in canon if i in ids_lidos}
tx_lidos = {t[:G.MAX_TEXTO] for (t,) in con.execute(
    f"SELECT texto FROM relatos WHERE id IN ({','.join('?' * len(ids_lidos))})", list(ids_lidos))}
desalinhados = [i for i, _ in lidos if textos[i] not in tx_lidos]
print(f'lidos na página: {len(lidos)} · índices que não apontam para texto lido: {len(desalinhados)}')
if desalinhados:
    falhas.append(f'{len(desalinhados)} lidos desalinhados')

# ——— bits: palpite não carrega classe que a taxa não deixa mostrar ———
reg = np.dtype([('pos', '<f4', 3), ('nat', 'u1'), ('fo', 'u1'), ('co', 'u1'), ('ano', '<u2'),
                ('mes', 'u1'), ('bits', '<u2'), ('pl', 'u1'), ('pf', 'u1'), ('rot', '<u4')])
P = np.frombuffer(open(D / 'pontos.bin', 'rb').read(), dtype=reg, count=n_bin, offset=4)
palpite = ((P['bits'] >> 12) & 3) == 0
print(f"lidos pelos bits: {int((~palpite).sum())} · palpites: {int(palpite.sum())}")
for j, (cab, cl) in enumerate(meta['rotulos']):
    t = meta['taxas'].get(f'{cab}:{cl}')
    n_pal = int(((P['rot'][palpite] >> j) & 1).sum())
    n_lid = int(((P['rot'][~palpite] >> j) & 1).sum())
    proibido = not t or t[3] == 'nao'
    if proibido and n_pal:
        falhas.append(f'palpite mostra {cab}:{cl} ({n_pal})')
    print(f'  {cab}:{cl:<20} palpite {n_pal:>7} · lido {n_lid:>5}' + ('  (só lidos)' if proibido else ''))
for k, f in enumerate(meta['formas']):
    print(f"  forma {f}: {int((((P['bits'] >> 10) & 3) == k).sum())}")

print('\n' + ('TUDO CERTO' if not falhas else 'FALHAS:\n  ' + '\n  '.join(falhas)))
sys.exit(1 if falhas else 0)
