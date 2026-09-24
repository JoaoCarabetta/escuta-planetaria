#!/usr/bin/env python3
"""Mede o aluno, e nunca dá um número sozinho.

O `rubrica/desenho-do-treino.md` exige três números lado a lado para cada campo,
e a razão é que o primeiro não significa nada sem os outros dois:

  acerto do modelo · linha de base da classe majoritária · teto de concordância

Abaixo da linha de base, o modelo é pior que um chute constante. Acima do teto,
ele não está lendo melhor — está reproduzindo o ruído de quem o ensinou.

E classe rara não se mede por acurácia: `devaneio` tem 15 exemplos e deu ZERO em
300 sorteios. Um modelo que nunca marque devaneio exibe 99% de acerto no campo.
Por isso o relatório traz **revocação por classe** em tudo que é raro.

  python3 avaliar.py [--aparelho=cpu]
"""
import json
import sys
from collections import Counter
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

from dados import CARGA, PORTAO, SONHADOR, TOM, conjuntos
from modelo import BASE, Aluno
from treinar import Levas, mover

AQUI = Path(__file__).parent


def por_classe(verdade, predito, nomes):
    """Revocação e precisão de cada classe, uma a uma."""
    linhas = []
    for i, nome in enumerate(nomes):
        v = [r[i] for r in verdade]
        p = [r[i] for r in predito]
        vp = sum(1 for a, b in zip(v, p) if a and b)
        fn = sum(1 for a, b in zip(v, p) if a and not b)
        fp = sum(1 for a, b in zip(v, p) if not a and b)
        n = vp + fn
        linhas.append((nome, n, vp / n if n else None,
                       vp / (vp + fp) if (vp + fp) else None))
    return linhas


def rodar(modelo, linhas, tk, ap, lote=16):
    carr = DataLoader(Levas(linhas, tk), batch_size=lote)
    saidas = {k: [] for k in ('portao', 'carga', 'tom')}
    alvos = {k: [] for k in ('portao', 'carga', 'tom')}
    modelo.eval()
    with torch.no_grad():
        for b in carr:
            b = mover(b, ap)
            s = modelo(b['ids'], b['mascara'])
            saidas['portao'] += (torch.sigmoid(s['portao']) > 0.5).int().tolist()
            saidas['tom'] += (torch.sigmoid(s['tom']) > 0.5).int().tolist()
            saidas['carga'] += s['carga'].argmax(1).tolist()
            alvos['portao'] += b['portao'].tolist()
            alvos['tom'] += b['tom'].tolist()
            alvos['carga'] += b['carga'].tolist()
    return saidas, alvos


def relatar(nome, saidas, alvos, tetos):
    print(f'\n{"="*66}\n{nome}  ({len(alvos["portao"])} relatos)\n{"="*66}')

    exato = sum(1 for a, b in zip(alvos['portao'], saidas['portao']) if a == b)
    n = len(alvos['portao'])
    # linha de base: responder sempre a combinação mais frequente
    base = Counter(tuple(a) for a in alvos['portao']).most_common(1)[0][1]
    print(f'\nPORTÃO  exato {100*exato/n:.1f}%  ·  base {100*base/n:.1f}%  ·  '
          f'teto {tetos["portao"]}')
    print(f'  {"classe":16s} {"n":>4s} {"revoc.":>8s} {"precis.":>8s}')
    for cl, k, rev, pre in por_classe(alvos['portao'], saidas['portao'], PORTAO):
        r = f'{100*rev:.0f}%' if rev is not None else '—'
        p = f'{100*pre:.0f}%' if pre is not None else '—'
        print(f'  {cl:16s} {k:4d} {r:>8s} {p:>8s}')

    m = [i for i, a in enumerate(alvos['carga']) if a >= 0]
    if m:
        ac = sum(1 for i in m if alvos['carga'][i] == saidas['carga'][i])
        bc = Counter(alvos['carga'][i] for i in m).most_common(1)[0]
        print(f'\nCARGA   acerto {100*ac/len(m):.1f}%  ·  base {100*bc[1]/len(m):.1f}% '
              f'({CARGA[bc[0]]})  ·  teto {tetos["carga"]}  ·  n={len(m)}')
        for i, cl in enumerate(CARGA):
            k = sum(1 for j in m if alvos['carga'][j] == i)
            if not k:
                continue
            vp = sum(1 for j in m if alvos['carga'][j] == i == saidas['carga'][j])
            print(f'  {cl:16s} {k:4d} {100*vp/k:7.0f}%')

    et = sum(1 for a, b in zip(alvos['tom'], saidas['tom']) if a == b)
    bt = Counter(tuple(a) for a in alvos['tom']).most_common(1)[0][1]
    print(f'\nTOM     exato {100*et/n:.1f}%  ·  base {100*bt/n:.1f}%  ·  teto {tetos["tom"]}')
    for cl, k, rev, pre in por_classe(alvos['tom'], saidas['tom'], TOM):
        if k:
            r = f'{100*rev:.0f}%' if rev is not None else '—'
            p = f'{100*pre:.0f}%' if pre is not None else '—'
            print(f'  {cl:16s} {k:4d} {r:>8s} {p:>8s}')


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    ap = arg.get('--aparelho', 'cpu')
    torch.set_num_threads(int(arg.get('--linhas', 4)))
    tr, val, pv, hm = conjuntos()
    tk = AutoTokenizer.from_pretrained(BASE)
    modelo = Aluno().to(ap)
    modelo.load_state_dict(torch.load(AQUI / 'aluno.pt', map_location=ap))

    # os tetos vêm das auditorias cegas, medidos e não estimados
    tetos_prova = dict(portao='93%', carga='92%', tom='75%')
    tetos_treino = dict(portao='98%', carga='97%', tom='82%')
    for nome, linhas, tetos in (
            ('VALIDAÇÃO (mesma origem do treino)', val, tetos_treino),
            ('AMOSTRA-PROVA (300 sorteados — a medida honesta)', pv, tetos_prova),
            ('OS 70 DO FITIPE (o único humano no topo)', hm, tetos_prova)):
        s, a = rodar(modelo, linhas, tk, ap)
        relatar(nome, s, a, tetos)

    # o confundidor registrado: propaganda está colada a "link"
    print(f'\n{"="*66}\nO CONFUNDIDOR DA PROPAGANDA\n{"="*66}')
    com_link = [r for r in pv if ('http' in r['texto'].lower() or 'R$' in r['texto'])
                and not r['portao'][PORTAO.index('propaganda')]]
    if com_link:
        s, _ = rodar(modelo, com_link, tk, ap)
        erra = sum(r[PORTAO.index('propaganda')] for r in s['portao'])
        print(f'{len(com_link)} textos da amostra-prova têm link ou preço e NÃO são anúncio.')
        print(f'O modelo marcou propaganda em {erra} deles ({100*erra/len(com_link):.0f}%).')
    else:
        print('nenhum caso de teste na amostra-prova')


if __name__ == '__main__':
    main()
