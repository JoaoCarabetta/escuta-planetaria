#!/usr/bin/env python3
"""Junta a anotação v3.5 final dos 3.473 textos (27/09, noite).

  - base: lotes/v34/final_v34.jsonl (v3.4 + v3.4.1);
  - por cima: os 1.537 corrigidos por 19 agentes (lotes/v35/corr_*_anotado);
  - o campo `bolsa` volta da base (alguns corretores o tiraram);
  - regra uniforme de postura, porque os corretores divergiram em
    "o que será que significa?": com palavra interrogativa de pedido de
    leitura ("o que", "oq", "qual", "quais", "por que") é `pergunta`;
    "será (que)", "acho que", "deve ser", "talvez" sem ela é `cogita`.

v3.5.1 (27/09, noite; decisões do Fitipe), por cima, campo a campo:
  lotes/v351/triste_*   "triste" depois de conteúdo desejado = decepção
  lotes/v351/choro_*    choro de emoção que a rodada v3.5 deixou passar
  lotes/v351/bandeira_* regra nova: ideação presente levanta; desejo
                        passivo não; menor sempre; ódio a pessoa só com
                        ameaça/desejo de dano; grupo levanta

  python3 aplicar_v35.py  →  rubrica/lotes/v35/final_v35.jsonl
"""
import glob
import json
import re
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).parent
BASE = AQUI / 'lotes' / 'v34' / 'final_v34.jsonl'
V35 = AQUI / 'lotes' / 'v35'
ATRIB = ('atribuicao_palavra', 'atribuicao_origem', 'atribuicao_postura', 'atribuicao_quem')
R_INTERROG = re.compile(r"\b(o\s*que|oq|oque|qq|qual|quais|por\s*que|pq|me ajud|interpret|"
                        r"gostaria de saber|quero saber|queria saber)", re.I)
R_HIPOTESE = re.compile(r"\b(ser[áa](\s+que)?|seria|acho|deve ser|talvez)\b", re.I)


def postura(a):
    n = 0
    post = list(a.get('atribuicao_postura') or [])
    for i, (pal, s) in enumerate(zip(a.get('atribuicao_palavra') or [], post)):
        if s not in ('pergunta', 'cogita'):
            continue
        novo = 'pergunta' if R_INTERROG.search(pal) else ('cogita' if R_HIPOTESE.search(pal) else s)
        if novo != s:
            post[i] = novo; n += 1
    a['atribuicao_postura'] = post
    return n


def main():
    base = {}
    for l in open(BASE):
        d = json.loads(l); base[d['id']] = d
    corr = {}
    for f in glob.glob(str(V35 / 'corr_*_anotado.jsonl')):
        for l in open(f):
            d = json.loads(l); corr[d['id']] = d
    esperados = {json.loads(l)['id'] for f in glob.glob(str(V35 / 'corr_*.jsonl'))
                 if not f.endswith('_anotado.jsonl') for l in open(f)}
    if esperados - set(corr):
        raise SystemExit(f'{len(esperados - set(corr))} corrigidos faltando')
    CAMPOS = {'triste': ('carga', 'despertar', 'confianca', 'nota'),
              'choro': ('carga', 'despertar', 'confianca', 'nota'),
              'bandeira': ('marcas', 'confianca', 'nota')}
    v351 = []
    for tipo in ('triste', 'choro', 'bandeira'):
        for f in sorted(glob.glob(str(V35.parent / 'v351' / f'{tipo}_*_anotado.jsonl'))):
            for l in open(f):
                d = json.loads(l)
                if d.get('mudou'):
                    v351.append((d['id'], {k: d[k] for k in CAMPOS[tipo] if k in d}))
    final, trocas = [], 0
    for i, b in base.items():
        if i in corr:
            x = dict(corr[i]); x['versao'] = 'v3.5 (agente)'
        else:
            x = dict(b); x['versao'] = 'v3.4→v3.5 (sem motivo de revisão)'; x.pop('mudou', None)
        x['bolsa'] = b['bolsa']
        for j, campos in v351:
            if j == i:
                x.update(campos); x['versao'] = x['versao'].split(' +')[0] + ' + v3.5.1'
        trocas += postura(x)
        if len({len(x.get(k) or []) for k in ATRIB}) > 1:
            print(f'  aviso: listas de atribuição desiguais em {i}')
        final.append(x)
    with open(V35 / 'final_v35.jsonl', 'w') as f:
        f.writelines(json.dumps(x, ensure_ascii=False) + '\n' for x in final)
    print(f'{len(final)} anotações → lotes/v35/final_v35.jsonl')
    print(Counter(x['versao'] for x in final))
    print(f'postura uniformizada: {trocas} trocas')


if __name__ == '__main__':
    main()
