#!/usr/bin/env python3
"""Junta a anotação v3.4 final dos 3.473 textos de 27/09.

  - os 2.177 corrigidos por agentes (lotes/v34/corr_*_anotado.jsonl) valem
    como estão;
  - os outros 1.296 não tinham motivo de revisão e passam da v3.3 para a
    v3.4 por regra mecânica:
      `meta` (marca)  → `fala_do_sonhar` no portão (literal + fala agora
                        combinam; a marca saiu)
      carga `neutra`  → `sem_afeto_dito` (fundidas)
      `sonhador`      → lista
      atribuicao_quem → lista vazia (sem atribuição, nada a dizer)

Confere que todo id aparece exatamente uma vez e que as listas de
atribuição têm o mesmo tamanho.

  python3 aplicar_v34.py  →  rubrica/lotes/v34/final_v34.jsonl
"""
import glob
import json
import re
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).parent
V33 = AQUI / 'lotes' / 'v33'
V34 = AQUI / 'lotes' / 'v34'
# v3.4.1 (27/09): a regra "o '?' decide a postura" falhou — 8 dos 17
# corretores apontaram, sozinhos, que pedido de leitura e pergunta direta
# sem "?" ("oq isso significa", "alguém interpreta pra mim", "não sei o
# que isso significa") viravam `cogita`. Passam a `pergunta`; "será que",
# "acho que", "deve ser" e "talvez" continuam `cogita`.
R_PERGUNTA = re.compile(r"\b(o\s*que|oq|oque|qq|qual|quais|por\s*que|pq|me ajud|interpret|"
                        r"gostaria de saber|quero saber|queria saber|sabe[m]? (o que|se))", re.I)
R_COGITA = re.compile(r"\b(acho|será que|sera que|deve ser|talvez)\b|\bcomo se\b", re.I)


def postura_v341(a):
    n = 0
    post = list(a.get('atribuicao_postura') or [])
    for i, (pal, s) in enumerate(zip(a.get('atribuicao_palavra') or [], post)):
        if s == 'cogita' and R_PERGUNTA.search(pal) and not R_COGITA.search(pal):
            post[i] = 'pergunta'; n += 1
    a['atribuicao_postura'] = post
    return n


ATRIB = ('atribuicao_palavra', 'atribuicao_origem', 'atribuicao_postura', 'atribuicao_quem')


def converter(a):
    a = dict(a)
    marcas = [m for m in a.get('marcas') or [] if m != 'meta']
    if 'meta' in (a.get('marcas') or []) and 'fala_do_sonhar' not in a['portao']:
        a['portao'] = a['portao'] + ['fala_do_sonhar']
    a['marcas'] = marcas
    a['carga'] = list(dict.fromkeys('sem_afeto_dito' if c == 'neutra' else c for c in a.get('carga') or []))
    s = a.get('sonhador')
    a['sonhador'] = s if isinstance(s, list) else ([s] if s else [])
    a.setdefault('atribuicao_quem', [])
    if len(a['atribuicao_quem']) != len(a.get('atribuicao_palavra') or []):
        a['atribuicao_quem'] = ['a_pessoa'] * len(a.get('atribuicao_palavra') or [])
    a['versao'] = 'v3.3→v3.4 (regra)'
    return a


def main():
    corrigidos = {}
    for f in glob.glob(str(V34 / 'corr_*_anotado.jsonl')):
        for l in open(f):
            d = json.loads(l)
            d['versao'] = 'v3.4 (agente)'
            corrigidos[d['id']] = d
    esperados = {json.loads(l)['id'] for f in glob.glob(str(V34 / 'corr_*.jsonl'))
                 if not f.endswith('_anotado.jsonl') for l in open(f)}
    faltam = esperados - set(corrigidos)
    if faltam:
        raise SystemExit(f'{len(faltam)} corrigidos faltando — algum agente não terminou')
    final, vistos, trocas = [], set(), 0
    for f in sorted(glob.glob(str(V33 / '*_anotado.jsonl'))):
        bolsa = Path(f).name.rsplit('_', 2)[0]
        for l in open(f):
            a = json.loads(l)
            if a['id'] in vistos:
                raise SystemExit(f'id repetido: {a["id"]}')
            vistos.add(a['id'])
            x = corrigidos.get(a['id']) or converter(a)
            x['bolsa'] = bolsa
            trocas += postura_v341(x)
            n = {len(x.get(k) or []) for k in ATRIB}
            if len(n) > 1:
                print(f'  aviso: listas de atribuição desiguais em {a["id"]}')
            final.append(x)
    with open(V34 / 'final_v34.jsonl', 'w') as f:
        f.writelines(json.dumps(x, ensure_ascii=False) + '\n' for x in final)
    print(f'{len(final)} anotações v3.4 → lotes/v34/final_v34.jsonl')
    print(Counter(x['versao'] for x in final))
    print(f'v3.4.1: {trocas} posturas cogita → pergunta (pedido de leitura sem "?")')


if __name__ == '__main__':
    main()
