#!/usr/bin/env python3
"""Via 2 dos candidatos de bandeira: SONDA DE RISCO retreinada na regra v3.5.1.

A sonda de 26/09 (aluno/risco_prob.npy; o script não foi guardado — rodou
inline) aprendeu com 220 bandeiras e depois ~400, na regra ANTIGA, e nunca
viu os ~52 mil textos que entraram depois (comentários do Reddit e do
Bluesky). Agora há ~9 mil conferidos, ~1.370 positivos na regra v3.5.1
(reconciliação em `risco_rotulos.py`): dá para medir de verdade.

Modelo: regressão logística sobre o embedding bge-m3 (1024-d, norma 1) —
linear de propósito: poucos positivos, e o embedding já separa o assunto;
o que a sonda aprende é a direção "sofrimento com risco" dentro dele.

Validação: 20% dos rótulos separados ANTES de tudo (estratificado, semente
2709); a força da regularização C é escolhida por validação cruzada nos
80%; a precisão/revocação relatada é a dos 20% nunca vistos. Depois o
modelo final treina em 100% e pontua o arquivo inteiro, em blocos (o
embedding é lido do banco em pedaços — não carrega 2 GB de uma vez).

LIMITE: os negativos conferidos vêm em boa parte da própria sonda antiga
(sofrimento sem risco) — são negativos DIFÍCEIS, o que é bom para aprender,
mas faz a precisão medida aqui ser a de um conjunto enriquecido (15% de
positivos). No arquivo aberto a taxa-base é muito menor; a precisão real
de cada faixa só se sabe conferindo.

  python3 risco_sonda_v351.py  →  <scratch>/sonda_p.npy + sonda_ids.txt
                                  <scratch>/sonda_validacao.json
Lê o banco só para leitura; não grava nada no banco nem na página.
"""
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

sys.path.insert(0, str(Path(__file__).parent))
import risco_rotulos as R

SCRATCH = Path('/private/tmp/claude-501/-Users-fitipe-Desktop-arte-c-joao-tta/'
               'e9da8b04-cc60-40d3-99e1-9659aa0a463e/scratchpad/risco')
SEMENTE = 2709
CS = (0.5, 1, 2, 4, 8, 16, 32)


def embeddings(con, ids):
    X = np.zeros((len(ids), 1024), np.float32)
    pos = {r: k for k, r in enumerate(ids)}
    for k in range(0, len(ids), 900):
        q = ids[k:k + 900]
        for rid, b in con.execute(f"SELECT id, embedding FROM relatos WHERE id IN ({','.join('?' * len(q))})", q):
            X[pos[rid]] = np.frombuffer(b, '<f4')
    return X


def faixas(y, p):
    out = {}
    for c in (0.3, 0.5, 0.7, 0.8, 0.9, 0.95):
        m = p >= c
        tp = int((y[m] == 1).sum())
        out[str(c)] = {'acima': int(m.sum()), 'precisao': round(tp / max(1, m.sum()), 3),
                       'revocacao': round(tp / max(1, (y == 1).sum()), 3)}
    return out


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    con = R.conectar()
    rotulo, conferidos, info = R.carregar(con)
    ids = sorted(rotulo)
    y = np.array([rotulo[i] for i in ids])
    X = embeddings(con, ids)
    ok = np.abs(X).sum(1) > 0
    ids, X, y = [i for i, v in zip(ids, ok) if v], X[ok], y[ok]
    print(f'{len(y)} rotulados com embedding · {y.sum()} positivos')

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEMENTE)
    cv = StratifiedKFold(5, shuffle=True, random_state=SEMENTE)
    ap_por_c = {}
    for C in CS:
        oof = np.zeros(len(ytr))
        for a, b in cv.split(Xtr, ytr):
            m = LogisticRegression(C=C, max_iter=3000).fit(Xtr[a], ytr[a])
            oof[b] = m.predict_proba(Xtr[b])[:, 1]
        ap_por_c[C] = average_precision_score(ytr, oof)
        print(f'  C={C:<5} AP (validação cruzada) {ap_por_c[C]:.3f}')
    C = max(ap_por_c, key=ap_por_c.get)
    m = LogisticRegression(C=C, max_iter=3000).fit(Xtr, ytr)
    pte = m.predict_proba(Xte)[:, 1]
    val = {'C': C, 'ap_cv': {str(k): round(v, 3) for k, v in ap_por_c.items()},
           'teste_n': int(len(yte)), 'teste_pos': int(yte.sum()),
           'teste_ap': round(average_precision_score(yte, pte), 3),
           'teste_auc': round(roc_auc_score(yte, pte), 3), 'teste_faixas': faixas(yte, pte),
           'rotulos': info}
    pr, rc, th = precision_recall_curve(yte, pte)
    for alvo in (0.5, 0.6, 0.7, 0.8):
        k = np.argmax(pr[:-1] >= alvo) if (pr[:-1] >= alvo).any() else None
        if k is not None:
            val[f'limiar_prec_{alvo}'] = {'limiar': round(float(th[k]), 3), 'revocacao': round(float(rc[k]), 3)}
    print(json.dumps({k: v for k, v in val.items() if k != 'rotulos'}, indent=1))

    # modelo final: todos os rótulos
    m = LogisticRegression(C=C, max_iter=3000).fit(X, y)
    w, b0 = m.coef_[0].astype(np.float32), np.float32(m.intercept_[0])
    todos, ps = [], []
    cur = con.execute('SELECT id, embedding FROM relatos WHERE embedding IS NOT NULL')
    while True:
        bloco = cur.fetchmany(20000)
        if not bloco:
            break
        E = np.frombuffer(b''.join(e for _, e in bloco), '<f4').reshape(len(bloco), 1024)
        ps.append(1 / (1 + np.exp(-(E @ w + b0))))
        todos.extend(r for r, _ in bloco)
    p = np.concatenate(ps).astype(np.float32)
    np.save(SCRATCH / 'sonda_p.npy', p)
    open(SCRATCH / 'sonda_ids.txt', 'w').write('\n'.join(todos))
    np.save(SCRATCH / 'sonda_w.npy', np.append(w, b0))
    naoconf = np.array([r not in conferidos for r in todos])
    val['arquivo'] = {str(c): {'todos': int((p >= c).sum()), 'nao_conferidos': int(((p >= c) & naoconf).sum())}
                      for c in (0.5, 0.7, 0.8, 0.9, 0.95)}
    json.dump(val, open(SCRATCH / 'sonda_validacao.json', 'w'), ensure_ascii=False, indent=1)
    print('arquivo:', json.dumps(val['arquivo']))


if __name__ == '__main__':
    main()
