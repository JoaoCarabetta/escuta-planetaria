#!/usr/bin/env python3
"""Monta e CONGELA os lotes da anotação dirigida de sábado 26/09.

Dirigida = buscar de propósito o que é raro, em vez de esperar que apareça na
amostra (a bandeira apareceu 0 vezes em 70; fala_do_sonhar, obra, notícia e
devaneio têm revocação ZERO no BERT por falta de exemplo). Cada lote vem de
uma pista de superfície (padrão no texto) ou do detector de obra; a pista só
PESCA — quem decide é o anotador, com a rubrica.

Fora sempre: duplicatas (canonico_de), textos já anotados (anotacoes_v3) e a
amostra-prova (tem de continuar intocada para medir). Semente 2015.
Só lê o banco. Saída: rubrica/lotes/sabado_26-09.jsonl e obras_detector.jsonl.
"""
import json
import sqlite3
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
SAIDA = AQUI / 'lotes'; SAIDA.mkdir(exist_ok=True)
FORA = """r.canonico_de IS NULL
  AND r.id NOT IN (SELECT relato_id FROM anotacoes_v3)
  AND r.id NOT IN (SELECT relato_id FROM amostra_prova)"""

LOTES = [
 ('longos_incertos', 100, """length(r.texto) > 1500 AND r.id IN
     (SELECT relato_id FROM revisao WHERE motivo IN ('portao_indeciso','portao_vazio'))"""),
 ('longos_sorteados', 50, "length(r.texto) > 1500"),
 ('voto_formular', 60, """(lower(r.texto) LIKE '%bons sonhos%' OR lower(r.texto) LIKE '%doces sonhos%'
     OR lower(r.texto) LIKE '%lindos sonhos%' OR lower(r.texto) LIKE '%realize seus sonhos%'
     OR lower(r.texto) LIKE '%realizem seus sonhos%' OR lower(r.texto) LIKE '%sonhe com os anjos%')"""),
 ('fala_do_sonhar', 80, """(lower(r.texto) LIKE '%toda noite eu sonho%' OR lower(r.texto) LIKE '%sempre sonho com%'
     OR lower(r.texto) LIKE '%nunca sonho%' OR lower(r.texto) LIKE '%não consigo sonhar%'
     OR lower(r.texto) LIKE '%sonho é um aviso%' OR lower(r.texto) LIKE '%sonhos são%'
     OR lower(r.texto) LIKE '%sonhar com % significa%' OR lower(r.texto) LIKE '%quase não sonho%'
     OR lower(r.texto) LIKE '%lembrar dos sonhos%' OR lower(r.texto) LIKE '%diário de sonhos%')"""),
 ('devaneio', 60, """(lower(r.texto) LIKE '%sonho acordad%' OR lower(r.texto) LIKE '%sonhando acordad%'
     OR lower(r.texto) LIKE '%devanei%' OR lower(r.texto) LIKE '%fico imaginando%'
     OR lower(r.texto) LIKE '%fico sonhando com%')"""),
 ('noticia', 40, """lower(r.texto) LIKE '%http%' AND (lower(r.texto) LIKE '%pesquisa%'
     OR lower(r.texto) LIKE '%estudo%' OR lower(r.texto) LIKE '%reportagem%'
     OR lower(r.texto) LIKE '%segundo especialistas%' OR lower(r.texto) LIKE '%cientistas%')"""),
 ('bandeira', 100, """(lower(r.texto) LIKE '%merecem morrer%' OR lower(r.texto) LIKE '%tem que morrer%'
     OR lower(r.texto) LIKE '%tinham que morrer%' OR lower(r.texto) LIKE '%deviam morrer%'
     OR lower(r.texto) LIKE '%quero matar%' OR lower(r.texto) LIKE '%vou matar%'
     OR lower(r.texto) LIKE '%me matar%' OR lower(r.texto) LIKE '%suicid%'
     OR lower(r.texto) LIKE '%não quero mais viver%' OR lower(r.texto) LIKE '%odeio esses%'
     OR lower(r.texto) LIKE '%odeio essas%' OR lower(r.texto) LIKE '%odeio todo%'
     OR lower(r.texto) LIKE '%me odeio%')"""),
 ('carga_literal', 150, """r.id IN (SELECT relato_id FROM predicoes_v32 WHERE p_literal >= 0.9)"""),
]


def main():
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=300)
    rng = np.random.default_rng(2015)
    vistos, saida, resumo = set(), [], []
    for nome, n, cond in LOTES:
        cand = [r for r in con.execute(f"SELECT r.id, r.texto FROM relatos r WHERE {FORA} AND {cond}")
                if r[0] not in vistos]
        escolha = [cand[i] for i in rng.permutation(len(cand))[:n]]
        for rid, txt in escolha:
            vistos.add(rid); saida.append({'id': rid, 'bolsa': nome, 'texto': txt})
        resumo.append(f'  {nome:18s} {len(escolha):4d} de {len(cand)} candidatos')
    with open(SAIDA / 'sabado_26-09.jsonl', 'w') as f:
        for x in saida: f.write(json.dumps(x, ensure_ascii=False) + '\n')
    # obras do detector: ≥0,95, para os agentes com busca
    p = np.load(AQUI.parent / 'aluno' / 'obra_prob.npy')
    ids = (AQUI.parent / 'aluno' / 'obra_prob_ids.txt').read_text().split('\n')
    em_circ = {r[0] for r in con.execute("SELECT relato_id FROM grupos_copia WHERE tipo='circulacao'")}
    obras = [(ids[i], float(p[i])) for i in np.argsort(-p) if p[i] >= 0.95 and ids[i] not in em_circ
             and ids[i] not in vistos]
    textos = dict(con.execute(f"SELECT id, texto FROM relatos WHERE id IN ({','.join('?'*len(obras))})",
                              [o[0] for o in obras]))
    with open(SAIDA / 'obras_detector.jsonl', 'w') as f:
        for rid, pr in obras:
            f.write(json.dumps({'id': rid, 'p_obra': round(pr, 3), 'texto': textos[rid]}, ensure_ascii=False) + '\n')
    print('lotes de anotação dirigida (rubrica/lotes/sabado_26-09.jsonl):')
    print('\n'.join(resumo))
    print(f'  total {len(saida)}')
    print(f'obras do detector p≥0,95, fora as sementes (rubrica/lotes/obras_detector.jsonl): {len(obras)}')


if __name__ == '__main__':
    main()
