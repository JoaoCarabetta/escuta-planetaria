#!/usr/bin/env python3
"""Detector de OBRA — letra de música, poema, citação — sem listas externas.

Pedido do Fitipe (25/09): achou letras no planeta que não são duplicatas de
ninguém. Pista: elas ficam lado a lado — o embedding já separa o REGISTRO de
letra (versos, refrão, crédito, 🎶) do de relato.

Sementes positivas: as circulações que o agente Sonnet confirmou como letra,
poema ou citação (rubrica/medidas/circulacao_classificada.json) + os casos que
o Fitipe achou. Negativas: sorteio de relatos que NÃO circularam (contaminação
pequena: obra é rara). Sonda linear (regressão logística) sobre o embedding →
probabilidade de obra para todo o arquivo. Só lê o banco; nada é gravado.

Saída: contagem por faixa de probabilidade e amostras de cada faixa, para
escolher o corte com o Fitipe. Validação cruzada nas sementes.
"""
import json
import re
import sqlite3
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
CLASSIF = AQUI.parent / 'rubrica' / 'medidas' / 'circulacao_classificada.json'
DO_FITIPE = ['7065731eba3deaea', 'dad2d0f674301d9b', '0d0a18f95a4c5319', '489eaba4bcf2df80']
OBRA = {'letra', 'poema', 'citacao'}

con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
vec = lambda b: np.frombuffer(b, 'float32')

grupos_obra = {x['grupo'] for x in json.load(open(CLASSIF)) if x['categoria'] in OBRA}
pos = [rid for rid, g in con.execute("SELECT relato_id, grupo FROM grupos_copia WHERE tipo='circulacao'")
       if g in grupos_obra] + DO_FITIPE
pos = list(dict.fromkeys(pos))
em_copia = {r[0] for r in con.execute("SELECT relato_id FROM grupos_copia")}

rows = con.execute("""SELECT r.id, r.texto, r.embedding FROM relatos r
    JOIN predicoes_v32 p ON p.relato_id = r.id
    WHERE r.canonico_de IS NULL AND r.embedding IS NOT NULL""").fetchall()
ids = [r[0] for r in rows]; txt = [r[1] or '' for r in rows]
X = np.stack([vec(r[2]) for r in rows]).astype('float32')
X /= np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-9)
onde = {rid: i for i, rid in enumerate(ids)}

ip = [onde[r] for r in pos if r in onde]
rng = np.random.default_rng(2015)
cand_neg = [i for i in rng.permutation(len(ids)) if ids[i] not in em_copia][:5000]
iy = ip + cand_neg
y = np.array([1]*len(ip) + [0]*len(cand_neg))
print(f'sementes: {len(ip)} positivas (letra/poema/citação + {len(DO_FITIPE)} do Fitipe) · '
      f'{len(cand_neg)} negativas sorteadas')

clf = LogisticRegression(C=4.0, class_weight='balanced', max_iter=2000)
p_cv = cross_val_predict(clf, X[iy], y, cv=5, method='predict_proba')[:, 1]
for lim in (0.5, 0.8, 0.95):
    tp = ((p_cv >= lim) & (y == 1)).sum(); fp = ((p_cv >= lim) & (y == 0)).sum()
    print(f'  validação cruzada, corte {lim}: acha {tp}/{len(ip)} sementes · '
          f'{fp} das {len(cand_neg)} negativas passam ({100*fp/len(cand_neg):.2f}%)')

clf.fit(X[iy], y)
p = clf.predict_proba(X)[:, 1]
sem_sementes = np.ones(len(ids), bool); sem_sementes[ip] = False
print(f'\n{len(ids)} relatos pontuados (fora as sementes):')
faixas = [(0.99, 1.01), (0.95, 0.99), (0.8, 0.95), (0.5, 0.8)]
corta = lambda i: re.sub(r'\s+', ' ', txt[i])[:110]
for lo, hi in faixas:
    m = np.where(sem_sementes & (p >= lo) & (p < hi))[0]
    print(f'\n  p {lo:.2f}–{min(hi,1):.2f}: {len(m)} relatos')
    for i in rng.choice(m, min(6, len(m)), replace=False):
        print(f'    {p[i]:.3f} "{corta(i)}"')
np.save(AQUI / 'obra_prob.npy', p)
(AQUI / 'obra_prob_ids.txt').write_text('\n'.join(ids))
print('\nprobabilidades salvas em aluno/obra_prob.npy (+ _ids.txt) — nada gravado no banco')
