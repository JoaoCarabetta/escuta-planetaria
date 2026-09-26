#!/usr/bin/env python3
"""Detector de obra v2 — duas probabilidades: obra de TERCEIROS e poema AUTORAL.

A v1 (detector_obra.py) aprendeu com 536 sementes e pegava o "registro
poético" inteiro, misturando letra alheia com poema da própria pessoa. A v2
aprende com as 1.160 obras conferidas por agentes com busca (rubrica/lotes/
obras_*_conferidas.jsonl) + as 170 circulações classificadas, separando:

  terceiros = letra · poema (autor conhecido) · citação
  autoral   = poema_autoral
  resto     = meme · outro · relato_com_letra + 5.000 sorteados não-obra

Rótulos de confiança BAIXA ficam fora do treino (a metade 1 do meio foi
classificada por estilo, sem busca). Sonda linear no bge-m3, zero fichas.
Só lê o banco. Saída: aluno/obra2_prob.npy (N×2: terceiros, autoral) + _ids.
"""
import json
import re
import sqlite3
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
DB = RAIZ / 'arquivo' / 'arquivo.db'
TERC, AUT = {'letra', 'poema', 'citacao'}, {'poema_autoral'}

rot = {}
for nome in ('obras_topo_conferidas', 'obras_meio_1_conferidas', 'obras_meio_2_conferidas'):
    for l in open(RAIZ / 'rubrica' / 'lotes' / f'{nome}.jsonl'):
        x = json.loads(l)
        if x.get('confianca') == 'baixa':
            continue
        rot[x['id']] = 1 if x['categoria'] in TERC else (2 if x['categoria'] in AUT else 0)
con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
circ = {x['grupo']: x for x in json.load(open(RAIZ / 'rubrica' / 'medidas' / 'circulacao_classificada.json'))}
for rid, g in con.execute("SELECT relato_id, grupo FROM grupos_copia WHERE tipo='circulacao'"):
    x = circ.get(g)
    if x and x['confianca'] != 'baixa':
        rot.setdefault(rid, 1 if x['categoria'] in TERC else 0)

rows = con.execute("""SELECT r.id, r.texto, r.embedding FROM relatos r
    JOIN predicoes_v32 p ON p.relato_id = r.id
    WHERE r.canonico_de IS NULL AND r.embedding IS NOT NULL""").fetchall()
ids = [r[0] for r in rows]; txt = [r[1] or '' for r in rows]
X = np.stack([np.frombuffer(r[2], 'float32') for r in rows]).astype('float32')
X /= np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-9)
onde = {r: i for i, r in enumerate(ids)}
em_copia = {r[0] for r in con.execute("SELECT relato_id FROM grupos_copia")}

rng = np.random.default_rng(2015)
neg = [i for i in rng.permutation(len(ids)) if ids[i] not in rot and ids[i] not in em_copia][:5000]
iy = [onde[r] for r in rot if r in onde] + neg
y = np.array([rot[ids[i]] for i in iy[:len(iy) - len(neg)]] + [0] * len(neg))
print(f'treino: terceiros {int((y==1).sum())} · autoral {int((y==2).sum())} · resto {int((y==0).sum())}')

clf = LogisticRegression(C=4.0, class_weight='balanced', max_iter=3000)
pc = cross_val_predict(clf, X[iy], y, cv=5, method='predict_proba')
for k, nome in ((1, 'terceiros'), (2, 'autoral')):
    for lim in (0.5, 0.8, 0.9):
        tp = ((pc[:, k] >= lim) & (y == k)).sum(); fp = ((pc[:, k] >= lim) & (y != k)).sum()
        print(f'  {nome:9s} corte {lim}: acha {tp}/{(y==k).sum()} · falso+ {fp} '
              f'(precisão {100*tp/max(tp+fp,1):.0f}%)')

clf.fit(X[iy], y)
P = clf.predict_proba(X)
fora = np.ones(len(ids), bool); fora[[onde[r] for r in rot if r in onde]] = False
corta = lambda i: re.sub(r'\s+', ' ', txt[i])[:100]
for k, nome in ((1, 'terceiros'), (2, 'autoral')):
    print(f'\n{nome} — arquivo, fora dos rotulados:')
    for lim in (0.95, 0.8, 0.5):
        print(f'   p≥{lim}: {int((fora & (P[:, k] >= lim)).sum())}')
    for i in rng.choice(np.where(fora & (P[:, k] >= 0.95))[0], 4, replace=False):
        print(f'   {P[i,k]:.2f} "{corta(i)}"')
np.save(AQUI / 'obra2_prob.npy', P[:, 1:].astype('float32'))
(AQUI / 'obra2_prob_ids.txt').write_text('\n'.join(ids))
print('\nsalvo aluno/obra2_prob.npy — nada gravado no banco')
