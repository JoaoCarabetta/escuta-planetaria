#!/usr/bin/env python3
"""Gera os dados do planeta V3 — o globo lido pelo aluno (portão v3.5, demais cabeças v3.6).

ALUNO (28/09): o PORTÃO (literal, figurado, fala do sonhar, camada, p_literal,
p_figurado) e a BANDEIRA vêm do aluno v3.5 (predicoes_v35); CARGA, DESPERTAR,
FIGURA, CONTEÚDO, ATRIBUIÇÃO e ORIGEM vêm do aluno v3.6 (predicoes_v36). Por
quê: o v3.6 aprendeu as classes raras, mas o portão dele piorou 1,3 ponto na
prova (92,2% → 90,9%; cega 95,2% → 92,8%) por prior inflado (83,6% de literais
no treino), e o corte calibrado (p_literal > 0,66) só corrige a taxa de literal
do arquivo, não o acerto (rubrica/medidas/portao_v35_v36_calibrado.md). Os ~3.7
mil relatos que só têm predicoes_v36 usam o portão do v3.6 com o corte 0,66
(aluno/limiar_portao_v36.json) e a bandeira do v3.6. As cabeças do v3.6 só
aparecem onde o PORTÃO DA PÁGINA (v3.5) abre a cabeça.

AFETO v2 (28/09 noite, decisão do Fitipe): nos literais, CARGA, CONTEÚDO,
DESPERTAR, ATRIBUIÇÃO e ORIGEM vêm do afeto v2 (aluno/afeto_v2.pt, treinado só
em literais; tabela predicoes_afeto_v2, inferida só onde o portão da página diz
literal) por LEFT JOIN + COALESCE; onde não há linha do v2 (não literal, ex.
fala do sonhar), segue o v3.6. FIGURA continua do v3.6 (o v2 quebra nela).
Taxas dessas cabeças refeitas com aluno/taxas_afeto_v2.py (prova 300).

V3 (28/09): julgamento do aluno (predicoes_v35/v36) no lugar do BERT v3.2;
projeção refeita com os ~50 mil comentários novos; forma do texto; leitura por
cabeça (carga, despertar, figura, atribuição); e a distinção que a V2 não
fazia entre o que foi LIDO (por Opus ou pelo Fitipe) e o que é PALPITE do
aluno — este sempre acompanhado da taxa de acerto medida daquela classe.

Formato de cada ponto (26 bytes): posição 3f · camada B · fonte B · comunidade B
· ano H · mês B · bits H · p_literal B · p_figurado B · rótulos I
  bits: 0 literal · 1 figurado · 2 incerto (nem literal nem figurado)
        3 curto · 4 médio · 5 longo · 6 enorme (um só dos quatro)
        7 tem sonho/sonhos/sonhei · 8 tem pesadelo/pesadelos
        9 fala do sonhar · 10-11 forma (0 post · 1 comentário · 2 continuação
        · 3 bluesky não verificado) · 12-13 lido (0 palpite · 1 Opus · 2 Fitipe)
        14 conteúdo narrado · 15 tem atribuição
  rótulos (um bit por classe, ver ROTULOS abaixo): carga · despertar · figura
        · origem da atribuição · só mencionado
  Nos LIDOS os bits são a leitura; nos demais, o palpite do aluno — e só nas
  classes em que a taxa medida deixa mostrar (MOSTRAR abaixo). Um bit apagado
  num palpite quer dizer "não dá para afirmar", não "não é".
  camada: 0 campo · 3 propaganda (apagada por padrão)

Princípios (acordados 2026-09-20/22): posição vem SÓ da semântica; sem
continentes fixos; três resoluções: densidade → pontos → texto.

CUIDADO (28/09): relato com bandeira NÃO ENTRA em arquivo nenhum publicado —
nem ponto, nem texto, nem índice de busca. Na V2 ele entrava e a página o
escondia (cuidado.json); quem baixasse os dados o lia do mesmo jeito.

Saída: dados/pontos.bin · textos*.json · lidos.json · busca/ · meta.json
"""
import glob
import json
import re
import sqlite3
import struct
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
DB = RAIZ / 'arquivo' / 'arquivo.db'
LOTES = RAIZ / 'rubrica' / 'lotes'
SAIDA = AQUI / 'dados'
SAIDA.mkdir(exist_ok=True)

QUALIDADES = ['curto', 'medio', 'longo', 'enorme']
CURTO, LONGO = 100, 1500
# corte de p_literal do v3.6, só para os relatos sem predicoes_v35
CORTE_LITERAL = json.load(open(RAIZ / 'aluno' / 'limiar_portao_v36.json'))['p_literal']
PAL_SONHO = re.compile(r'\bsonh(?:o|os|ei)\b', re.I)
PAL_PESADELO = re.compile(r'\bpesadelos?\b', re.I)
MAX_TEXTO = 40000
FORMAS = ['post', 'comentario', 'continuacao', 'bluesky_nao_verificado']

