#!/usr/bin/env python3
"""Conjuntos do afeto v2 — as MESMAS fontes do v3.6 (dados_v36.conjuntos_v36:
final_v35 + afeto15k sem a_27 + 90% do raros_enxuto), mas SÓ os textos cujo
gabarito tem `literal` no portão (com ou sem fala_do_sonhar). Não altera
dados_v35/dados_v36.

  TREINO    literais do treino do v3.6.
  VALIDAÇÃO literais dos 344 do final_v35 (semente 2015) — decide a época.
  EXTRA     literais dos 263 do raros_enxuto — só medida.

`literal` no gabarito = portao[0] == 1 (ambíguo mascarado = -100 → fora).
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dados_v35 import CABECAS, PORTAO, contar
from dados_v36 import conjuntos_v36

LIT = PORTAO.index('literal')


def so_literal(linhas):
    return [r for r in linhas if r['portao'][LIT] == 1]


def conjuntos_afeto(usar_v3=False, verbose=True):
    """→ (treino, validacao, validacao_extra, relatorio), todos só-literal."""
    tr, val, val_raros, rel = conjuntos_v36(usar_v3, verbose=verbose)
    out = tuple(so_literal(x) for x in (tr, val, val_raros))
    rel = dict(rel)
    rel['afeto_v2'] = dict(
        treino=f'{len(out[0])} literais de {len(tr)}',
        validacao=f'{len(out[1])} literais de {len(val)}',
        validacao_extra=f'{len(out[2])} literais de {len(val_raros)}',
        treino_por_fonte=dict(Counter(r['origem_rot'] for r in out[0])),
        treino_com_fala_do_sonhar=sum(r['portao'][PORTAO.index('fala_do_sonhar')] == 1
                                      for r in out[0]))
    if verbose:
        print('afeto v2:', json.dumps(rel['afeto_v2'], ensure_ascii=False), flush=True)
    return out + (rel,)


def contagens(linhas, rotulo):
    print(f'-- {rotulo} (n={len(linhas)}) --')
    for cab, nomes in CABECAS.items():
        if cab == 'portao':
            continue
        print(' ', cab, dict(contar(linhas, cab, nomes)))
    print('  conteudo', dict(Counter(r['conteudo'] for r in linhas)))
    print('  tem_atrib', dict(Counter(r['tem_atrib'] for r in linhas)))


if __name__ == '__main__':
    tr, val, vr, rel = conjuntos_afeto('--v3' in sys.argv)
    contagens(tr, 'treino afeto v2')
    contagens(val, 'validação (decide época)')
    contagens(vr, 'validação extra raros')
