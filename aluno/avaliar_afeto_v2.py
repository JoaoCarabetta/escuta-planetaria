#!/usr/bin/env python3
"""aluno_v36.pt (afeto v1) × afeto_v2.pt, só nas cabeças de afeto, condicionadas
ao portão do GABARITO (só linhas com `literal`; a decisão de literal não é
medida aqui — é do portao_v1). Formato do avaliar_raros_v36.

Conjuntos: PROVA (300), RAROS (263, validação extra do raros_enxuto),
FINAL (344, validação do final_v35 — decidiu a época do afeto_v2, não é
independente). Só lê; não grava nada além do relatório.

  python3 avaliar_afeto_v2.py [--aparelho=mps]
"""
import json
import sys
from pathlib import Path

from transformers import AutoTokenizer

from avaliar_raros_v36 import prever_tudo, tabela_dupla
from avaliar_v35 import exato, por_classe
from dados_afeto import LIT
from dados_v35 import (CARGA, CONTEUDO, DESPERTAR, FIGURA, ORIGEM, PORTAO,
                       conectar, conjuntos as conjuntos_v35, prova_v35)
from dados_v36 import conjuntos_v36
from modelo_v35 import BASE, M

AQUI = Path(__file__).parent
L = 0.5
A, B = 'aluno_v36.pt', 'afeto_v2.pt'
RA, RB = 'v3.6', 'afeto_v2'


def avaliar_conjunto(nome, todas, tk, ap, saida, resumo):
    linhas = [r for r in todas if r['portao'][LIT] == 1]
    Pa, Pb = prever_tudo(A, linhas, tk, ap), prever_tudo(B, linhas, tk, ap)
    saida.append(f'\n## {nome}: {len(linhas)} literais (gabarito) de {len(todas)}\n')
    res = resumo[nome] = {}

    def cond(cab, nomes, titulo=None):
        ii = [i for i, r in enumerate(linhas) if M not in r[cab]]
        if not ii:
            saida.append(f'\n### {cab.upper()} — sem exemplos\n'); return
        al = [linhas[i][cab] for i in ii]
        pa = [[int(q > L) for q in Pa[cab][i]] for i in ii]
        pb = [[int(q > L) for q in Pb[cab][i]] for i in ii]
        tabela_dupla(titulo or cab.upper(), saida, al, pa, pb, nomes, RA, RB)
        ea, base, _ = exato(al, pa); eb, _, _ = exato(al, pb)
        res[cab] = dict(n=len(al), v36=ea, v2=eb, chute=base,
                        classes={x['classe']: dict(n=x['n'], f1_v36=x['f1'], f1_v2=y['f1'])
                                 for x, y in zip(por_classe(al, pa, nomes), por_classe(al, pb, nomes))})

    cond('carga', CARGA); cond('despertar', DESPERTAR); cond('origem', ORIGEM)
    cond('figura', FIGURA, 'FIGURA (literal E figurado no gabarito)')

    ii = [i for i, r in enumerate(linhas) if r['conteudo'] != M]
    al = [[int(linhas[i]['conteudo'] == c) for c in range(2)] for i in ii]
    pa = [[int(max(range(2), key=lambda c: Pa['conteudo'][i][c]) == c) for c in range(2)] for i in ii]
    pb = [[int(max(range(2), key=lambda c: Pb['conteudo'][i][c]) == c) for c in range(2)] for i in ii]
    tabela_dupla('CONTEÚDO', saida, al, pa, pb, CONTEUDO, RA, RB)
    ea, base, _ = exato(al, pa); eb, _, _ = exato(al, pb)
    res['conteudo'] = dict(n=len(al), v36=ea, v2=eb, chute=base)

    ii = [i for i, r in enumerate(linhas) if r['tem_atrib'] != M]
    al = [[linhas[i]['tem_atrib']] for i in ii]
    pa = [[int(Pa['tem_atrib'][i][0] > L)] for i in ii]
    pb = [[int(Pb['tem_atrib'][i][0] > L)] for i in ii]
    tabela_dupla('TEM_ATRIB', saida, al, pa, pb, ['tem_atrib'], RA, RB)
    ea, base, _ = exato(al, pa); eb, _, _ = exato(al, pb)
    res['tem_atrib'] = dict(n=len(al), v36=ea, v2=eb, chute=base)


def figura_figurado(nome, todas, tk, ap, saida):
    """Informativo: figura onde o gabarito é figurado (qualquer), que o afeto_v2
    quase não viu no treino (só literal E figurado)."""
    linhas = [r for r in todas if M not in r['figura']]
    if not linhas:
        return
    Pa, Pb = prever_tudo(A, linhas, tk, ap), prever_tudo(B, linhas, tk, ap)
    al = [r['figura'] for r in linhas]
    tabela_dupla(f'FIGURA em todo figurado do gabarito — {nome} (informativo, fora da regra)',
                 saida, al, [[int(q > L) for q in p] for p in Pa['figura']],
                 [[int(q > L) for q in p] for p in Pb['figura']], FIGURA, RA, RB)


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    ap = arg.get('--aparelho', 'mps')
    tk = AutoTokenizer.from_pretrained(BASE)
    pv, _ = prova_v35(conectar())
    _, val35 = conjuntos_v35(False, verbose=False)
    _, _, val_raros, _ = conjuntos_v36(False, verbose=False)
    saida = ['# aluno_v36.pt (afeto v1) × afeto_v2.pt — só as cabeças de afeto, nos literais do gabarito',
             '\n`L=0.5` em tudo. Condicionado ao portão do GABARITO (linhas com `literal`); '
             'a decisão literal × não-literal não entra. Chute constante = combinação mais '
             'comum do próprio conjunto; teto entre anotadores só existe para o portão (93%), '
             'não para estas cabeças.']
    resumo = {}
    avaliar_conjunto('PROVA (300, sorteio uniforme)', pv, tk, ap, saida, resumo)
    avaliar_conjunto('RAROS (263, validação extra raros_enxuto)', val_raros, tk, ap, saida, resumo)
    avaliar_conjunto('FINAL (344, validação do final_v35 — decidiu a época do afeto_v2)',
                     val35, tk, ap, saida, resumo)
    figura_figurado('prova', pv, tk, ap, saida)
    figura_figurado('raros', val_raros, tk, ap, saida)
    txt = '\n'.join(saida)
    (AQUI / 'avaliacao_afeto_v2.md').write_text(txt)
    (AQUI / 'avaliacao_afeto_v2.json').write_text(json.dumps(resumo, indent=1, ensure_ascii=False))
    print(txt)


if __name__ == '__main__':
    main()
