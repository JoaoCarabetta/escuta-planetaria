#!/usr/bin/env python3
"""Haiku × Sonnet × aluno (BERT) contra o Opus na amostra-prova v3.5 (27/09).

O Opus anotou os 300 do zero pela v3.5 (lotes/v35/prova_*_anotado) — é a
régua. Haiku e Sonnet anotaram os mesmos 300 pela mesma rubrica; o aluno
entra pelas decisões gravadas em predicoes_v35. A pergunta: qual modelo
barato faz os 15 mil de afeto depois da V3? Mede por campo, e só nas
cabeças que valem para o texto (carga/despertar/conteúdo onde o Opus diz
literal).

A 1ª tentativa do Haiku na prova_1 foi descartada (rotulou por regex);
vale teste_haiku_v2/prova_1.
"""
import json
import sqlite3
from pathlib import Path

L = Path(__file__).parent / 'lotes' / 'v35'
DB = Path(__file__).parent.parent / 'arquivo' / 'arquivo.db'


def ler(*arqs):
    d = {}
    for a in arqs:
        for l in open(L / a):
            x = json.loads(l); d[x['id']] = x
    return d


def S(v):
    return set(v) if isinstance(v, list) else ({v} if v else set())


def main():
    opus = ler('prova_1_anotado.jsonl', 'prova_2_anotado.jsonl')
    mods = {'haiku': ler('teste_haiku_v2/prova_1_anotado.jsonl', 'teste_haiku/prova_2_anotado.jsonl'),
            'sonnet': ler('teste_sonnet/prova_1_anotado.jsonl', 'teste_sonnet/prova_2_anotado.jsonl')}
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    bert = {}
    for rid, dp, dc, dd, dco in con.execute(
            f"SELECT relato_id, portao, carga, despertar, conteudo "
            f"FROM predicoes_v35 WHERE relato_id IN ({','.join('?' * len(opus))})", list(opus)):
        j = lambda v: json.loads(v) if v and v.startswith('[') else ([v] if v else [])
        bert[rid] = {'portao': j(dp), 'carga': j(dc), 'despertar': j(dd), 'conteudo': dco}
    mods['bert'] = bert

    def lit(x): return 'literal' in S(x.get('portao'))
    campos = [('literal?', lambda x: lit(x), None),
              ('portão exato', lambda x: frozenset(S(x.get('portao')) - {'ambiguo'}), None),
              ('carga exata', lambda x: frozenset(S(x.get('carga'))), 'lit'),
              ('carga toca', lambda x: frozenset(S(x.get('carga'))), 'toca'),
              ('conteúdo', lambda x: x.get('conteudo'), 'lit'),
              ('despertar exato', lambda x: frozenset(S(x.get('despertar'))), 'lit'),
              ('tem atribuição', lambda x: bool(x.get('atribuicao_palavra')), 'litfala')]
    print(f"{'campo':18s}" + ''.join(f'{m:>10s}' for m in mods))
    for nome, f, cond in campos:
        linha = f'{nome:18s}'
        for m, d in mods.items():
            ok = n = 0
            for i, o in opus.items():
                if i not in d: continue
                if cond in ('lit', 'toca') and not (lit(o) and lit(d[i])): continue
                if cond == 'litfala' and not (S(o.get('portao')) & {'literal', 'fala_do_sonhar'}): continue
                if m == 'bert' and nome == 'tem atribuição': continue
                a, b = f(o), f(d[i])
                ok += (bool(a & b) or a == b) if cond == 'toca' else (a == b); n += 1
            linha += f'{(100 * ok / n if n else float("nan")):9.1f}%'
        print(linha)
    print('\n(n: literal/portão sobre os 300; carga/conteúdo/despertar onde os dois dizem literal)')


if __name__ == '__main__':
    main()
