#!/usr/bin/env python3
"""Monta e CONGELA os lotes da anotação com a rubrica v3.3 (27/09).

Depois da revisão às cegas do Fitipe, a calibração está feita e ele pediu
"mais de 500 de cada tipo, se achar melhor". Cinco bolsas:

  longos      800  metade com portão incerto no aluno, metade sorteada
  afeto       800  literais (p≥0,9) com palavra de afeto ou de acordar
  raras       800  pistas dos valores que o aluno quase não viu (despertar
                   raro, fala_do_sonhar, voto formular, devaneio, notícia)
  atribuicao  800  literais com palavra de atribuição (premonição, sinal,
                   orixá, viagem astral, visita, significado…) — eixo novo
  sorteio     400  sorteio simples do arquivo inteiro, sem pista: é o que
                   mede as proporções reais e protege o aluno do viés das
                   bolsas

A pista só PESCA — quem decide é o anotador, com a rubrica. Fora sempre:
duplicatas, textos já anotados (anotacoes_v3), a amostra-prova e os 83 da
revisão cega. Semente 2709. Só lê o banco.

  python3 lotes_v33.py   →  rubrica/lotes/v33/<bolsa>_<k>.jsonl
"""
import json
import sqlite3
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
SAIDA = AQUI / 'lotes' / 'v33'
FORA = """r.canonico_de IS NULL
  AND r.id NOT IN (SELECT relato_id FROM anotacoes_v3)
  AND r.id NOT IN (SELECT relato_id FROM amostra_prova)"""
LIT = "r.id IN (SELECT relato_id FROM predicoes_v32 WHERE p_literal >= 0.9)"


def ou(*padroes):
    return '(' + ' OR '.join(f"lower(r.texto) LIKE '%{p}%'" for p in padroes) + ')'


# (bolsa, sub-bolsa, n, condição); arquivos cortados em pedaços por agente
LOTES = [
 ('longos', 'incertos', 400, """length(r.texto) > 1500 AND r.id IN
     (SELECT relato_id FROM revisao WHERE motivo IN ('portao_indeciso','portao_vazio'))"""),
 ('longos', 'sorteados', 400, "length(r.texto) > 1500"),
 ('afeto', '', 800, LIT + " AND length(r.texto) <= 1500 AND " + ou(
     'sonho bom', 'sonho ruim', 'sonho lindo', 'sonho horr', 'pesadelo horr', 'sonho estranho',
     'sonho esquisito', 'sonho bizarro', 'sonho maravilh', 'sonho triste', 'sonho assustador',
     'acordei feliz', 'acordei triste', 'acordei chorando', 'acordei rindo', 'acordei assustad',
     'acordei confus', 'acordei mal', 'acordei bem', 'acordei com medo', 'que alívio', 'não queria acordar')),
 ('raras', 'despertar', 300, LIT + " AND " + ou(
     'que alívio', 'ainda bem que era', 'graças a deus era', 'queria voltar', 'queria continuar',
     'não queria acordar', 'acordei confus', 'acordei sem saber', 'acordei rindo', 'acordei saltitante',
     'acordei feliz', 'acordei em paz', 'acordei desnorteado', 'acordei perdid')),
 ('raras', 'fala_do_sonhar', 200, ou(
     'toda noite eu sonho', 'sempre sonho com', 'nunca sonho', 'não consigo sonhar', 'sonhos são',
     'quase não sonho', 'lembrar dos sonhos', 'diário de sonhos', 'não lembro dos meus sonhos',
     'tenho pesadelos', 'sonho lúcido', 'paralisia do sono')),
 ('raras', 'voto_formular', 100, ou(
     'bons sonhos', 'doces sonhos', 'lindos sonhos', 'realize seus sonhos', 'sonhe com os anjos')),
 ('raras', 'devaneio', 120, ou(
     'sonho acordad', 'sonhando acordad', 'devanei', 'fico imaginando', 'fico sonhando com')),
 ('raras', 'noticia', 80, "lower(r.texto) LIKE '%http%' AND " + ou(
     'pesquisa', 'estudo', 'reportagem', 'segundo especialistas', 'cientistas')),
 ('atribuicao', '', 800, LIT + " AND " + ou(
     'premoni', 'viagem astral', 'projeção astral', 'saída do corpo', 'saí do corpo', 'desdobramento',
     'mensagem', 'sinal', 'aviso', 'avisando', 'recado', 'me visitou', 'veio me visitar', 'visita',
     'espírito', 'orixá', 'xangô', 'ogum', 'iemanjá', 'exu', 'pomba gira', 'caboclo', 'preto velho',
     'anjo', 'deus me', 'universo', 'significa', 'interpreta', 'se realizou', 'aconteceu de verdade',
     'se concretizou', 'sonho profético', 'intuição', 'guia espiritual', 'mentor')),
 ('sorteio', '', 400, "1=1"),
]
POR_AGENTE = {'longos': 160, 'afeto': 270, 'raras': 270, 'atribuicao': 270, 'sorteio': 400}


def main():
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=300)
    rng = np.random.default_rng(2709)
    cegos = {json.loads(l)['id'] for l in open(AQUI / 'lotes' / 'revisao_cega_fitipe.jsonl')}
    vistos, bolsas, resumo = set(cegos), {}, []
    for bolsa, sub, n, cond in LOTES:
        cand = [r for r in con.execute(
            f"SELECT r.id, r.texto, r.fonte, r.forma FROM relatos r WHERE {FORA} AND {cond}")
            if r[0] not in vistos]
        escolha = [cand[i] for i in rng.permutation(len(cand))[:n]]
        for rid, txt, fonte, forma in escolha:
            vistos.add(rid)
            bolsas.setdefault(bolsa, []).append(
                {'id': rid, 'bolsa': bolsa, 'pista': sub, 'fonte': fonte, 'forma': forma, 'texto': txt})
        resumo.append(f'  {bolsa:11s}{sub:15s}{len(escolha):5d} de {len(cand)} candidatos')
    SAIDA.mkdir(parents=True, exist_ok=True)
    for bolsa, itens in bolsas.items():
        ordem = rng.permutation(len(itens))        # mistura as sub-bolsas
        itens = [itens[i] for i in ordem]
        k = POR_AGENTE[bolsa]
        for j in range(0, len(itens), k):
            with open(SAIDA / f'{bolsa}_{j // k + 1}.jsonl', 'w') as f:
                for x in itens[j:j + k]:
                    f.write(json.dumps(x, ensure_ascii=False) + '\n')
    print('\n'.join(resumo))
    print(f'  total {sum(len(v) for v in bolsas.values())}')
    for p in sorted(SAIDA.glob('*.jsonl')):
        print(f'  {p.name}: {sum(1 for _ in open(p))}')


if __name__ == '__main__':
    main()
