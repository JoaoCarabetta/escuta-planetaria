#!/usr/bin/env python3
"""Conjuntos do aluno v3.5 — treino, validação e as duas réguas.

  TREINO     `rubrica/lotes/v35/final_v35.jsonl` (3.473 anotações v3.5, Opus).
             Opcionalmente (--v3), as anotações antigas de `anotacoes_v3` que NÃO
             estão no final_v35, só para o PORTÃO e só nas células compatíveis
             (ver `rotulos_v3`). Tudo o mais delas entra como -100.
  VALIDAÇÃO  10% do final_v35, semente 2015. Só v3.5: a v3 nunca decide época.
  PROVA      os 300 da `amostra_prova`, anotados do zero pela v3.5
             (`prova_1_anotado.jsonl` + `prova_2_anotado.jsonl`). Nunca treino.
  CEGA       os 83 da revisão cega do Fitipe (`revisao_cega_*`): segunda régua,
             só literal × não-literal e figurado. Nunca treino.

Convenção de máscara: -100 = "esta célula não tem rótulo". Vale célula a célula
(o portão da v3 tem máscara por classe) e cabeça a cabeça (carga só sob
literal, figura só sob figurado, etc.).

`ambiguo` não é classe: é máscara. Num texto `["literal","figurado","ambiguo"]`
as candidatas (literal, figurado) ficam -100 no portão e as não candidatas 0.
As cabeças condicionais seguem a regra da rubrica: valem se `literal` está
entre as candidatas.
"""
import hashlib
import json
import random
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
DB = RAIZ / 'arquivo' / 'arquivo.db'
V35 = RAIZ / 'rubrica' / 'lotes' / 'v35'
LOTES = RAIZ / 'rubrica' / 'lotes'
SEMENTE = 2015
M = -100

PORTAO = ['literal', 'figurado', 'fala_do_sonhar', 'devaneio',
          'obra', 'noticia', 'propaganda', 'descartavel']
CARGA = ['prazerosa', 'aflitiva', 'mista', 'estranha', 'sem_afeto_dito']
CONTEUDO = ['narrado', 'so_mencionado']
DESPERTAR = ['alivio', 'decepcao', 'acordou_mal', 'acordou_bem',
             'desorientado', 'acordou_neutro']
# figura: <15 exemplos no final_v35 vai para 'outra' (metafora 14, escape 14,
# titulo_obra 6, comercial 2, homonimo/marca/toponimo 1 cada). Contado, não
# escolhido: ver `contar_raros`.
FIGURA = ['desejo', 'intensificador', 'votos', 'outra']
# origem: outra_pessoa (12) vai para 'outra'
ORIGEM = ['nao_diz', 'a_si', 'entidade_religiosa', 'espirito_proprio',
          'universo_destino', 'morto', 'outra']
MINIMO_RARO = 15

CABECAS = dict(portao=PORTAO, carga=CARGA, despertar=DESPERTAR, figura=FIGURA,
               origem=ORIGEM)          # multi-rótulo (sigmoide)
# conteudo: 2 classes exclusivas (CE); tem_atrib e bandeira: binárias (sigmoide)


def ler_jsonl(p):
    return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]


def multi(valores, nomes, mapa_outra=None):
    v = [0] * len(nomes)
    for x in valores or []:
        if x in nomes:
            v[nomes.index(x)] = 1
        elif mapa_outra and 'outra' in nomes:
            v[nomes.index('outra')] = 1
    return v


def rotulos_v35(a):
    """Uma anotação v3.5 → alvos de todas as cabeças."""
    pt = set(a.get('portao') or [])
    amb = 'ambiguo' in pt
    portao = [(M if (amb and k in pt) else int(k in pt)) for k in PORTAO]
    lit = 'literal' in pt
    fal = 'fala_do_sonhar' in pt
    fig = 'figurado' in pt
    r = dict(portao=portao)
    r['carga'] = multi(a.get('carga'), CARGA) if (lit and a.get('carga')) else [M] * len(CARGA)
    c = a.get('conteudo')
    r['conteudo'] = CONTEUDO.index(c) if (lit and c in CONTEUDO) else M
    r['despertar'] = multi(a.get('despertar'), DESPERTAR) if lit else [M] * len(DESPERTAR)
    # figura vazia sob figurado existe (≈raro); entra como tudo-zero, que é o dito
    r['figura'] = multi(a.get('figura'), FIGURA, True) if fig else [M] * len(FIGURA)
    orig = a.get('atribuicao_origem') or []
    if lit or fal:
        r['tem_atrib'] = int(bool(orig))
        r['origem'] = multi(orig, ORIGEM, True) if orig else [M] * len(ORIGEM)
    else:
        r['tem_atrib'] = M
        r['origem'] = [M] * len(ORIGEM)
    r['bandeira'] = int('bandeira' in (a.get('marcas') or []))
    return r


