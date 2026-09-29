#!/usr/bin/env python3
"""Compara aluno_v35.pt × aluno_v36.pt em DOIS conjuntos que não são a prova:

  RAROS   os 263 de validação extra do raros_enxuto (dados_v36.conjuntos_v36,
          split estratificado por lote, semente 2015) — mede o que a rodada
          v3.6 visava (alívio, mista, espírito_proprio etc.), que a prova (300,
          sorteio uniforme) quase não tem.
  FINAL   os 344 de validação do final_v35 (dados_v35.conjuntos, semente 2015)
          — o mesmo corte que decidiu a época do v3.5 e do v3.6.

Mesmo formato de `avaliar_v35.py`: por cabeça, cada classe traz n, precisão,
revocação, F1 e o F1 "sempre sim" (linha de base honesta); aqui os dois
modelos ficam lado a lado. Não treina nada, não toca em pesos.

  python3 avaliar_raros_v36.py [--aparelho=mps]
"""
import sys
from pathlib import Path

import torch
from transformers import AutoTokenizer

from avaliar_v35 import exato, pct, por_classe
from dados_v35 import (CARGA, CONTEUDO, DESPERTAR, FIGURA, ORIGEM, PORTAO,
                       conjuntos as conjuntos_v35)
from dados_v36 import conjuntos_v36
from modelo_v35 import BASE, K_INFER, M, AlunoV35
from treinar_v35 import Textos, prever

AQUI = Path(__file__).parent
L = 0.5
MODELOS = ['aluno_v35.pt', 'aluno_v36.pt']


def prever_tudo(nome, linhas, tk, ap):
    modelo = AlunoV35().to(ap)
    modelo.load_state_dict(torch.load(AQUI / nome, map_location=ap))
    return prever(modelo, Textos(linhas, tk, K_INFER), ap)


def tabela_dupla(titulo, linhas_saida, alvos, preds_a, preds_b, nomes, rot_a, rot_b):
    ac_a, base, comb = exato(alvos, preds_a)
    ac_b, _, _ = exato(alvos, preds_b)
    rot = '+'.join(n for n, x in zip(nomes, comb) if x) or '(nada)'
    linhas_saida.append(f'\n### {titulo}  (n={len(alvos)})\n')
    linhas_saida.append(f'acerto exato: **{rot_a} {pct(ac_a)}** · **{rot_b} {pct(ac_b)}** · '
                        f'chute constante {pct(base)} (`{rot}`)\n')
    linhas_saida.append(f'| classe | n | {rot_a} prec | {rot_a} rev | {rot_a} F1 | '
                        f'{rot_b} prec | {rot_b} rev | {rot_b} F1 | F1 "sempre sim" |')
    linhas_saida.append('|---|---|---|---|---|---|---|---|---|')
    ra = por_classe(alvos, preds_a, nomes)
    rb = por_classe(alvos, preds_b, nomes)
    for x, y in zip(ra, rb):
        linhas_saida.append(f"| {x['classe']} | {x['n']} | {pct(x['prec'])} | {pct(x['rev'])} | "
                            f"{pct(x['f1'])} | {pct(y['prec'])} | {pct(y['rev'])} | {pct(y['f1'])} | "
                            f"{pct(x['f1_sempre_sim'])} |")


def avaliar_conjunto(nome_set, linhas, tk, ap, saida):
    Pa = prever_tudo('aluno_v35.pt', linhas, tk, ap)
    Pb = prever_tudo('aluno_v36.pt', linhas, tk, ap)
    saida.append(f'\n## {nome_set} (n={len(linhas)})\n')

    idx = [i for i, r in enumerate(linhas) if M not in r['portao']]
    amb = len(linhas) - len(idx)
    a = [linhas[i]['portao'] for i in idx]
    pa = [[int(q > L) for q in Pa['portao'][i]] for i in idx]
    pb = [[int(q > L) for q in Pb['portao'][i]] for i in idx]
    tabela_dupla(f'PORTÃO (fora {amb} ambíguos)', saida, a, pa, pb, PORTAO, 'v3.5', 'v3.6')

    def cond(cab, nomes):
        ii = [i for i, r in enumerate(linhas) if M not in r[cab]]
        if not ii:
            saida.append(f'\n### {cab.upper()} — sem exemplos com a cabeça aberta\n')
            return
        a = [linhas[i][cab] for i in ii]
        pa = [[int(q > L) for q in Pa[cab][i]] for i in ii]
        pb = [[int(q > L) for q in Pb[cab][i]] for i in ii]
        tabela_dupla(cab.upper() + ' (onde o gabarito abre a cabeça)', saida, a, pa, pb, nomes,
                    'v3.5', 'v3.6')

    cond('carga', CARGA)
    cond('despertar', DESPERTAR)
    cond('figura', FIGURA)
    cond('origem', ORIGEM)

    ii = [i for i, r in enumerate(linhas) if r['conteudo'] != M]
    if ii:
        a = [[int(linhas[i]['conteudo'] == c) for c in range(2)] for i in ii]
        pa = [[int(max(range(2), key=lambda c: Pa['conteudo'][i][c]) == c) for c in range(2)] for i in ii]
        pb = [[int(max(range(2), key=lambda c: Pb['conteudo'][i][c]) == c) for c in range(2)] for i in ii]
        tabela_dupla('CONTEÚDO (onde o gabarito é literal com conteúdo)', saida, a, pa, pb,
                    CONTEUDO, 'v3.5', 'v3.6')

    for cab in ('tem_atrib', 'bandeira'):
        ii = [i for i, r in enumerate(linhas) if r[cab] != M]
        if not ii:
            continue
        a = [[linhas[i][cab]] for i in ii]
        pa = [[int(Pa[cab][i][0] > L)] for i in ii]
        pb = [[int(Pb[cab][i][0] > L)] for i in ii]
        tabela_dupla(cab.upper(), saida, a, pa, pb, [cab], 'v3.5', 'v3.6')


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    ap = arg.get('--aparelho', 'mps')
    tk = AutoTokenizer.from_pretrained(BASE)

    _, val35 = conjuntos_v35(False, verbose=False)
    _, _, val_raros, _ = conjuntos_v36(False, verbose=False)

    saida = ['# aluno_v35.pt × aluno_v36.pt — validação extra dos raros (263) e '
             'validação do final_v35 (344)',
             '\nNenhuma das duas é a amostra-prova (300): são os cortes que decidiram a '
             'época de cada treino (final_v35) e a medida das classes raras que a rodada '
             'v3.6 visava (raros_enxuto). `L=0.5` em tudo, igual `avaliar_v35.py`.']
    avaliar_conjunto('VALIDAÇÃO EXTRA — raros_enxuto (10% estratificado, semente 2015)',
                     val_raros, tk, ap, saida)
    avaliar_conjunto('VALIDAÇÃO — final_v35 (10%, semente 2015; decidiu a época dos dois)',
                     val35, tk, ap, saida)

    txt = '\n'.join(saida)
    print(txt)
    (AQUI / 'avaliacao_raros_v35_v36.md').write_text(txt)


if __name__ == '__main__':
    main()
