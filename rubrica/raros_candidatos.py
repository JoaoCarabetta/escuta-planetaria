#!/usr/bin/env python3
"""Congela os CANDIDATOS a valores raros (afeto/atribuição) em lotes para o Sonnet.

Lê o que `raros_sondas.py` deixou no scratch (p_cal por classe para cada
literal canônico não anotado, e os termos que bateram) e escolhe, POR
CLASSE, os textos de maior p_cal — a chance calibrada, nos sorteados de A,
de o anotador confirmar a classe. p_cal já junta as duas vias: sonda alta
E palavra (a interseção) sobe primeiro; palavra sozinha ou sonda sozinha
vêm depois, na medida em que cada uma acerta nos rótulos.

Cota por classe (META): até a cota, parando antes se o p_cal marginal cai
abaixo de P_MIN (menos candidatos quando a precisão despenca — anotar texto
com chance de 5% é o sorteio cego de volta); os primeiros META_MIN aceitam
até P_PISO. Classes sem sonda (poucos positivos) só levam quem bate
palavra, ordenados pela similaridade com os positivos.

Um texto pode servir a várias classes: é UM candidato, com todas as classes
em `classes_candidatas` e o p de cada uma em `p`. A ordem nos arquivos é
ALEATÓRIA (semente fixa): o anotador não pode ver o texto chegar em bloco
de "alívio" e passar a achar alívio em tudo.

  python3 raros_candidatos.py  →  rubrica/lotes/raros/r_<k>.jsonl (200 cada:
                                   id, texto, forma, classes_candidatas, via, p)
                                   <scratch>/raros/resumo_candidatos.json
Não altera o banco.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import risco_rotulos as R
from raros_sondas import NOMES, SCRATCH

SAIDA = Path(__file__).parent / 'lotes' / 'raros'
POR_ARQUIVO = 200
# Cota por classe. As que NÃO são raras de verdade (≥4% dos literais: decepção,
# estranha, tem_atribuicao) ficam com pouco — o sorteio já as confirma e elas
# ainda vêm de carona nos candidatos das outras. O resto divide o teto de
# ~5.000 textos.
META = {'alivio': 400, 'acordou_bem': 400, 'desorientado': 400, 'acordou_neutro': 300,
        'decepcao': 150, 'mista': 400, 'estranha': 150, 'tem_atribuicao': 150,
        'o_entidade_religiosa': 300, 'o_morto': 400, 'o_espirito_proprio': 400, 'o_outra': 300,
        'q_familia': 300, 'q_religioso': 300, 'q_doutrina_literatura': 400, 'q_oraculo': 400,
        'q_heranca': 300, 'q_terapia': 300, 'se_cumpriu': 400}
META_MIN = 150        # até aqui aceita p_cal ≥ P_PISO; depois exige P_MIN
P_MIN = 0.12          # p_cal marginal abaixo disso: para (anotar texto de 5% é o sorteio cego de volta)
P_PISO = 0.05
SEMENTE = 2809


def main():
    val = json.load(open(SCRATCH / 'validacao.json'))['por_classe']
    uni = open(SCRATCH / 'universo_ids.txt').read().split('\n')
    Pc = np.load(SCRATCH / 'p_cal.npy')
    Ps = np.load(SCRATCH / 'p_sonda.npy')
    oofA = np.load(SCRATCH / 'oof_A.npz')
    termos = {}
    for l in open(SCRATCH / 'palavras.jsonl'):
        x = json.loads(l); termos[x['id']] = x['termos']

    escolha = {}            # id → set de classes
    resumo = {}
    assert set(META) == set(NOMES)
    for j, c in enumerate(NOMES):
        sem_sonda = val[c]['via'] != 'sonda'
        if sem_sonda:
            bate = np.array([c in termos.get(i, {}) for i in uni])
            ordem = [k for k in np.argsort(-Ps[:, j]) if bate[k]][:META[c]]
        else:
            o = np.argsort(-Pc[:, j])
            ordem = []
            for k in o:
                n = len(ordem)
                if n >= META[c]:
                    break
                if Pc[k, j] < (P_PISO if n < META_MIN else P_MIN):
                    break
                ordem.append(k)
        for k in ordem:
            escolha.setdefault(uni[k], set()).add(c)
        pc = Pc[ordem, j]
        # conferência da calibração: no A sorteado (fora-da-dobra), o topo de MESMA
        # fração do universo (mín. 10 textos) — precisão observada × p_cal médio
        conf = {}
        if c in oofA.files and len(ordem):
            yA, sA = oofA[c][:, 0], oofA[c][:, 1]
            kA = max(10, int(round(len(ordem) * len(yA) / len(uni))))
            o = np.argsort(-sA)[:kA]
            conf = dict(k_A=kA, prec_obs_A=round(float(yA[o].mean()), 3), p_cal_medio_A=round(float(sA[o].mean()), 3))
        resumo[c] = dict(**conf,n=len(ordem), prec_esperada=round(float(pc.mean()), 3) if len(ordem) else None,
                         p_marginal=round(float(pc.min()), 3) if len(ordem) else None,
                         com_palavra=int(sum(c in termos.get(uni[k], {}) for k in ordem)))

    pos = {i: k for k, i in enumerate(uni)}
    ids = sorted(escolha)
    rng = np.random.default_rng(SEMENTE)
    ids = [ids[k] for k in rng.permutation(len(ids))]
    con = R.conectar()
    tx = {}
    for k in range(0, len(ids), 900):
        q = ids[k:k + 900]
        for rid, t, f in con.execute(f"SELECT id, texto, forma FROM relatos WHERE id IN ({','.join('?' * len(q))})", q):
            tx[rid] = (t, f)

    SAIDA.mkdir(parents=True, exist_ok=True)
    for f in SAIDA.glob('r_*.jsonl'):
        f.unlink()                                   # regerar do zero
    esperado = {c: 0.0 for c in NOMES}               # soma de p_cal de TODOS os candidatos
    for i in ids:
        k = pos[i]
        for j, c in enumerate(NOMES):
            esperado[c] += float(Pc[k, j])
    for a in range(0, len(ids), POR_ARQUIVO):
        with open(SAIDA / f'r_{a // POR_ARQUIVO + 1}.jsonl', 'w') as f:
            for i in ids[a:a + POR_ARQUIVO]:
                k, cls = pos[i], sorted(escolha[i], key=NOMES.index)
                via = {c: ('ambas' if c in termos.get(i, {}) and val[c]['via'] == 'sonda'
                           else 'palavras+vizinho' if val[c]['via'] != 'sonda'
                           else 'sonda') for c in cls}
                t, forma = tx[i]
                f.write(json.dumps(dict(id=i, texto=t, forma=forma, classes_candidatas=cls, via=via,
                                        p={c: round(float(Pc[k, NOMES.index(c)]), 3) for c in cls},
                                        termos={c: termos[i][c] for c in cls if c in termos.get(i, {})}),
                                   ensure_ascii=False) + '\n')
    n_arq = (len(ids) + POR_ARQUIVO - 1) // POR_ARQUIVO
    out = dict(total=len(ids), arquivos=n_arq, por_classe=resumo,
               esperado_confirmar={c: round(v, 1) for c, v in esperado.items()},
               classes_por_texto=dict(Counter(len(v) for v in escolha.values())),
               formas=dict(Counter(tx[i][1] for i in ids)),
               caracteres_medios=int(np.mean([len(tx[i][0]) for i in ids])))
    json.dump(out, open(SCRATCH / 'resumo_candidatos.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
