#!/usr/bin/env python3
"""Conjuntos do aluno v3.6 — junta o final_v35 (v3.5) com duas fontes novas
anotadas pelo Sonnet, sem mexer em dados_v35.py nem no aluno v3.5.

  TREINO   final_v35 (via dados_v35.conjuntos, 90%) + afeto15k (8.000, menos
           a_27 — ver abaixo) + 90% do raros_enxuto (2.630, estratificado).
  VALIDAÇÃO 10% do final_v35 (dados_v35.conjuntos, semente 2015) — decide a
           época, como no v3.5. Não inclui as fontes novas.
  VALIDAÇÃO EXTRA (raros) 10% do raros_enxuto, estratificado por lote (e_1..e_9),
           semente 2015 — medida extra das classes raras; NÃO decide época.
  PROVA e CEGA: intocadas (dados_v35.prova_v35 / dados_v35.cega).

Fontes novas, só os 13 campos pedidos (rubrica v3.5.1): id, portao, carga,
conteudo, despertar, figura, atribuicao_palavra, atribuicao_origem,
atribuicao_postura, atribuicao_quem, marcas, confianca, nota. Os lotes que
vieram com os 20 campos da rubrica completa (a_*, e_1/e_2/e_8) têm os campos
extras ignorados aqui — só os 13 chegam a `rotulos_v35`.

`a_27_anotado.jsonl` (afeto15k) FICA DE FORA: 49 dos 190 textos `literal` têm
`carga: []` onde a nota do próprio anotador diz explicitamente "sem afeto
dito" / "não conta como afeto" (deveria ser `carga: ["sem_afeto_dito"]`); um id
do lote (`22a227eba9`) tem só 10 caracteres hex em vez dos 16 do blake2b —
sinal de saída truncada/malformada nesse lote específico. Os outros 39 lotes de
afeto15k e os 9 de raros_enxuto não mostram o padrão (conferido).

Mesmas regras de exclusão do dados_v35: ids proibidos (prova, revisão cega,
fitipe70), copy_paste, e impressão de texto repetida (inclusive contra os
textos da prova/cega e entre as duas fontes novas e o final_v35). Se um id das
fontes novas colidir com um id do final_v35, o final_v35 (Opus) prevalece — a
linha nova é descartada.

Valores fora do vocabulário da rubrica em `atribuicao_origem` (`dizem`,
`doutrina_literatura` — valores de `atribuicao_quem`, não de `atribuicao_origem`,
por engano do anotador) são tratados como o dados_v35 trata qualquer valor fora
da lista: `multi(..., mapa_outra=True)` joga em `outra`.
"""
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dados_v35 import (CABECAS, CARGA, CONTEUDO, DESPERTAR, FIGURA, M, ORIGEM,
                       PORTAO, SEMENTE, conectar, conjuntos, contar, ids_proibidos,
                       impressao, ler_jsonl, rotulos_v35, textos)

RAIZ = Path(__file__).parent.parent
AFETO15K = RAIZ / 'rubrica' / 'lotes' / 'afeto15k'
RAROS_ENXUTO = RAIZ / 'rubrica' / 'lotes' / 'raros_enxuto'

CAMPOS_13 = ['id', 'portao', 'carga', 'conteudo', 'despertar', 'figura',
             'atribuicao_palavra', 'atribuicao_origem', 'atribuicao_postura',
             'atribuicao_quem', 'marcas', 'confianca', 'nota']

LOTE_QUEBRADO = {'a_27_anotado'}   # ver docstring: carga incompleta, id truncado


def _numero(stem):
    # 'a_12_anotado' -> 12 · 'e_9_anotado' -> 9
    return int(stem.split('_')[1])


def _carrega_lote(pasta, prefixo):
    arqs = sorted(pasta.glob(f'{prefixo}_*_anotado.jsonl'), key=lambda p: _numero(p.stem))
    out = []
    for p in arqs:
        if p.stem in LOTE_QUEBRADO:
            continue
        for a in ler_jsonl(p):
            r13 = {k: a.get(k) for k in CAMPOS_13}
            out.append((p.stem, r13))
    return out, [p.stem for p in arqs if p.stem in LOTE_QUEBRADO]


def fontes_novas():
    """(itens_afeto, itens_raros, lotes_excluidos) — cada item é (lote, dict de 13 campos)."""
    afeto, exc_a = _carrega_lote(AFETO15K, 'a')
    raros, exc_r = _carrega_lote(RAROS_ENXUTO, 'e')
    return afeto, raros, exc_a + exc_r


def _linhas_de(con, itens, origem, proibidos, copia, ids_final, marcas_usadas, fora):
    """itens: [(lote, dict13)] → linhas rotuladas, célula a célula, dedupe por
    id proibido/copy_paste/colisão com final_v35/texto repetido. `marcas_usadas`
    e `fora` são compartilhados e mutados (acumula entre chamadas)."""
    ids = [a['id'] for _, a in itens]
    tx = textos(con, ids)
    linhas = []
    for lote, a in itens:
        i = a['id']
        if i in proibidos:
            fora['prova/cega/70'] += 1; continue
        if i in copia:
            fora['copy_paste'] += 1; continue
        if i in ids_final:
            fora['colide com final_v35 (Opus prevalece)'] += 1; continue
        if i not in tx:
            fora['sem texto no banco'] += 1; continue
        m = impressao(tx[i])
        if m in marcas_usadas:
            fora['texto repetido (entre fontes/prova)'] += 1; continue
        marcas_usadas.add(m)
        linhas.append(dict(id=i, texto=tx[i], bolsa=origem, lote=lote,
                           origem_rot=origem, **rotulos_v35(a)))
    return linhas


