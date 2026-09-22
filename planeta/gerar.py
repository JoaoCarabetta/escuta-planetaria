#!/usr/bin/env python3
"""Gera os dados do planeta v1 — campo de densidade, não coleção de pontos.

Princípios (acordados 2026-09-20/22):
  - posição vem SÓ da semântica (embedding), nada mais significa
  - sem continentes fixos: os nomes emergem da vizinhança onde se olha
  - campo-base = relatos com sonho ou desejo; resto são camadas acendíveis
  - três resoluções: densidade → pontos → texto

Saída: planeta/dados/pontos.bin (posições+marcadores) e textos.json
"""
import json
import re
import sqlite3
import struct
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
SAIDA = AQUI / 'dados'
SAIDA.mkdir(exist_ok=True)

QUALIDADES = ['recorrente', 'lucido', 'premonitorio', 'visita_de_morto', 'paralisia', 'erotico']
MAX_TEXTO = 40000        # sem corte: no GitHub Pages nao ha o teto de 64MB do Artifacts
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
    """Índice invertido sobre o texto INTEIRO — busca de verdade.

    O `vocab` do meta.json guarda só as 3 palavras mais raras de cada relato:
    serve para batizar uma vizinhança, não para procurar. Quem digitava uma
    palavra comum recebia 'nenhum com essa palavra' sobre um arquivo que a
    continha centenas de vezes.

    O índice inteiro pesa dezenas de MB, então vai partido em gavetas: a página
    baixa a lista de palavras uma vez e, a cada busca, só as gavetas das
    palavras que casaram — algumas dezenas de KB.
    """
    # sem a lista de vazias: quem procura 'gente' ou 'casa' tem direito de achar.
    # O que é palavra de todo mundo o teto de frequência tira sozinho.
    def fatiar(texto):
        return set(re.findall(r"[a-zà-ú']{3,}", normalizar(texto)))

    df = Counter()
    conjuntos = []
    for t in textos:
        ps = fatiar(t)
        conjuntos.append(ps)
        df.update(ps)
    # ≥3 relatos corta o rastro de erros de digitação; ≤25% corta o que está em
    # toda parte e não localiza nada.
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
            ant, deltas = 0, []           # diferenças: números pequenos, JSON curto
            for d in docs:
                deltas.append(d - ant)
                ant = d
            saida[str(j)] = deltas
        json.dump(saida, open(pasta / f'{g}.json', 'w'), separators=(',', ':'))
    json.dump(lexico, open(pasta / 'lexico.json', 'w'), ensure_ascii=False,
              separators=(',', ':'))
    mb = sum(p.stat().st_size for p in pasta.glob('*.json')) / 1e6
    maior = max(p.stat().st_size for p in pasta.glob('[0-9]*.json')) / 1e3
    print(f'índice de busca: {len(lexico)} palavras · {total} ocorrências · '
          f'{mb:.1f}MB em {FRAGMENTOS} gavetas (maior {maior:.0f}KB)')