# um bit por classe, na ordem; a página lê esta lista do meta.json
ROTULOS = [
    ('carga', 'prazerosa'), ('carga', 'aflitiva'), ('carga', 'estranha'),
    ('carga', 'sem_afeto_dito'), ('carga', 'mista'),
    ('despertar', 'alivio'), ('despertar', 'decepcao'), ('despertar', 'acordou_mal'),
    ('despertar', 'acordou_bem'), ('despertar', 'desorientado'), ('despertar', 'acordou_neutro'),
    ('figura', 'desejo'), ('figura', 'intensificador'), ('figura', 'votos'), ('figura', 'outra'),
    ('origem', 'nao_diz'), ('origem', 'a_si'), ('origem', 'entidade_religiosa'),
    ('origem', 'espirito_proprio'), ('origem', 'universo_destino'), ('origem', 'morto'),
    ('origem', 'outra'),
    ('conteudo', 'so_mencionado'),
]
BIT_ROT = {k: j for j, k in enumerate(ROTULOS)}
# o Opus usa figuras e origens que o aluno não tem: caem em 'outra'
FIGURA_OUTRA = {'metafora', 'escape', 'titulo_obra', 'comercial', 'homonimo', 'marca', 'toponimo'}
ORIGEM_OUTRA = {'outra_pessoa'}

# Taxa de acerto do palpite: quando o aluno diz X, quantas vezes X está certo
# na amostra-prova (300 sorteados, gabarito v3.5). PORTÃO: copiada de
# rubrica/medidas/resultado-do-aluno-v35.md ("Taxa de acerto do palpite, para a
# página", 27/09; portão do v3.5). CARGA, CONTEÚDO, DESPERTAR, FIGURA, TEM_ATRIB,
# ORIGEM: refeitas em 28/09 com o aluno v3.6 (aluno/avaliacao_v36.md/.json,
# precisão × marcados; limiar 0,5).
# (cabeça, classe): (taxa %, palpites na prova, faixa 95%, mostrar)
# Regra de "mostrar" (do relatório v3.5; reproduz todas as linhas antigas):
# faixa = intervalo de Wilson 95%; 'sim' com >=20 palpites e limite inferior da
# faixa > 60%; 'aviso' com >=10 palpites; 'nao' abaixo disso. Classes sem
# nenhum palpite na prova não têm linha.
# 'nao' = a página não mostra o palpite dessa classe (nem o usa em filtro).
TAXAS = {
    ('portao', 'literal'): (96, 196, '93–98', 'sim'),
    ('portao', 'figurado'): (96, 95, '90–98', 'sim'),
    ('portao', 'fala_do_sonhar'): (47, 15, '25–70', 'aviso'),
    ('portao', 'noticia'): (0, 2, '0–66', 'nao'),
    ('portao', 'propaganda'): (100, 1, '21–100', 'nao'),
    ('portao', 'descartavel'): (100, 1, '21–100', 'nao'),
    # carga, conteúdo, despertar, tem_atrib, origem: afeto v2 (aluno/taxas_afeto_v2.json,
    # 28/09 noite); origem 'outra' forçada 'nao' (15%). Figura: v3.6.
    ('carga', 'prazerosa'): (42, 19, '23–64', 'aviso'),
    ('carga', 'aflitiva'): (80, 20, '58–92', 'aviso'),
    ('carga', 'mista'): (33, 3, '6–79', 'nao'),
    ('carga', 'estranha'): (50, 10, '24–76', 'aviso'),
    ('carga', 'sem_afeto_dito'): (97, 143, '92–98', 'sim'),
    ('conteudo', 'narrado'): (99, 180, '97–100', 'sim'),
    ('conteudo', 'so_mencionado'): (75, 12, '47–91', 'aviso'),
    ('despertar', 'decepcao'): (12, 8, '2–47', 'nao'),
    ('despertar', 'acordou_mal'): (83, 6, '44–97', 'nao'),
    ('despertar', 'acordou_bem'): (40, 5, '12–77', 'nao'),
    ('despertar', 'desorientado'): (83, 6, '44–97', 'nao'),
    ('despertar', 'acordou_neutro'): (80, 5, '38–96', 'nao'),
    ('figura', 'desejo'): (95, 74, '87–98', 'sim'),
    ('figura', 'intensificador'): (69, 26, '50–83', 'aviso'),
    ('figura', 'outra'): (100, 1, '21–100', 'nao'),
    ('tem_atrib', 'tem_atrib'): (93, 15, '70–99', 'aviso'),
    ('origem', 'nao_diz'): (90, 10, '60–98', 'aviso'),
    ('origem', 'a_si'): (73, 11, '43–90', 'aviso'),
    ('origem', 'entidade_religiosa'): (100, 1, '21–100', 'nao'),
    ('origem', 'espirito_proprio'): (100, 2, '34–100', 'nao'),
    ('origem', 'universo_destino'): (100, 1, '21–100', 'nao'),
    ('origem', 'morto'): (0, 1, '0–79', 'nao'),
    ('origem', 'outra'): (15, 13, '4–42', 'nao'),
}
mostra = lambda cab, cl: TAXAS.get((cab, cl), (0, 0, '', 'nao'))[3] != 'nao'

