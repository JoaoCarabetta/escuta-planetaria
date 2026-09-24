#!/usr/bin/env python3
"""Monta os conjuntos de treino, validação e prova a partir de `anotacoes_v3`.

A separação é a do `rubrica/desenho-do-treino.md` e não pode ser afrouxada aqui:

  TREINO    anotações `claude:v3*` das bolsas por pista de superfície.
  VALIDAÇÃO 10% do treino, sorteado com semente fixa. Serve para parar de
            treinar na hora certa — e por isso também não pode ser a prova.
  PROVA     os 300 sorteados uniformemente (`amostra_prova`) e os 70 do Fitipe.
            Nunca veem treino. Se vissem, a nota mediria memória, não leitura.

O `sonhador`, a `carga` e o `despertar` só existem sob `literal`; onde o portão
não tem literal, o rótulo é -100, que é como o PyTorch marca "não cobre este".
"""
import hashlib
import json
import random
import re
import sqlite3
import unicodedata
from pathlib import Path

DB = Path(__file__).parent.parent / 'arquivo' / 'arquivo.db'
SEMENTE = 2015

PORTAO = ['literal', 'figurado', 'devaneio', 'fala_do_sonhar',
          'obra', 'noticia', 'propaganda', 'descartavel']
CARGA = ['prazerosa', 'neutra', 'aflitiva', 'mista', 'sem_afeto_dito', 'sem_conteudo']
TOM = ['leve', 'ironico', 'lamento', 'aflito', 'confidencia', 'indignado',
       'hesitante', 'grave', 'seco']
SONHADOR = ['proprio', 'terceiro', 'citado']
BINARIOS = ['meta', 'bandeira']


# A `carga` da v3.1 usava um valor `nao_dito` que a v3.2 partiu em
# `sem_afeto_dito` e `sem_conteudo`. Não há como decidir retroativamente qual
# dos dois cada `nao_dito` era, então essas linhas entram com -100 na cabeça
# da carga: perdem o rótulo daquele campo e mantêm todos os outros. É perda
# declarada, não conversão inventada.

def uma(v):
    """Primeiro valor de uma lista JSON, ou None. Campos de valor único foram
    gravados como lista porque o anotador humano podia marcar mais de um."""
    try:
        l = json.loads(v or '[]')
    except Exception:
        l = [v] if v else []
    return l[0] if l else None


def linhas(con, onde):
    q = f"""SELECT a.relato_id, r.texto, a.tem_literal, a.tem_figurado, a.tem_devaneio,
                   a.carga, a.tom, a.meta, a.descartavel, a.extra, a.confianca
            FROM anotacoes_v3 a JOIN relatos r ON r.id = a.relato_id WHERE {onde}"""
    saida = []
    for rid, txt, l, f, d, cg, tm, m, x, ex, conf in con.execute(q):
        e = json.loads(ex or '{}')
        p = [0] * len(PORTAO)
        for i, k in enumerate(PORTAO):
            if k == 'literal': p[i] = int(bool(l))
            elif k == 'figurado': p[i] = int(bool(f))
            elif k == 'devaneio': p[i] = int(bool(d))
            elif k == 'descartavel': p[i] = int(bool(x))
            else: p[i] = int(bool(e.get(k)))
        tom = [0] * len(TOM)
        try:
            for v in json.loads(tm or '[]'):
                if v in TOM: tom[TOM.index(v)] = 1
        except Exception:
            pass
        cgv = uma(cg)
        snv = uma(json.dumps(e.get('sonhador') or []))
        saida.append(dict(
            id=rid, texto=txt, portao=p, tom=tom,
            carga=CARGA.index(cgv) if (p[0] and cgv in CARGA) else -100,
            sonhador=SONHADOR.index(snv) if (p[0] and snv in SONHADOR) else -100,
            meta=int(bool(m)), bandeira=int(bool(e.get('bandeira'))),
            confianca=conf))
    return saida


def impressao(texto):
    """Assinatura do texto, insensível a acento, caixa e pontuação.

    A régua de duplicatas só compara o que o qwen chamou de `relato` — 22.641
    relatos com embedding ficam fora do alcance dela, e é justamente onde mora
    o anúncio. Três textos de marketing da MESMA fôrma ("a cobertura dos sonhos
    em Ipanema, desenhada pela arquiteta Maria Eduarda") entraram no treino sem
    nenhuma entrada na tabela de ecos. Com `propaganda` sendo classe rara, três
    cópias de uma fôrma podem ser um quarto dos exemplos dela — e aí o modelo
    aprende aquela frase, não a classe.

    Aqui a defesa é exata e barata: assinatura do texto normalizado. Não
    substitui consertar a régua; impede o dano no treino de hoje.
    """
    s = unicodedata.normalize('NFD', (texto or '').lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return hashlib.blake2b(re.sub(r'\W+', ' ', s).strip().encode(), digest_size=8).hexdigest()


def conjuntos():
    con = sqlite3.connect(DB, timeout=300)
    treino = linhas(con, """a.anotador LIKE 'claude:v3%'
        AND a.relato_id NOT IN (SELECT relato_id FROM amostra_prova)
        AND a.relato_id NOT IN (SELECT relato_id FROM anotacoes_v3 WHERE anotador='fitipe')""")
    # um relato pode ter sido anotado na v3.1 e na v3.2: fica a mais recente
    vistos, marcas, limpo, repetidos = set(), set(), [], 0
    for r in reversed(treino):
        if r['id'] in vistos:
            continue
        m = impressao(r['texto'])
        if m in marcas:                      # mesma fôrma, texto diferente de id
            repetidos += 1
            continue
        vistos.add(r['id']); marcas.add(m); limpo.append(r)
    treino = limpo
    if repetidos:
        print(f'  {repetidos} textos idênticos removidos do treino')
    prova = linhas(con, "a.anotador LIKE 'claude:v32:%' AND a.relato_id IN (SELECT relato_id FROM amostra_prova)")
    humano = linhas(con, "a.anotador = 'fitipe'")

    rng = random.Random(SEMENTE)
    rng.shuffle(treino)
    corte = max(1, len(treino) // 10)
    return treino[corte:], treino[:corte], prova, humano


if __name__ == '__main__':
    tr, val, pv, hm = conjuntos()
    print(f'treino {len(tr)} · validação {len(val)} · prova {len(pv)} · humano {len(hm)}')
    from collections import Counter
    print('portão no treino:', {PORTAO[i]: sum(r['portao'][i] for r in tr) for i in range(len(PORTAO))})
    print('carga no treino:', Counter(CARGA[r['carga']] if r['carga'] >= 0 else '—' for r in tr))
    print('vazamento prova→treino:', len({r['id'] for r in tr} & {r['id'] for r in pv + hm}))