def vazio():
    return dict(portao=[M] * len(PORTAO), carga=[M] * len(CARGA), conteudo=M,
                despertar=[M] * len(DESPERTAR), figura=[M] * len(FIGURA),
                tem_atrib=M, origem=[M] * len(ORIGEM), bandeira=M)


def rotulos_v3(votos):
    """Anotações v3.x (vários anotadores por relato) → só o portão, célula a
    célula, e só onde o significado não mudou.

    Na v3.2 `literal` e `fala_do_sonhar` eram EXCLUDENTES; na v3.5 combinam
    (hábito com conteúdo = os dois). Então:
      literal=1                → literal 1 (sonho contado continua sonho)
                                 fala_do_sonhar -100 (podia ser hábito)
      fala_do_sonhar=1         → fala 1; literal -100 (podia ter conteúdo)
      nem um nem outro         → literal 0, fala 0
    figurado, obra, noticia, propaganda, descartavel: sem mudança de definição
    relevante → valem. devaneio: a v3.5 exige cena com ação e duração, e o
    devaneio sem cena virou figurado/escape → -100.
    Várias anotações do mesmo relato: célula só vale se TODAS concordam;
    divergência vira -100. Carga, figura, despertar, atribuição, bandeira: tudo
    -100 (carga tinha outro significado; bandeira mudou de regra; figura tinha
    outros valores).
    """
    celulas = defaultdict(set)
    for l, f, fala, ob, no, pr, de in votos:
        if l:
            celulas['literal'].add(1); celulas['fala_do_sonhar'].add(M)
        elif fala:
            celulas['fala_do_sonhar'].add(1); celulas['literal'].add(M)
        else:
            celulas['literal'].add(0); celulas['fala_do_sonhar'].add(0)
        for k, v in (('figurado', f), ('obra', ob), ('noticia', no),
                     ('propaganda', pr), ('descartavel', de)):
            celulas[k].add(int(bool(v)))
    p = []
    for k in PORTAO:
        s = celulas.get(k)
        p.append(next(iter(s)) if (s and len(s) == 1) else M)
    r = vazio()
    r['portao'] = p
    return r


def impressao(texto):
    s = unicodedata.normalize('NFD', (texto or '').lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return hashlib.blake2b(re.sub(r'\W+', ' ', s).strip().encode(), digest_size=8).hexdigest()


def conectar():
    return sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=300)


def textos(con, ids):
    ids = list(ids)
    out = {}
    for i in range(0, len(ids), 900):
        pedaco = ids[i:i + 900]
        q = ','.join('?' * len(pedaco))
        out.update(dict(con.execute(f'SELECT id, texto FROM relatos WHERE id IN ({q})', pedaco)))
    return out


def ids_proibidos(con):
    prova = {r[0] for r in con.execute('SELECT relato_id FROM amostra_prova')}
    cega = {a['id'] for a in ler_jsonl(LOTES / 'revisao_cega_fitipe.jsonl')}
    fitipe70 = {r[0] for r in con.execute("SELECT relato_id FROM anotacoes_v3 WHERE anotador='fitipe'")}
    copia = {r[0] for r in con.execute("SELECT relato_id FROM grupos_copia WHERE tipo='copy_paste'")}
    return prova, cega, fitipe70, copia


def prova_v35(con):
    """Os 300 com o gabarito v3.5. Devolve (linhas, quantas do prova_1)."""
    ans = []
    n1 = 0
    for nome in ('prova_1_anotado.jsonl', 'prova_2_anotado.jsonl'):
        p = V35 / nome
        if p.exists():
            L = ler_jsonl(p)
            if nome.startswith('prova_1'):
                n1 = len(L)
            ans += L
    tx = textos(con, [a['id'] for a in ans])
    return [dict(id=a['id'], texto=tx[a['id']], bruto=a, **rotulos_v35(a)) for a in ans], n1


def cega(con):
    """Revisão cega: portão humano em outro vocabulário. `nao_dormido` = não
    literal; portão vazio ou só 'literal' = literal. figurado vale como está."""
    R = {a['id']: a for a in ler_jsonl(LOTES / 'revisao_cega_respostas_fitipe.jsonl')}
    tx = textos(con, R)
    out = []
    for i, a in R.items():
        pt = set(a['portao'])
        out.append(dict(id=i, texto=tx[i], literal=int('nao_dormido' not in pt),
                        figurado=int('figurado' in pt)))
    return out