def main():
    con = sqlite3.connect(DB, timeout=300)
    con.execute('PRAGMA busy_timeout=300000')
    print('lendo o arquivo…')
    linhas = con.execute("""
        SELECT r.id, r.texto, r.fonte, r.comunidade, r.data_relato,
               a.natureza_texto, a.tem_sonho_dormido, a.tem_desejo, a.tem_sofrimento,
               a.qualidades, r.interno_url IS NOT NULL
        FROM relatos r JOIN anotacoes a ON a.id = (
            -- UMA anotação por relato. Sem isto, os 216 relatos que sobraram
            -- dos testes A/B entre modelos (gemma4, qwen 2b/4b/9b) viravam 2, 3
            -- ou 4 pontos na MESMA posição do planeta — e a régua chegava a
            -- comparar um relato com a própria cópia e marcá-lo como duplicata
            -- de si mesmo, fazendo-o sumir. Prefere o juiz de produção.
            SELECT a2.id FROM anotacoes a2
            WHERE a2.relato_id = r.id AND a2.versao = 'v2.1'
              AND a2.anotador LIKE 'ollama%'
            ORDER BY CASE WHEN a2.anotador = 'ollama:qwen3.5-9b' THEN 0 ELSE 1 END, a2.id
            LIMIT 1)
        WHERE r.embedding IS NOT NULL
          -- a mesma pessoa repostando entra uma vez só; duas pessoas sonhando
          -- a mesma coisa entram as duas — isso é o achado, não ruído
          AND r.canonico_de IS NULL
        ORDER BY r.data_relato""").fetchall()
    print(f'{len(linhas)} relatos com anotação e embedding')

    # A posição vem do projetar.py (UMAP em 3 eixos livres). O PCA que havia aqui
    # preservava 36% da semelhança semântica; a bola do UMAP preserva ~61%.
    # Rode `python3 projetar.py` quando entrarem relatos novos.
    if not (SAIDA / 'projecao.npy').exists():
        raise SystemExit('falta dados/projecao.npy — rode primeiro: python3 projetar.py')
    proj = np.load(SAIDA / 'projecao.npy')
    onde = {i: k for k, i in enumerate(open(SAIDA / 'projecao_ids.txt').read().split('\n')) if i}
    tem = [l[0] in onde for l in linhas]
    faltam = len(linhas) - sum(tem)
    linhas = [l for l, v in zip(linhas, tem) if v]
    esfera = proj[[onde[l[0]] for l in linhas]].astype('float32')
    print(f'{len(linhas)} pontos posicionados'
          + (f' · {faltam} sem projeção (rode projetar.py de novo)' if faltam else ''))

    # ————— empacota posições e marcadores em binário —————
    NAT = {'relato': 0, 'meta': 1, 'idiomatico': 2, 'ruido': 3}
    FONTES, COMUNIDADES = {}, {}
    registros, textos, quandos = [], [], []
    conta_palavra = Counter()
    docs_palavras = []

    for i, l in enumerate(linhas):
        (_id, texto, fonte, com, data, nat, sonho, desejo, sofr, quals, _u) = l
        qs = set(json.loads(quals or '[]'))
        f = FONTES.setdefault(fonte or '?', len(FONTES))
        c = COMUNIDADES.setdefault(com or '?', len(COMUNIDADES))
        # o Bluesky deixa forjar createdAt: datas fora da janela real são grampeadas
        ano = int((data or '2015')[:4]) if data else 2015
        mes = int((data or '2015-01')[5:7]) if data and len(data) > 6 else 1
        grampeado = ano < 2015 or ano > 2026
        if ano < 2015: ano, mes = 2015, 1
        if ano > 2026: ano, mes = 2026, 12
        bits = ((sonho or 0) | ((desejo or 0) << 1) | ((sofr or 0) << 2))
        for j, q in enumerate(QUALIDADES):
            bits |= (1 << (3 + j)) if q in qs else 0
        registros.append((esfera[i], NAT.get(nat, 0), f, c, ano, mes, bits))
        textos.append(texto[:MAX_TEXTO])
        # carimbo completo UTC, para a ficha mostrar hora, minuto e segundo.
        # Vazio quando a data foi grampeada: ali o ano do ponto é uma correção
        # nossa, e mostrar o carimbo forjado contradiria a linha do tempo.
        quandos.append('' if grampeado else (data or ''))
        ps = set(palavras(texto[:600]))
        docs_palavras.append(ps)
        conta_palavra.update(ps)
        if i % 20000 == 0 and i:
            print(f'  {i}…')

    # ————— palavras distintivas por ponto (base dos nomes emergentes) —————
    # guarda, por ponto, os índices das 3 palavras mais raras que ele contém:
    # a raridade global é o que torna uma palavra distintiva de uma vizinhança.
    vocab = [w for w, n in conta_palavra.items() if 12 <= n <= len(linhas) // 25]
    idx_vocab = {w: i for i, w in enumerate(vocab)}
    print(f'vocabulário distintivo: {len(vocab)} palavras')
    palavras_por_ponto = []
    for ps in docs_palavras:
        cand = sorted((conta_palavra[w], idx_vocab[w]) for w in ps if w in idx_vocab)[:3]
        palavras_por_ponto.append([i for _, i in cand])

    with open(SAIDA / 'pontos.bin', 'wb') as f:
        f.write(struct.pack('<I', len(registros)))
        for (pos, nat, fo, co, ano, mes, bits) in registros:
            f.write(struct.pack('<3f', *[float(v) for v in pos]))
            f.write(struct.pack('<BBBHBH', nat, fo, co, ano, mes, bits))
        for pp in palavras_por_ponto:
            f.write(struct.pack('<B', len(pp)))
            for i in pp:
                f.write(struct.pack('<I', i))

    escrever_indice_busca(textos)

    # blocos de tamanho fixo em número de itens: a página calcula qual buscar
    POR_ARQ = 8000
    n_arq = 0
    for i0 in range(0, len(textos), POR_ARQ):
        json.dump({'i0': i0, 'textos': textos[i0:i0 + POR_ARQ],
                   'quando': quandos[i0:i0 + POR_ARQ]},
                  open(SAIDA / f'textos{n_arq}.json', 'w'), ensure_ascii=False)
        n_arq += 1
    json.dump({
        'n': len(registros),
        'fontes': [k for k, _ in sorted(FONTES.items(), key=lambda x: x[1])],
        'comunidades': [k for k, _ in sorted(COMUNIDADES.items(), key=lambda x: x[1])],
        'qualidades': QUALIDADES,
        'vocab': vocab,
        'ano_min': min(r[4] for r in registros), 'ano_max': max(r[4] for r in registros),
        'arquivos_texto': n_arq, 'por_arquivo': POR_ARQ,
    }, open(SAIDA / 'meta.json', 'w'), ensure_ascii=False)

    mb = lambda p: (SAIDA / p).stat().st_size / 1e6
    maior = max(mb(f'textos{i}.json') for i in range(n_arq))
    print(f"\npontos.bin {mb('pontos.bin'):.1f}MB · {n_arq} blocos de texto "
          f"(maior: {maior:.1f}MB)")
    print(f"campo-base (relato c/ sonho ou desejo): "
          f"{sum(1 for r in registros if r[1]==0 and (r[6] & 3))}")


if __name__ == '__main__':
    main()