def _split_estratificado(linhas, frac=0.1, semente=SEMENTE):
    """10% por lote, semente fixa — para o raros_enxuto (e_1..e_9)."""
    por_lote = defaultdict(list)
    for r in linhas:
        por_lote[r['lote']].append(r)
    val, tr = [], []
    for lote in sorted(por_lote):
        L = list(por_lote[lote])
        rng = random.Random(semente)
        rng.shuffle(L)
        corte = max(1, round(len(L) * frac)) if L else 0
        val += L[:corte]
        tr += L[corte:]
    return tr, val


def conjuntos_v36(usar_v3=False, verbose=True):
    """→ (treino, validacao, validacao_raros_extra, relatorio)."""
    con = conectar()
    prova, cg, f70, copia = ids_proibidos(con)
    proibidos = prova | cg | f70
    final_v35 = ler_jsonl(RAIZ / 'rubrica' / 'lotes' / 'v35' / 'final_v35.jsonl')
    ids_final = {a['id'] for a in final_v35}

    tr35, val35 = conjuntos(usar_v3, verbose=verbose)
    marcas_prova = {impressao(t) for t in textos(con, proibidos).values()}
    marcas_usadas = {impressao(r['texto']) for r in tr35 + val35} | marcas_prova

    afeto_itens, raros_itens, lotes_excluidos = fontes_novas()

    fora_afeto, fora_raros = Counter(), Counter()
    linhas_afeto = _linhas_de(con, afeto_itens, 'afeto15k', proibidos, copia,
                              ids_final, marcas_usadas, fora_afeto)
    linhas_raros = _linhas_de(con, raros_itens, 'raros_enxuto', proibidos, copia,
                              ids_final, marcas_usadas, fora_raros)

    raros_tr, raros_val = _split_estratificado(linhas_raros)

    treino = tr35 + linhas_afeto + raros_tr
    relatorio = dict(
        final_v35=dict(treino=len(tr35), validacao=len(val35)),
        afeto15k=dict(lidos=len(afeto_itens), usados=len(linhas_afeto),
                      descartados=dict(fora_afeto), lotes_excluidos=[s for s in lotes_excluidos
                                                                      if s.startswith('a_')]),
        raros_enxuto=dict(lidos=len(raros_itens), usados=len(linhas_raros),
                          treino=len(raros_tr), validacao_extra=len(raros_val),
                          descartados=dict(fora_raros),
                          lotes_excluidos=[s for s in lotes_excluidos if s.startswith('e_')]),
        treino_total=len(treino), validacao_total=len(val35),
    )
    if verbose:
        print(f"v3.6: treino {len(treino)} (v3.5 {len(tr35)} · afeto15k {len(linhas_afeto)} · "
              f"raros_enxuto treino {len(raros_tr)}) · validação {len(val35)} "
              f"(v3.5, decide época) · validação extra raros {len(raros_val)}", flush=True)
        print(f"  afeto15k descartados: {dict(fora_afeto)} · lote excluído: "
              f"{[s for s in lotes_excluidos if s.startswith('a_')]}", flush=True)
        print(f"  raros_enxuto descartados: {dict(fora_raros)}", flush=True)
    return treino, val35, raros_val, relatorio


def contagens(linhas, rotulo):
    print(f'-- {rotulo} (n={len(linhas)}) --')
    for cab, nomes in CABECAS.items():
        print(' ', cab, dict(contar(linhas, cab, nomes)))
    print('  conteudo', dict(Counter(r['conteudo'] for r in linhas)))
    print('  tem_atrib', dict(Counter(r['tem_atrib'] for r in linhas)),
          'bandeira', dict(Counter(r['bandeira'] for r in linhas)))


if __name__ == '__main__':
    tr, val, val_raros, rel = conjuntos_v36('--v3' in sys.argv)
    print('\n=== relatório da junção ===')
    import json
    print(json.dumps(rel, indent=1, ensure_ascii=False))
    print('\n=== contagens por cabeça/classe ===')
    contagens(tr, 'treino v3.6 (final_v35 + afeto15k + raros treino)')
    contagens(val, 'validação v3.5 (decide época)')
    contagens(val_raros, 'validação extra raros_enxuto (só medida)')

    # comparação com o treino v3.5 puro (mesmo corte, sem as fontes novas)
    from dados_v35 import conjuntos as conjuntos_v35
    tr35, _ = conjuntos_v35(False, verbose=False)
    contagens(tr35, 'treino v3.5 puro (para comparação)')

    vazamento = {r['id'] for r in tr + val + val_raros}
    con = conectar()
    from dados_v35 import prova_v35
    pv, n1 = prova_v35(con)
    inter = vazamento & {r['id'] for r in pv}
    print(f'\nvazamento contra a prova: {len(inter)} (tem que ser 0)')