def conjuntos(usar_v3=False, verbose=True):
    con = conectar()
    prova, cg, f70, copia = ids_proibidos(con)
    proibidos = prova | cg | f70
    anot = ler_jsonl(V35 / 'final_v35.jsonl')
    tx = textos(con, [a['id'] for a in anot])
    # impressões dos textos de prova: um texto idêntico a um da prova, com
    # outro id, também não pode ir para o treino
    marcas_prova = {impressao(t) for t in textos(con, proibidos).values()}

    linhas, fora = [], Counter()
    marcas = set()
    for a in anot:
        i = a['id']
        if i in proibidos:
            fora['prova/cega/70'] += 1; continue
        if i in copia:
            fora['copy_paste'] += 1; continue
        m = impressao(tx[i])
        if m in marcas_prova:
            fora['igual a texto de prova'] += 1; continue
        if m in marcas:
            fora['texto repetido'] += 1; continue
        marcas.add(m)
        linhas.append(dict(id=i, texto=tx[i], bolsa=a.get('bolsa'), origem_rot='v35',
                           **rotulos_v35(a)))

    rng = random.Random(SEMENTE)
    rng.shuffle(linhas)
    corte = len(linhas) // 10
    val, tr = linhas[:corte], linhas[corte:]

    extra = []
    if usar_v3:
        ja = {r['id'] for r in linhas} | {a['id'] for a in anot}
        votos = defaultdict(list)
        q = """SELECT relato_id, tem_literal, tem_figurado, extra, descartavel
               FROM anotacoes_v3 WHERE anotador LIKE 'claude:%'
               AND anotador NOT LIKE 'claude:aud%'"""
        for rid, l, f, ex, de in con.execute(q):
            if rid in ja or rid in proibidos or rid in copia:
                continue
            e = json.loads(ex or '{}')
            votos[rid].append((l, f, e.get('fala_do_sonhar'), e.get('obra'),
                               e.get('noticia'), e.get('propaganda'), de))
        tx3 = textos(con, votos)
        for rid, vs in votos.items():
            m = impressao(tx3[rid])
            if m in marcas or m in marcas_prova:
                fora['v3 repetido/prova'] += 1; continue
            marcas.add(m)
            r = rotulos_v3(vs)
            if all(x == M for x in r['portao']):
                continue
            extra.append(dict(id=rid, texto=tx3[rid], bolsa='v3', origem_rot='v3', **r))
        tr = tr + extra
    if verbose:
        print(f'treino {len(tr)} (v3: {len(extra)}) · validação {len(val)} · descartados {dict(fora)}',
              flush=True)
    return tr, val


def contar(linhas, cab, nomes):
    c = Counter()
    for r in linhas:
        for k, v in zip(nomes, r[cab]):
            if v == 1:
                c[k] += 1
    return c


if __name__ == '__main__':
    import sys
    tr, val = conjuntos('--v3' in sys.argv)
    for cab, nomes in CABECAS.items():
        print(cab, dict(contar(tr, cab, nomes)))
    print('conteudo', Counter(r['conteudo'] for r in tr))
    print('tem_atrib', Counter(r['tem_atrib'] for r in tr), 'bandeira', Counter(r['bandeira'] for r in tr))
    con = conectar()
    pv, n1 = prova_v35(con)
    print('prova', len(pv), 'prova_1', n1, 'vazamento', len({r['id'] for r in tr + val} & {r['id'] for r in pv}))
    for cab, nomes in CABECAS.items():
        print(' prova', cab, dict(contar(pv, cab, nomes)))
    # viés de prior: sorteio x resto do treino
    so = [r for r in tr + val if r['bolsa'] == 'sorteio']
    print('\nprior do portão: sorteio (n=%d) x treino v35 (n=%d) x prova' % (len(so), sum(r['origem_rot'] == 'v35' for r in tr + val)))
    t35 = [r for r in tr + val if r['origem_rot'] == 'v35']
    for k in PORTAO:
        i = PORTAO.index(k)
        f = lambda L: 100 * sum(r['portao'][i] == 1 for r in L) / len(L)
        print(f'  {k:15s} {f(so):5.1f}% {f(t35):5.1f}% {f(pv):5.1f}%')
    f = lambda L: 100 * sum(r['bandeira'] == 1 for r in L) / len(L)
    print(f'  {"bandeira":15s} {f(so):5.1f}% {f(t35):5.1f}% {f(pv):5.1f}%')
