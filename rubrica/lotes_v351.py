#!/usr/bin/env python3
"""Lotes da v3.5.1 (27/09, noite) — duas decisões do Fitipe que só um leitor
aplica (não dá para decidir por palavra):

  bandeira  toda anotação que teve bandeira na v3.4 ou na v3.5 (155). Regra
            nova: ideação suicida PRESENTE levanta, mesmo sem plano; desejo
            passivo e vago ("morrer seria melhor", "quero sumir") não;
            menor de idade com ideação sempre levanta; ódio a PESSOA só com
            ameaça ou desejo de dano (xingamento sozinho não); ódio ou
            estereótipo depreciativo contra GRUPO levanta; ódio a si sem
            intenção não.
  triste    literal com `acordou_mal` e sem `decepcao` (441). Regra nova:
            "acordei triste/tô mal" depois de conteúdo claramente desejado,
            mesmo sem "não era real", é `decepcao` (e carga prazerosa).

  python3 lotes_v351.py  →  rubrica/lotes/v351/{bandeira,triste}_<k>.jsonl
"""
import json
import sqlite3
from pathlib import Path

AQUI = Path(__file__).parent
SAIDA = AQUI / 'lotes' / 'v351'
DB = AQUI.parent / 'arquivo' / 'arquivo.db'


def main():
    v34 = {json.loads(l)['id']: json.loads(l) for l in open(AQUI / 'lotes/v34/final_v34.jsonl')}
    v35 = [json.loads(l) for l in open(AQUI / 'lotes/v35/final_v35.jsonl')]
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    tx = dict(con.execute(f"SELECT id, texto FROM relatos WHERE id IN ({','.join('?' * len(v35))})",
                          [a['id'] for a in v35]))
    band = [a for a in v35 if 'bandeira' in (a.get('marcas') or []) or 'bandeira' in (v34[a['id']].get('marcas') or [])]
    trist = [a for a in v35 if 'literal' in a['portao'] and 'acordou_mal' in (a.get('despertar') or [])
             and 'decepcao' not in (a.get('despertar') or []) and a not in band]
    SAIDA.mkdir(parents=True, exist_ok=True)
    for nome, itens, k in (('bandeira', band, 160), ('triste', trist, 230)):
        for j in range(0, len(itens), k):
            with open(SAIDA / f'{nome}_{j // k + 1}.jsonl', 'w') as f:
                for a in itens[j:j + k]:
                    base = {c: v for c, v in a.items() if c not in ('mudou', 'versao', 'bolsa')}
                    f.write(json.dumps({'id': a['id'], 'anotacao_v35': base, 'texto': tx[a['id']]},
                                       ensure_ascii=False) + '\n')
        print(nome, len(itens))


if __name__ == '__main__':
    main()
