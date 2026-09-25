#!/usr/bin/env python3
"""A RÉGUA DE SIMILARIDADE — ecos e duplicatas, sem fundir sonhos parecidos.

Princípio (Fitipe, 2026-09-20): duas pessoas sonhando quase a mesma coisa é O ACHADO,
não ruído. Só é duplicata quando há evidência de ser a MESMA pessoa repetindo.

  ≥0,97 + mesmo autor + ≤90 dias        → duplicata   (marca canonico_de)
  ≥0,90 + mesmo autor + ≤7 dias         → duplicata   (a pessoa repostando o
                                          próprio texto com outro título, horas
                                          depois: "Desabafo da minha vida" e
                                          "Textão sobre minha vida", mesmo corpo.
                                          Sonho recorrente não some por isso —
                                          ele já é uma QUALIDADE do relato único.)
  MESMA URL                             → duplicata   (certeza, não semelhança:
                                          é o mesmo post gravado duas vezes. O
                                          piloto entrou com id de 10 caracteres
                                          e o moinho recolheu os mesmos posts
                                          depois, com id novo. Fica o do moinho,
                                          que tem autor e passou pelo pipeline.)
  texto IDÊNTICO + ≥200 chars +
  contas ≠ + ≤1 hora                    → duplicata   (a mesma redação em duas
                                          contas suas — o Jornal GGN e o perfil
                                          do dono, 21 segundos de intervalo.
                                          O PISO DE 200 CARACTERES é o que
                                          protege o achado (aviso do Fitipe):
                                          abaixo dele, gente diferente escreve
                                          igual de verdade — três pessoas
                                          postaram "sonhei q o twitter voltava"
                                          com minutos de diferença na mesma
                                          noite, e isso é o ouro, não o lixo.)
  ≥0,995 + mesmo autor, sem janela      → duplicata   (verbatim da mesma conta é
                                          repost, tenha passado quanto tempo for)
  ≥0,97 + autores diferentes            → eco_forte   (liga, não funde. Se forem
                                          três ou mais cópias, `copias.py` ainda
                                          as agrupa como copy-paste ou obra —
                                          e não esconde nenhuma, porque 24
                                          pessoas repostando é dado.)
  0,90–0,97                             → sonho_gemeo (liga — o material precioso)

Uso: python3 regua.py [--aplicar]   (sem --aplicar só relata)
"""
import hashlib
import sqlite3
import sys
import datetime
import re
import unicodedata
import numpy as np
from pathlib import Path

DB = Path(__file__).parent / 'arquivo.db'
APLICAR = '--aplicar' in sys.argv
# --min-chars N: só compara textos com pelo menos N caracteres (25/09: a régua
# por embedding explodiu com tuítes curtos; o curto vai para agrupamento exato)
MIN_CHARS = next((int(x.split('=')[1]) for x in sys.argv if x.startswith('--min-chars=')), 0)
LIM_GEMEO, LIM_FORTE, DIAS_DUP = 0.90, 0.97, 90
LIM_VERBATIM = 0.995   # praticamente letra por letra
MIN_REPOST = 60          # minutos: janela do repost institucional
DIAS_REPOST = 7          # dias: janela do repost da própria pessoa, com edição
TAM_REPOST = 200         # caracteres: abaixo disso, texto igual é coincidência real


def reconciliar_urls(con, aplicar):
    """Mesma URL = mesmo post. Certeza, não semelhança.

    O piloto gravou 491 relatos com id de 10 caracteres e sem autor; o moinho
    recolheu os mesmos posts depois, com id derivado do id do Reddit. Os dois
    ficaram no arquivo e viram dois pontos colados no planeta. Fica o do moinho,
    que tem o autor e passou pelo pipeline inteiro.
    """
    pares = con.execute("""
        SELECT velho.id, novo.id FROM relatos velho JOIN relatos novo
          ON novo.interno_url = velho.interno_url AND novo.id <> velho.id
        WHERE velho.interno_url IS NOT NULL AND velho.canonico_de IS NULL
          AND length(velho.id) < length(novo.id)""").fetchall()
    print(f'mesma URL gravada duas vezes: {len(pares)} pares')
    if aplicar and pares:
        con.executemany("UPDATE relatos SET canonico_de=? WHERE id=? AND canonico_de IS NULL",
                        [(novo, velho) for velho, novo in pares])
        con.commit()
    return len(pares)


