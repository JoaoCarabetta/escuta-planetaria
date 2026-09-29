#!/usr/bin/env python3
"""Taxas de acerto do palpite para a página (planeta-v3/gerar.py, TAXAS), das
cabeças de afeto: v3.6 × afeto_v2, na PROVA (300), nos literais do gabarito.

Mesma regra do gerar.py: taxa = precisão (quando o aluno diz X, quantas vezes X
está certo); faixa = Wilson 95%; 'sim' com >=20 palpites e limite inferior >60%;
'aviso' com >=10; 'nao' abaixo. A coluna v3.6 serve de conferência: tem de
reproduzir as linhas atuais do gerar.py.

  python3 taxas_afeto_v2.py [--aparelho=mps]
"""
import json
import math
import sys
from pathlib import Path

from transformers import AutoTokenizer

from avaliar_raros_v36 import prever_tudo
from avaliar_v35 import por_classe
from dados_afeto import LIT
from dados_v35 import CARGA, CONTEUDO, DESPERTAR, ORIGEM, conectar, prova_v35
from modelo_v35 import BASE, M

AQUI = Path(__file__).parent
L = 0.5


def wilson(k, n, z=1.96):
    if not n:
        return 0, 0
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0, c - m), min(1, c + m)


def linha(prec, marc):
    k = round(prec * marc)
    lo, hi = wilson(k, marc)
    st = 'sim' if marc >= 20 and lo > 0.6 else 'aviso' if marc >= 10 else 'nao'
    return (round(100 * prec), marc, f'{round(100 * lo)}–{round(100 * hi)}', st)


def taxas(P, linhas):
    out = {}
    for cab, nomes in (('carga', CARGA), ('despertar', DESPERTAR), ('origem', ORIGEM)):
        ii = [i for i, r in enumerate(linhas) if M not in r[cab]]
        al = [linhas[i][cab] for i in ii]
        pr = [[int(q > L) for q in P[cab][i]] for i in ii]
        for x in por_classe(al, pr, nomes):
            if x['marcados']:
                out[(cab, x['classe'])] = linha(x['prec'], x['marcados'])
    ii = [i for i, r in enumerate(linhas) if r['conteudo'] != M]
    al = [[int(linhas[i]['conteudo'] == c) for c in range(2)] for i in ii]
    pr = [[int(max(range(2), key=lambda c: P['conteudo'][i][c]) == c) for c in range(2)] for i in ii]
    for x in por_classe(al, pr, CONTEUDO):
        if x['marcados']:
            out[('conteudo', x['classe'])] = linha(x['prec'], x['marcados'])
    ii = [i for i, r in enumerate(linhas) if r['tem_atrib'] != M]
    al = [[linhas[i]['tem_atrib']] for i in ii]
    pr = [[int(P['tem_atrib'][i][0] > L)] for i in ii]
    for x in por_classe(al, pr, ['tem_atrib']):
        if x['marcados']:
            out[('tem_atrib', 'tem_atrib')] = linha(x['prec'], x['marcados'])
    return out


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    ap = arg.get('--aparelho', 'mps')
    tk = AutoTokenizer.from_pretrained(BASE)
    pv, _ = prova_v35(conectar())
    linhas = [r for r in pv if r['portao'][LIT] == 1]
    ta = taxas(prever_tudo('aluno_v36.pt', linhas, tk, ap), linhas)
    tb = taxas(prever_tudo('afeto_v2.pt', linhas, tk, ap), linhas)
    print(f'{len(linhas)} literais do gabarito na prova')
    for k in sorted(set(ta) | set(tb)):
        print(f'{k[0]:>10} {k[1]:<20} v3.6 {ta.get(k)}   v2 {tb.get(k)}')
    json.dump({f'{c}:{k}': v for (c, k), v in tb.items()},
              open(AQUI / 'taxas_afeto_v2.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
