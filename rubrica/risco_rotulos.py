#!/usr/bin/env python3
"""Rótulos de BANDEIRA já conferidos, reconciliados na regra v3.5.1 (27/09).

Por que um módulo à parte: as duas vias de busca de candidatos (palavras e
sonda, `risco_palavras.py` e `risco_sonda_v351.py`) precisam do MESMO
conjunto de positivos/negativos e do MESMO conjunto de "já conferidos" (que
nunca voltam a ser candidatos). Se cada script reconciliasse por conta
própria, as duas listas divergiriam em silêncio.

Fontes, da mais forte para a mais fraca (a mais forte vence no conflito):

  4. rubrica/lotes/v351/*_anotado.jsonl   — regra NOVA (v3.5.1), `marcas`
  3. rubrica/lotes/v35/final_v35.jsonl     — v3.5 (regravado após a v3.5.1)
  2. rubrica/lotes/risco_conferidos*.jsonl — conferência da sonda (26/09),
     regra ANTIGA. A regra mudou: ódio a si sem ideação e desejo passivo
     vago deixaram de levantar; ódio a pessoa só com ameaça/desejo de dano.
     Então: positivo `si` urgente/alta/media e `outros`/`relatado`
     urgente/alta continuam POSITIVOS; `si` baixa e `outros` baixa/media/
     nenhuma, e notas que falam só de auto-ódio, ficam AMBÍGUOS (conferidos,
     mas fora do treino). Negativos continuam negativos.
  1. anotacoes_v3 json_extract(extra,'$.bandeira') — a última por relato.

Conferidos também: rubrica/lotes/v3*/*_anotado.jsonl (toda anotação v3.x
passou pela pergunta da bandeira), cuidado_manual.jsonl e os índices já
escondidos em planeta-v2/dados/cuidado.json (mapeados de volta a id pelo
texto+data, como faz arquivo/atualizar_cuidado.py, só que ao contrário).

`carregar()` devolve (rotulo: id→1|0, conferidos: set de ids, info: dict).
Rótulo ausente para um id conferido = ambíguo (não entra no treino).
"""
import glob
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
LOTES = AQUI / 'lotes'
DB = RAIZ / 'arquivo' / 'arquivo.db'
PAGINA = RAIZ / 'planeta-v2' / 'dados'

# nota do conferente que fala só de auto-ódio (sem ideação) → ambíguo na v3.5.1
_SO_AUTOODIO = re.compile(r'auto.?[oó]dio|[oó]dio a si|se odeia|odeia a si', re.I)
_IDEACAO = re.compile(r'suic|idea[cç]|se matar|morrer|morte|autoles|automut|cort|plano|'
                      r'tentativ|despedida|tirar a (pr[oó]pria )?vida|acabar com|m[eé]todo', re.I)


def _jsonl(caminho):
    for l in open(caminho):
        if l.strip():
            yield json.loads(l)


def conectar():
    return sqlite3.connect(f'file:{DB}?mode=ro', uri=True)


def ids_da_pagina():
    """Ids que estão na página pública hoje (V2): os que o projetar.py posicionou."""
    return {i for i in open(PAGINA / 'projecao_ids.txt').read().split('\n') if i}


def escondidos_na_pagina(con):
    """Índices do cuidado.json → ids, pelo texto+data publicados."""
    idx = set(json.load(open(PAGINA / 'cuidado.json')))
    meta = json.load(open(PAGINA / 'meta.json'))
    alvo = {}
    for b in range(meta['arquivos_texto']):
        bl = json.load(open(PAGINA / f'textos{b}.json'))
        for k, t in enumerate(bl['textos']):
            if bl['i0'] + k in idx:
                alvo[t] = bl['quando'][k]
    ids = set()
    pag = ids_da_pagina()
    for rid, t in con.execute('SELECT id, texto FROM relatos WHERE canonico_de IS NULL'):
        if rid in pag and t[:40000] in alvo:
            ids.add(rid)
    return ids


def carregar(con=None, com_cuidado=True):
    con = con or conectar()
    rotulo, fonte_do = {}, {}
    conferidos = set()
    ambiguos = Counter()

    # 1. anotacoes_v3 (mais fraca): última anotação com bandeira dita
    for rid, b in con.execute("""SELECT relato_id, json_extract(extra,'$.bandeira') FROM anotacoes_v3
                                 WHERE json_extract(extra,'$.bandeira') IS NOT NULL ORDER BY id"""):
        rotulo[rid] = int(bool(b)); fonte_do[rid] = 'anotacoes_v3'; conferidos.add(rid)

    # 2. conferência da sonda, regra antiga, reconciliada
    for f in sorted(glob.glob(str(LOTES / 'risco_conferidos*.jsonl'))):
        for x in _jsonl(f):
            rid = x['id']; conferidos.add(rid)
            if not x.get('bandeira'):
                rotulo[rid] = 0; fonte_do[rid] = 'sonda26'; continue
            tipo, grav, nota = x.get('tipo'), x.get('gravidade'), x.get('nota') or ''
            firme = ((tipo == 'si' and grav in ('urgente', 'alta', 'media')) or
                     (tipo in ('outros', 'relatado') and grav in ('urgente', 'alta')))
            if firme and _SO_AUTOODIO.search(nota) and not _IDEACAO.search(nota):
                firme = False
            if firme:
                rotulo[rid] = 1; fonte_do[rid] = 'sonda26'
            else:
                rotulo.pop(rid, None); fonte_do[rid] = 'sonda26_ambiguo'
                ambiguos[f'{tipo}/{grav}'] += 1

    # anotações v3.x antigas: só contam como conferidas (o rótulo vem do final_v35)
    for f in glob.glob(str(LOTES / 'v3*' / '*_anotado.jsonl')):
        for x in _jsonl(f):
            conferidos.add(x['id'])

    # 3. final_v35
    for x in _jsonl(LOTES / 'v35' / 'final_v35.jsonl'):
        rotulo[x['id']] = int('bandeira' in (x.get('marcas') or []))
        fonte_do[x['id']] = 'v35'; conferidos.add(x['id'])

    # 4. v3.5.1 (mais forte)
    for f in sorted(glob.glob(str(LOTES / 'v351' / '*_anotado.jsonl'))):
        for x in _jsonl(f):
            rotulo[x['id']] = int('bandeira' in (x.get('marcas') or []))
            fonte_do[x['id']] = 'v351'; conferidos.add(x['id'])

    manual = LOTES / 'cuidado_manual.jsonl'
    if manual.exists():
        for x in _jsonl(manual):
            conferidos.add(x['id'])
    # conferências já feitas por ESTA rodada (risco_v351), se existirem
    for f in glob.glob(str(LOTES / 'risco_v351' / '*_conferido*.jsonl')):
        for x in _jsonl(f):
            conferidos.add(x['id'])
            if 'bandeira' in x:
                rotulo[x['id']] = int(bool(x['bandeira'])); fonte_do[x['id']] = 'risco_v351'

    esc = escondidos_na_pagina(con) if com_cuidado else set()
    conferidos |= esc
    info = {'positivos': sum(rotulo.values()), 'negativos': len(rotulo) - sum(rotulo.values()),
            'conferidos': len(conferidos), 'ambiguos': dict(ambiguos),
            'por_fonte': dict(Counter(fonte_do[r] for r in rotulo)), 'escondidos_na_pagina': len(esc)}
    return rotulo, conferidos, info


if __name__ == '__main__':
    r, c, info = carregar()
    print(json.dumps(info, ensure_ascii=False, indent=1))