def achatar_cadeias(con, passadas=6):
    """Repete até estabilizar: uma passagem só usa o mapa antigo e não converge."""
    for _ in range(passadas):
        if _achatar_uma_vez(con) == 0:
            return


def _achatar_uma_vez(con):
    """Todo duplicado aponta direto para o relato que sobrevive.

    Cadeias A→B→C faziam A e B sumirem e só C ficar — o conteúdo se preserva,
    mas quem lê `canonico_de` acha que A foi substituído por B, que também não
    existe. Aqui cada um passa a apontar para a raiz. Se restar ciclo, quebra-se
    pelo mais antigo, que é quem tem direito à data na linha do tempo.
    """
    pai = dict(con.execute("SELECT id, canonico_de FROM relatos WHERE canonico_de IS NOT NULL"))
    data = dict(con.execute("SELECT id, data_relato FROM relatos"))
    mudou, solta = [], set()
    for x in list(pai):
        visto, atual = {x}, pai[x]
        while atual in pai:
            if atual in visto:                       # ciclo: fica o mais antigo
                anel = list(visto)
                raiz = min(anel, key=lambda k: (data.get(k) or '9999'))
                # a raiz precisa SOLTAR a própria marca, senão continua apontando
                # de volta para dentro do anel e o ciclo nunca se desfaz
                solta.add(raiz)
                for m in anel:
                    if m != raiz:
                        mudou.append((raiz, m))
                atual = raiz
                break
            visto.add(atual)
            atual = pai[atual]
        if atual != pai[x]:
            mudou.append((atual, x))
    mudou = [(r, m) for r, m in mudou if r != m and m not in solta]
    if mudou or solta:
        con.executemany("UPDATE relatos SET canonico_de=? WHERE id=?", mudou)
        con.executemany("UPDATE relatos SET canonico_de=NULL WHERE id=?", [(r,) for r in solta])
        con.execute("UPDATE relatos SET canonico_de=NULL WHERE canonico_de=id")
        con.commit()
    print(f'cadeias achatadas: {len(mudou)} ajustes')
    return len(mudou) + len(solta)


