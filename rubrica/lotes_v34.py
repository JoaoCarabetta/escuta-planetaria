#!/usr/bin/env python3
"""Monta os lotes de CORREÇÃO para a rubrica v3.4 (27/09).

Não re-anota os 3.473 da v3.3 do zero: separa os textos em que alguma
decisão do Fitipe de 27/09 pode mudar a anotação e manda só esses de volta,
com a anotação v3.3 junto como referência. Motivos:

  habitual    fala_do_sonhar, ou literal com repetição (literal e fala não
              são mais excludentes)
  despertar   literal com despertar ou com "acord"/"chor" no texto
  atribuicao  atribuição anotada, ou literal com pista de quem atribui
              (mãe, avó, terreiro, Google, TikTok, "dizem", significado…)
  bandeira    bandeira levantada (agora só o que é PRESENTE)
  figura      figurado sem figura, ou "bons sonhos"/padaria (figura `votos`,
              homônimo do doce)

O resto (sem motivo) passa para a v3.4 por script em aplicar_v34.py.
Lotes cortados por tamanho de texto, não por contagem, para os longos não
estourarem um agente só.

  python3 lotes_v34.py  →  rubrica/lotes/v34/corr_<k>.jsonl
"""
import glob
import json
import re
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).parent
V33 = AQUI / 'lotes' / 'v33'
SAIDA = AQUI / 'lotes' / 'v34'
LIMITE = 140_000          # caracteres de texto por agente
MAX_ITENS = 200           # e no máximo isto de relatos

R_ATRIB = re.compile(r'm[ãa]e|av[óo]|\bv[óo]\b|tia\b|pai de santo|m[ãa]e de santo|google|tiktok|dizem|'
                     r'pastor|terreiro|chatgpt|\bia\b|signific|cartomante|benzedeira|igreja|centro esp', re.I)
R_FIG = re.compile(r'bons sonhos|doces sonhos|lindos sonhos|sonhe com os anjos|padaria|confeitaria', re.I)


def motivos(a, t):
    p, m = a['portao'], []
    if 'fala_do_sonhar' in p or ('literal' in p and a.get('repeticao')):
        m.append('habitual')
    if 'literal' in p and (a.get('despertar') or re.search(r'acord|chor', t, re.I)):
        m.append('despertar')
    if a.get('atribuicao_palavra') or ('literal' in p and R_ATRIB.search(t)):
        m.append('atribuicao')
    if 'bandeira' in (a.get('marcas') or []):
        m.append('bandeira')
    if ('figurado' in p and not a.get('figura')) or R_FIG.search(t):
        m.append('figura')
    return m


def main():
    itens = []
    for f in sorted(glob.glob(str(V33 / '*_anotado.jsonl'))):
        entrada = f.replace('_anotado.jsonl', '.jsonl')
        textos = {json.loads(l)['id']: json.loads(l) for l in open(entrada)}
        for l in open(f):
            a = json.loads(l)
            t = textos[a['id']]
            m = motivos(a, t['texto'])
            if m:
                itens.append({'id': a['id'], 'bolsa': t['bolsa'], 'forma': t['forma'], 'motivos': m,
                              'anotacao_v33': a, 'texto': t['texto']})
    SAIDA.mkdir(parents=True, exist_ok=True)
    for p in SAIDA.glob('corr_*.jsonl'):
        if not p.name.endswith('_anotado.jsonl'):
            p.unlink()
    lote, tam, k = [], 0, 1
    for x in itens:
        if lote and (tam + len(x["texto"]) > LIMITE or len(lote) >= MAX_ITENS):
            with open(SAIDA / f'corr_{k}.jsonl', 'w') as f:
                f.writelines(json.dumps(y, ensure_ascii=False) + '\n' for y in lote)
            lote, tam, k = [], 0, k + 1
        lote.append(x); tam += len(x['texto'])
    with open(SAIDA / f'corr_{k}.jsonl', 'w') as f:
        f.writelines(json.dumps(y, ensure_ascii=False) + '\n' for y in lote)
    print(f'{len(itens)} textos a corrigir em {k} lotes')
    print(Counter(m for x in itens for m in x['motivos']))


if __name__ == '__main__':
    main()