STOP = set("""a o e de da do das dos em um uma que com para por nao não mais eu me minha meu se
ela ele isso essa esse sua seu você vc ja já como mas ou foi era ser ter tem tinha muito muita
quando sempre pra pro também depois até anos ano dia hoje ontem noite the a an and of to in that
i my was it is for with me on had this at as be are you we he she they them his her so but not
have has sonho sonhos sonhei sonhar sonhando dream dreams dreamt dreaming pesadelo nightmare
tudo nada aqui ali onde nunca antes agora ainda vez vezes outra outro dela dele meus minhas
seus suas tenho tinha tive sinto acho sei fazer faz vou estou está sou era são foi fui
dont im ive really just like then there when out up all one about what would could should
gente coisa coisas vida pessoa pessoas tempo casa pq porque então""".split())


def normalizar(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def palavras(texto):
    for w in re.findall(r"[a-zà-ú']{4,}", normalizar(texto)):
        if w not in STOP:
            yield w


FRAGMENTOS = 256        # gavetas do índice de busca


def escrever_indice_busca(textos):
    """Índice invertido sobre o texto INTEIRO, partido em 256 gavetas (ver V2)."""
    def fatiar(texto):
        return set(re.findall(r"[a-zà-ú']{3,}", normalizar(texto)))

    df = Counter()
    conjuntos = []
    for t in textos:
        ps = fatiar(t)
        conjuntos.append(ps)
        df.update(ps)
    teto = max(50, len(textos) // 4)
    lexico = sorted(w for w, n in df.items() if 3 <= n <= teto)
    ondeW = {w: i for i, w in enumerate(lexico)}

    gavetas = [dict() for _ in range(FRAGMENTOS)]
    for d, ps in enumerate(conjuntos):
        for w in ps:
            j = ondeW.get(w)
            if j is not None:
                gavetas[j % FRAGMENTOS].setdefault(j, []).append(d)

    pasta = SAIDA / 'busca'
    pasta.mkdir(exist_ok=True)
    for antigo in pasta.glob('*.json'):
        antigo.unlink()
    total = 0
    for g, gaveta in enumerate(gavetas):
        saida = {}
        for j, docs in gaveta.items():
            total += len(docs)
            ant, deltas = 0, []
            for d in docs:
                deltas.append(d - ant)
                ant = d
            saida[str(j)] = deltas
        json.dump(saida, open(pasta / f'{g}.json', 'w'), separators=(',', ':'))
    json.dump(lexico, open(pasta / 'lexico.json', 'w'), ensure_ascii=False,
              separators=(',', ':'))
    mb = sum(p.stat().st_size for p in pasta.glob('*.json')) / 1e6
    print(f'índice de busca: {len(lexico)} palavras · {total} ocorrências · {mb:.1f}MB')


def jsonl(caminho):
    for l in open(caminho):
        if l.strip():
            yield json.loads(l)


def ids_de_cuidado(con):
    """Todo id com bandeira, POR ID (a V2 mapeava pelo texto e perdia os que
    não casavam). Fontes: as mesmas do arquivo/atualizar_cuidado.py, mais a
    anotação v3.5 em subpastas, mais — por precaução — o que o aluno (v3.5; v3.6 onde não há v3.5)
    marcou com bandeira e ninguém conferiu como falso.
    Devolve (ids, relatório por fonte)."""
    ids, fonte = set(), Counter()

    def pega(i, de):
        if i not in ids:
            fonte[de] += 1
        ids.add(i)

    for (i,) in con.execute("""SELECT relato_id FROM anotacoes_v3 WHERE anotador LIKE 'claude:sab%'
                               AND json_extract(extra,'$.bandeira')=1"""):
        pega(i, 'anotações sab')
    conferido_falso = set()
    for f in (glob.glob(str(LOTES / 'risco_conferidos*.jsonl'))
              + glob.glob(str(LOTES / 'risco_v351' / '*_conferido*.jsonl'))):
        for x in jsonl(f):
            if x.get('bandeira') is True:
                pega(x['id'], 'conferência de risco')
            elif x.get('bandeira') is False:
                conferido_falso.add(x['id'])
    manual = LOTES / 'cuidado_manual.jsonl'
    if manual.exists():
        for x in jsonl(manual):
            pega(x['id'], 'cuidado manual')
    # o atualizar_cuidado.py só olhava um nível (v3*/*); a v3.5 tem subpastas
    for f in glob.glob(str(LOTES / 'v3*' / '**' / '*_anotado*.jsonl'), recursive=True):
        for x in jsonl(f):
            if 'bandeira' in (x.get('marcas') or []):
                pega(x['id'], 'anotação v3.x')
    for x in jsonl(LOTES / 'v35' / 'final_v35.jsonl'):
        if 'bandeira' in (x.get('marcas') or []):
            pega(x['id'], 'anotação v3.x')
    # anotações Sonnet de 28/09 (afeto sorteado e classes raras)
    for f in (glob.glob(str(LOTES / 'afeto15k' / '*_anotado.jsonl'))
              + glob.glob(str(LOTES / 'raros_enxuto' / '*_anotado.jsonl'))):
        for x in jsonl(f):
            if 'bandeira' in (x.get('marcas') or []):
                pega(x['id'], 'anotação Sonnet 28/09')
    # o aluno marca muito desabafo depressivo sem plano; mas até a regra fechar,
    # o que ele marcou e ninguém leu fica de fora
    # a bandeira é do v3.5; onde o v3.5 não tem linha (~3,7 mil ids novos), a do v3.6
    for (i,) in con.execute("""SELECT relato_id FROM predicoes_v35 WHERE bandeira = 1
            UNION SELECT relato_id FROM predicoes_v36 WHERE bandeira = 1
              AND relato_id NOT IN (SELECT relato_id FROM predicoes_v35)"""):
        if i in ids:
            continue
        if i not in conferido_falso:
            pega(i, 'palpite do aluno, não conferido')
    return ids, fonte, conferido_falso


def ids_sensiveis():
    """Decisão do Fitipe (28/09): a bandeira tem dois níveis. Risco real
    (ideação presente, ameaça a pessoa concreta, menor) → fora da página, como
    sempre. ENDOSSO da vigília a uma violência SONHADA ("sonhei que bati na ex,
    acordei leve"), sem alvo em perigo → fica na página com a etiqueta
    "conteúdo sensível", sem número (o aluno não aprende bandeira; a única
    fonte é a leitura). Marca `endosso_violencia` nas anotações."""
    ids = set()
    for f in (glob.glob(str(LOTES / '**' / '*_anotado*.jsonl'), recursive=True)
              + [str(LOTES / 'v35' / 'final_v35.jsonl')]):
        for x in jsonl(f):
            if 'endosso_violencia' in (x.get('marcas') or []):
                ids.add(x['id'])
    return ids


def carregar_lidos():
    """Os ~3.800 lidos de verdade: Opus (rubrica v3.5.1) e o Fitipe (revisão
    cega). Onde os dois leram, o Fitipe tem precedência campo a campo."""
    opus = {}
    for f in ['v35/final_v35.jsonl', 'v35/prova_1_anotado.jsonl', 'v35/prova_2_anotado.jsonl']:
        for x in jsonl(LOTES / f):
            opus[x['id']] = x
    fitipe = {x['id']: x for x in jsonl(LOTES / 'revisao_cega_respostas_fitipe.jsonl')}
    lidos = {}
    for i, x in opus.items():
        atrib = []
        pal = x.get('atribuicao_palavra') or []
        for k, p in enumerate(pal):
            g = lambda c: ((x.get(c) or []) + [None] * len(pal))[k]
            atrib.append([p.strip('"“”'), g('atribuicao_origem'), g('atribuicao_postura'),
                          g('atribuicao_quem')])
        lidos[i] = {'por': 'opus', 'portao': x.get('portao') or [],
                    'carga': x.get('carga') or [], 'conteudo': x.get('conteudo'),
                    'despertar': x.get('despertar') or [], 'figura': x.get('figura') or [],
                    'atrib': atrib}
    for i, x in fitipe.items():
        d = lidos.get(i, {'portao': [], 'carga': [], 'conteudo': None, 'despertar': [],
                          'figura': [], 'atrib': []})
        d['por'] = 'fitipe' if 'por' not in d else 'fitipe+opus'
        # no vocabulário dele, portão vazio = sonho dormido (literal);
        # 'meta' é o nome antigo de fala do sonhar
        p = set(x.get('portao') or [])
        if 'nao_dormido' not in p:
            d['portao'] = ['literal']
        else:
            d['portao'] = ([c for c in ('figurado',) if c in p]
                           + (['fala_do_sonhar'] if 'meta' in p else [])) or ['nao_dormido']
        d['carga'] = x.get('carga') or []
        d['despertar'] = [c for c in (x.get('despertar') or []) if c != 'nada']
        lidos[i] = d
    return lidos, len(opus), len(fitipe)


# ——— VÍNCULOS (28/09): o que liga um relato a outros ———
# Pedido do Fitipe (25/09): tags clicáveis na ficha que revelam os iguais como
# se fosse busca — "circulação (N)" (letra/meme que rodou entre contas por
# meses), "idêntico (N)" (frase comum ou copy-paste entre contas), "quase
# idêntico (N)" (ecos fortes entre contas, régua por embedding), "repetido N×
# pela mesma conta" (as cópias escondidas por canonico_de, com as datas); e a
# conversa em torno do post (tabela vinculos): quem responde a quem.
# Mais as DUAS DATAS do Bluesky (tuítes importados na migração do X): a data
# declarada é a do post original, o rkey do Bluesky diz quando chegou lá.
TID = '234567abcdefghijklmnopqrstuvwxyz'


def data_do_rkey(uri):
    """Data de criação real de um post do Bluesky, pelo rkey (TID) no fim da URI."""
    r = (uri or '').rsplit('/', 1)[-1]
    if len(r) != 13 or any(ch not in TID for ch in r):
        return None
    v = 0
    for ch in r:
        v = v * 32 + TID.index(ch)
    from datetime import datetime, timezone
    return datetime.fromtimestamp((v >> 10) / 1e6, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def escrever_vinculos(con, na_pagina):
    """na_pagina: id → índice do ponto. Escreve dados/vinculos.json (esparso)."""
    V = {'copias': {}, 'grupos': {}, 'quase': {}, 'repetido': {}, 'pai': {}, 'filhos': {}, 'datas2': {}}
    TIPO = {'frase_comum': 0, 'copy_paste': 1, 'circulacao': 2}
    # cópias: grupos de texto normalizado idêntico entre contas diferentes
    grupos = {}
    for (rid, g, tipo) in con.execute('SELECT relato_id, grupo, tipo FROM grupos_copia'):
        if rid in na_pagina:
            grupos.setdefault((tipo, g), []).append(na_pagina[rid])
    for (tipo, g), idxs in grupos.items():
        if len(idxs) < 2:
            continue
        gid = f'{TIPO[tipo]}:{g}'
        V['grupos'][gid] = sorted(idxs)
        for i in idxs:
            V['copias'][i] = gid
    # quase idêntico: ecos fortes entre contas diferentes, vizinho a vizinho
    # (sem componente conexa: por encadeamento viraria um megagrupo)
    for (a, b) in con.execute("SELECT a, b FROM ecos WHERE tipo='eco_forte' AND mesmo_autor=0"):
        if a in na_pagina and b in na_pagina:
            ia, ib = na_pagina[a], na_pagina[b]
            V['quase'].setdefault(ia, []).append(ib)
            V['quase'].setdefault(ib, []).append(ia)
    # repetido pela mesma conta: as cópias apontam para o canônico (escondidas)
    for (c, data) in con.execute(
            'SELECT canonico_de, data_relato FROM relatos WHERE canonico_de IS NOT NULL'):
        if c in na_pagina:
            V['repetido'].setdefault(na_pagina[c], []).append((data or '')[:10])
    for i in V['repetido']:
        V['repetido'][i].sort()
    # conversa: comentário → post pai (quando o pai está no arquivo e na página)
    for (rid, pai) in con.execute(
            'SELECT relato_id, pai_relato_id FROM vinculos WHERE pai_relato_id IS NOT NULL'):
        if rid in na_pagina and pai in na_pagina and rid != pai:
            V['pai'][na_pagina[rid]] = na_pagina[pai]
            V['filhos'].setdefault(na_pagina[pai], []).append(na_pagina[rid])
    # duas datas do Bluesky: declarada × criação real (rkey), quando diferem > 1 dia
    from datetime import datetime
    for (rid, uri, data) in con.execute(
            "SELECT id, interno_id_original, data_relato FROM relatos WHERE fonte='bluesky'"):
        if rid not in na_pagina:
            continue
        real = data_do_rkey(uri)
        if not real:
            continue
        if not data:
            V['datas2'][na_pagina[rid]] = [None, real]
            continue
        try:
            dif = abs((datetime.fromisoformat(real[:19]) - datetime.fromisoformat(data[:19])).days)
        except ValueError:
            continue
        if dif > 1:
            V['datas2'][na_pagina[rid]] = [data, real]
    tam = Counter(len(v) for v in V['quase'].values())
    print(f"vínculos: cópias {len(V['copias'])} em {len(V['grupos'])} grupos · "
          f"quase idênticos {len(V['quase'])} relatos (máx. {max(tam) if tam else 0} vizinhos) · "
          f"repetidos {len(V['repetido'])} · conversa {len(V['pai'])} respostas / "
          f"{len(V['filhos'])} pais · duas datas {len(V['datas2'])}")
    json.dump(V, open(SAIDA / 'vinculos.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    return V


def main():
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=300)
    con.execute('PRAGMA busy_timeout=300000')

    cuidado, por_fonte, conferido_falso = ids_de_cuidado(con)
    print(f'cuidado: {len(cuidado)} ids com bandeira · ' +
          ' · '.join(f'{k} {v}' for k, v in por_fonte.items()))

    proj = np.load(SAIDA / 'projecao.npy')
    pids = [i for i in open(SAIDA / 'projecao_ids.txt').read().split('\n') if i]
    onde = {i: k for k, i in enumerate(pids)}
    print(f'projeção: {len(pids)} pontos')

    print('lendo o arquivo…')
    linhas = con.execute("""
        SELECT r.id, r.texto, r.fonte, r.comunidade, r.data_relato, r.forma,
               a.portao, a.p_literal, a.p_figurado,
               b.portao, b.p_literal, b.p_figurado,
               COALESCE(c.p_carga, b.p_carga), COALESCE(c.p_conteudo, b.p_conteudo),
               COALESCE(c.p_despertar, b.p_despertar),
               b.p_figura, COALESCE(c.p_tem_atrib, b.p_tem_atrib), COALESCE(c.p_origem, b.p_origem),
               EXISTS (SELECT 1 FROM revisao v WHERE v.relato_id = r.id
                       AND v.motivo = 'enorme' AND v.resolvido_em IS NULL)
        FROM relatos r JOIN predicoes_v36 b ON b.relato_id = r.id
             LEFT JOIN predicoes_v35 a ON a.relato_id = r.id
             LEFT JOIN predicoes_afeto_v2 c ON c.relato_id = r.id
        WHERE r.embedding IS NOT NULL AND r.canonico_de IS NULL
        ORDER BY r.data_relato, r.id""").fetchall()
    linhas = [l for l in linhas if l[0] in onde]
    print(f'{len(linhas)} relatos com predição, embedding e projeção '
          f'(sem v3.5: {sum(1 for l in linhas if l[6] is None)}, portão pelo v3.6)')

    # ——— o cuidado alcança as cópias: por id canônico e por texto idêntico ———
    # Repost da mesma pessoa aponta para o canônico (canonico_de); se a
    # bandeira caiu na cópia, o texto publicado é o do canônico.
    extra = set()
    for (i, c) in con.execute('SELECT id, canonico_de FROM relatos WHERE canonico_de IS NOT NULL'):
        if i in cuidado and c not in cuidado:
            extra.add(c)
        if c in cuidado and i not in cuidado:
            extra.add(i)
    textos_cuidado = {t for (t,) in con.execute(
        f"SELECT texto FROM relatos WHERE id IN ({','.join('?' * len(cuidado))})", list(cuidado))}
    por_texto = {l[0] for l in linhas if l[1] in textos_cuidado and l[0] not in cuidado}
    print(f'cuidado estendido: +{len(extra)} por cópia canônica · +{len(por_texto)} por texto idêntico')
    fora = cuidado | extra | por_texto
    antes = len(linhas)
    linhas = [l for l in linhas if l[0] not in fora]
    saiu = antes - len(linhas)
    print(f'saíram da página por cuidado: {saiu} (de {antes})')

    lidos, n_opus, n_fitipe = carregar_lidos()
    # lido numa cópia vale para o canônico que está na página
    canon = dict(con.execute('SELECT id, canonico_de FROM relatos WHERE canonico_de IS NOT NULL'))
    for i in list(lidos):
        if i in canon and canon[i] not in lidos:
            lidos[canon[i]] = lidos[i]

    esfera = proj[[onde[l[0]] for l in linhas]].astype('float32')
    na_pagina = {l[0]: i for i, l in enumerate(linhas)}
    V = escrever_vinculos(con, na_pagina)
    sens = sorted(na_pagina[i] for i in ids_sensiveis() if i in na_pagina)
    json.dump(sens, open(SAIDA / 'sensivel.json', 'w'))
    print(f'conteúdo sensível (endosso de violência sonhada, fica na página com etiqueta): {len(sens)}')

    FONTES, COMUNIDADES = {}, {}
    registros, textos, quandos, pcs = [], [], [], {}
    lidos_pub = []
    conta_palavra = Counter()
    docs_palavras = []
    conta = Counter()

    for i, l in enumerate(linhas):
        (_id, texto, fonte, com, data, forma, portao, p_lit, p_fig,
         portao36, p_lit36, p_fig36, p_carga, p_conteudo, p_despertar, p_figura,
         p_tem_atrib, p_origem, enorme) = l
        texto = texto or ''
        dec = lambda v: json.loads(v) if v else []
        lido = lidos.get(_id)
        if portao is None:
            # sem v3.5: portão do v3.6, com o corte de literal calibrado
            portao_al = set(dec(portao36)) - {'literal'}
            if p_lit36 > CORTE_LITERAL:
                portao_al.add('literal')
            p_lit, p_fig = p_lit36, p_fig36
            conta['portao_v36_sem_v35'] += 1
        else:
            portao_al = set(dec(portao))
        camada = 3 if portao_al & {'propaganda', 'descartavel'} else 0
        rot = 0
        if lido:
            por = 2 if lido['por'].startswith('fitipe') else 1
            pt = set(lido['portao'])
            # o lido manda também na camada: o Opus leu e disse que é sonho
            camada = 3 if pt & {'propaganda', 'descartavel'} else 0
            lit, fig = 'literal' in pt, 'figurado' in pt
            fala = 'fala_do_sonhar' in pt
            narr = lido['conteudo'] == 'narrado'
            atr = bool(lido['atrib'])
            for c in lido['carga']:
                rot |= 1 << BIT_ROT[('carga', c)] if ('carga', c) in BIT_ROT else 0
            for c in lido['despertar']:
                rot |= 1 << BIT_ROT[('despertar', c)] if ('despertar', c) in BIT_ROT else 0
            for c in lido['figura']:
                c = 'outra' if c in FIGURA_OUTRA else c
                rot |= 1 << BIT_ROT[('figura', c)] if ('figura', c) in BIT_ROT else 0
            for a in lido['atrib']:
                c = 'outra' if a[1] in ORIGEM_OUTRA else a[1]
                if ('origem', c) in BIT_ROT:
                    rot |= 1 << BIT_ROT[('origem', c)]
            if lido['conteudo'] == 'so_mencionado':
                rot |= 1 << BIT_ROT[('conteudo', 'so_mencionado')]
            lidos_pub.append([i, lido])
            conta['lido_' + ('fitipe' if por == 2 else 'opus')] += 1
        else:
            por = 0
            lit = 'literal' in portao_al
            fig = 'figurado' in portao_al
            fala = 'fala_do_sonhar' in portao_al        # 'aviso': 47%
            # cabeças do v3.6, decididas com o limiar 0,5 (o mesmo do inferir_v36
            # e da avaliação) e abertas pelo portão DA PÁGINA (v3.5), não pelo do v3.6
            lst = lambda pj: [n for n, x in json.loads(pj).items() if x > 0.5]
            pcont = json.loads(p_conteudo)
            conteudo = max(pcont, key=pcont.get) if lit else None
            narr = conteudo == 'narrado'
            atr = (lit or fala) and p_tem_atrib > 0.5
            if conteudo == 'so_mencionado' and mostra('conteudo', 'so_mencionado'):
                rot |= 1 << BIT_ROT[('conteudo', 'so_mencionado')]
            carga = lst(p_carga) if lit else []
            despertar = lst(p_despertar) if lit else []
            figura = lst(p_figura) if fig else []
            origem = lst(p_origem) if atr else []
            mostradas = []
            for cab, v in (('carga', carga), ('despertar', despertar), ('figura', figura),
                           ('origem', origem)):
                for c in v:
                    if mostra(cab, c) and (cab, c) in BIT_ROT:
                        rot |= 1 << BIT_ROT[(cab, c)]
                        if cab == 'carga':
                            mostradas.append(c)
            # carga combinada: a proporção entre as cargas que o aluno afirma,
            # tirada das probabilidades dele — "aflitiva 60% + estranha 40%"
            if len(mostradas) > 1 and p_carga:
                pc = json.loads(p_carga)
                s = sum(pc[c] for c in mostradas) or 1
                pcs[i] = [[c, round(100 * pc[c] / s)] for c in mostradas]
        f = FONTES.setdefault(fonte or '?', len(FONTES))
        c = COMUNIDADES.setdefault(com or '?', len(COMUNIDADES))
        # Linha do tempo pela data DECLARADA (decisão do Fitipe: é quando foi
        # sonhado). Tuítes importados no Bluesky trazem datas anteriores a 2015 —
        # antes eram grampeadas em 2015/01; agora entram no ano delas. Post do
        # Bluesky sem data no coletor usa a data de criação real (rkey).
        if not data and i in V['datas2']:
            data = V['datas2'][i][1]
        ano = int(data[:4]) if data else 2015
        mes = int(data[5:7]) if data and len(data) > 6 else 1
        grampeado = ano < 2008 or ano > 2026
        if ano < 2008: ano, mes = 2008, 1
        if ano > 2026: ano, mes = 2026, 12
        bits = lit | (fig << 1) | ((not lit and not fig) << 2)
        n = len(texto)
        tam = 3 if enorme else (0 if n < CURTO else (1 if n <= LONGO else 2))
        bits |= 1 << (3 + tam)
        bits |= (bool(PAL_SONHO.search(texto)) << 7) | (bool(PAL_PESADELO.search(texto)) << 8)
        fm = FORMAS.index(forma) if forma in FORMAS else 0
        bits |= (fala << 9) | (fm << 10) | (por << 12) | (narr << 14) | (atr << 15)
        conta['forma_' + FORMAS[fm]] += 1
        registros.append((esfera[i], camada, f, c, ano, mes, bits,
                          round(100 * (p_lit or 0)), round(100 * (p_fig or 0)), rot))
        textos.append(texto[:MAX_TEXTO])
        quandos.append('' if grampeado else (data or ''))
        ps = set(palavras(texto[:600]))
        docs_palavras.append(ps)
        conta_palavra.update(ps)
        if i % 50000 == 0 and i:
            print(f'  {i}…')

    vocab = [w for w, n in conta_palavra.items() if 12 <= n <= len(linhas) // 25]
    idx_vocab = {w: i for i, w in enumerate(vocab)}
    print(f'vocabulário distintivo: {len(vocab)} palavras')

    with open(SAIDA / 'pontos.bin', 'wb') as f:
        f.write(struct.pack('<I', len(registros)))
        for (pos, nat, fo, co, ano, mes, bits, pl, pf, rot) in registros:
            f.write(struct.pack('<3f', *[float(v) for v in pos]))
            f.write(struct.pack('<BBBHBHBBI', nat, fo, co, ano, mes, bits, pl, pf, rot))
        for ps in docs_palavras:
            pp = [i for _, i in sorted((conta_palavra[w], idx_vocab[w])
                                       for w in ps if w in idx_vocab)[:3]]
            f.write(struct.pack('<B', len(pp)))
            for k in pp:
                f.write(struct.pack('<I', k))

    escrever_indice_busca(textos)

    POR_ARQ = 8000
    n_arq = 0
    for antigo in SAIDA.glob('textos*.json'):
        antigo.unlink()
    for i0 in range(0, len(textos), POR_ARQ):
        bloco = {'i0': i0, 'textos': textos[i0:i0 + POR_ARQ],
                 'quando': quandos[i0:i0 + POR_ARQ]}
        # proporção das cargas combinadas, só onde há mais de uma (esparso)
        pc = {str(k - i0): v for k, v in pcs.items() if i0 <= k < i0 + POR_ARQ}
        if pc:
            bloco['cargas'] = pc
        json.dump(bloco, open(SAIDA / f'textos{n_arq}.json', 'w'), ensure_ascii=False)
        n_arq += 1

    # os lidos vão num arquivo à parte, pequeno, carregado com a página: a
    # atribuição (palavra, origem, quem) só existe neles e vira filtro
    json.dump([[i, {k: v for k, v in d.items() if v not in (None, [], '')}]
               for i, d in lidos_pub],
              open(SAIDA / 'lidos.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    # a V2 escondia pela página; aqui não há o que esconder. Vazio fica para
    # o caso de o Fitipe querer tirar algo à mão sem regerar tudo.
    json.dump([], open(SAIDA / 'cuidado.json', 'w'))

    json.dump({
        'n': len(registros),
        'fontes': [k for k, _ in sorted(FONTES.items(), key=lambda x: x[1])],
        'comunidades': [k for k, _ in sorted(COMUNIDADES.items(), key=lambda x: x[1])],
        'qualidades': QUALIDADES,
        'formas': FORMAS,
        'rotulos': [list(k) for k in ROTULOS],
        'taxas': {f'{a}:{b}': list(v) for (a, b), v in TAXAS.items()},
        'vocab': vocab,
        'ano_min': min(r[4] for r in registros), 'ano_max': max(r[4] for r in registros),
        'arquivos_texto': n_arq, 'por_arquivo': POR_ARQ,
        'guardados_por_cuidado': saiu,
    }, open(SAIDA / 'meta.json', 'w'), ensure_ascii=False)

    mb = lambda p: (SAIDA / p).stat().st_size / 1e6
    print(f"\npontos.bin {mb('pontos.bin'):.1f}MB · {n_arq} blocos de texto · "
          f"lidos.json {mb('lidos.json'):.2f}MB")
    print(f"pontos {len(registros)} · lidos {len(lidos_pub)} (de {n_opus} Opus + {n_fitipe} Fitipe) · "
          f"palpites {len(registros) - len(lidos_pub)} · fora por cuidado {saiu}")
    print(dict(conta))
    print(f"cargas combinadas com proporção: {len(pcs)}")
    json.dump({'pontos': len(registros), 'lidos': len(lidos_pub),
               'lidos_opus': conta['lido_opus'], 'lidos_fitipe': conta['lido_fitipe'],
               'palpites': len(registros) - len(lidos_pub), 'fora_por_cuidado': saiu,
               'cuidado_ids': len(cuidado), 'cuidado_por_fonte': dict(por_fonte),
               'cuidado_extra_copia': len(extra), 'cuidado_extra_texto': len(por_texto),
               'formas': {k: v for k, v in conta.items() if k.startswith('forma_')}},
              open(AQUI / 'numeros.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