def impressao(texto):
    """Assinatura do texto, insensível a acento, caixa e espaço."""
    s = unicodedata.normalize('NFD', (texto or '').lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return hashlib.blake2b(re.sub(r'\W+', ' ', s).strip().encode(), digest_size=8).digest()


def main():
    con = sqlite3.connect(DB, timeout=180)
    con.execute('PRAGMA busy_timeout=180000')
    reconciliar_urls(con, APLICAR)
    linhas = con.execute("""SELECT r.id, r.embedding, r.interno_autor_hash, r.data_relato,
               r.texto
        -- Todo relato com vetor, uma linha por relato (a chave de relatos). A
        -- versão anterior juntava com anotacoes 'ollama%' natureza='relato':
        -- os ~290 mil moídos pelo BERT (25/09) nunca seriam comparados, e o
        -- figurado — que a V2 do planeta mostra — também não.
        FROM relatos r
        WHERE r.embedding IS NOT NULL AND length(r.embedding) > 0
          AND length(r.texto) >= ?""", (MIN_CHARS,)).fetchall()
    if not linhas:
        print('nenhum relato com embedding ainda'); return
    ids = [l[0] for l in linhas]
    autores = [l[2] for l in linhas]
    datas = [datetime.datetime.fromisoformat((l[3] or '').replace('Z', ''))
             if l[3] else None for l in linhas]
    marcas = [impressao(l[4]) for l in linhas]    # guarda 8 bytes, não o texto
    tams = [len(l[4] or '') for l in linhas]
    X = np.stack([np.frombuffer(l[1], dtype='float32') for l in linhas]).astype('float32')
    del linhas
    norma = np.linalg.norm(X, axis=1, keepdims=True)
    validos = norma[:, 0] > 0          # descarta embeddings vazios
    X, norma = X[validos], norma[validos]
    ids = [i for i, v in zip(ids, validos) if v]
    autores = [a for a, v in zip(autores, validos) if v]
    datas = [d for d, v in zip(datas, validos) if v]
    marcas = [m for m, v in zip(marcas, validos) if v]
    tams = [t for t, v in zip(tams, validos) if v]
    X /= norma
    print(f'{len(ids)} relatos · comparando…')

    achados, B = [], 512
    for i0 in range(0, len(ids), B):
        S = X[i0:i0 + B] @ X.T
        for li, linha in enumerate(S):
            i = i0 + li
            linha[:i + 1] = -1                      # só metade superior
            for j in np.where(linha >= LIM_GEMEO)[0]:
                sim = float(linha[j])
                mesmo = int(bool(autores[i]) and autores[i] == autores[j])
                dias = (abs((datas[i] - datas[j]).days)
                        if datas[i] and datas[j] else None)
                minutos = (abs((datas[i] - datas[j]).total_seconds()) / 60
                           if datas[i] and datas[j] else None)
                # repost institucional: texto longo letra por letra igual, contas
                # diferentes, minutos de intervalo. O piso de tamanho é o que
                # separa isso de duas pessoas que sonharam e escreveram igual.
                repost = (marcas[i] == marcas[int(j)] and not mesmo
                          and min(tams[i], tams[int(j)]) >= TAM_REPOST
                          and minutos is not None and minutos <= MIN_REPOST)
                # verbatim da MESMA conta é repost, tenha passado quanto tempo
                # for: 15 pares escapavam só por estarem a mais de 90 dias de
                # distância. O que NÃO entra aqui é o verbatim entre contas
                # diferentes — isso é copy-paste, e some para `grupos_copia`,
                # onde nenhuma cópia é escondida (ver arquivo/copias.py).
                if sim >= LIM_VERBATIM and mesmo:
                    tipo = 'duplicata'
                elif sim >= LIM_FORTE and mesmo and dias is not None and dias <= DIAS_DUP:
                    tipo = 'duplicata'
                elif mesmo and dias is not None and dias <= DIAS_REPOST:
                    tipo = 'duplicata'
                elif repost:
                    tipo = 'duplicata'
                elif sim >= LIM_FORTE:
                    tipo = 'eco_forte'
                else:
                    tipo = 'sonho_gemeo'
                # o canônico é sempre o mais antigo: é dele a data que a linha do
                # tempo deve mostrar. Empate, fica o texto mais longo.
                a, b = i, int(j)
                if datas[a] and datas[b] and datas[b] < datas[a]: a, b = b, a
                elif datas[a] and datas[b] and datas[a] == datas[b] and tams[b] > tams[a]: a, b = b, a
                achados.append((ids[a], ids[b], sim, tipo, mesmo, dias))

    from collections import Counter
    c = Counter(a[3] for a in achados)
    print(f"duplicatas {c['duplicata']} · ecos fortes {c['eco_forte']} · sonhos gêmeos {c['sonho_gemeo']}")

    if not APLICAR:
        print('\n(sem --aplicar: nada gravado)  amostra de sonhos gêmeos:')
        for a in [x for x in achados if x[3] == 'sonho_gemeo'][:5]:
            t1 = con.execute('SELECT substr(replace(texto,char(10)," "),1,90) FROM relatos WHERE id=?', (a[0],)).fetchone()[0]
            t2 = con.execute('SELECT substr(replace(texto,char(10)," "),1,90) FROM relatos WHERE id=?', (a[1],)).fetchone()[0]
            print(f'\n  {a[2]:.3f} {"(mesmo autor)" if a[4] else ""}\n   A: {t1}\n   B: {t2}')
        return

    con.executemany("""INSERT OR REPLACE INTO ecos (a,b,similaridade,tipo,mesmo_autor,dias_entre)
                       VALUES (?,?,?,?,?,?)""", achados)

    # A régua RECALCULA tudo, então apaga as marcas antigas antes de escrever as
    # novas. Marcar por cima com "AND canonico_de IS NULL" preservava o veredito
    # de execuções passadas — e quando a regra de qual cópia é a canônica mudou,
    # nasceram 670 CICLOS (A aponta para B e B para A). Como o planeta só mostra
    # quem tem canonico_de nulo, nos ciclos os DOIS sumiam: o relato desaparecia
    # inteiro em vez de sobrar um.
    con.execute("UPDATE relatos SET canonico_de=NULL")
    for a, b, *_ , in [x for x in achados if x[3] == 'duplicata']:
        con.execute("UPDATE relatos SET canonico_de=? WHERE id=? AND canonico_de IS NULL", (a, b))
    con.commit()
    reconciliar_urls(con, True)      # de novo: as marcas de URL foram apagadas acima
    achatar_cadeias(con)
    print(f'{len(achados)} ligações gravadas em `ecos`')


if __name__ == '__main__':
    main()
