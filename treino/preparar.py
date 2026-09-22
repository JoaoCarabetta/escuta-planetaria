#!/usr/bin/env python3
"""Prepara o conjunto de treino do Laya a partir dos julgamentos do qwen3.5.

Princípios:
  1. Os 120 do gabarito humano NUNCA entram no treino — são o teste final.
  2. Uma fatia de validação (qwen) fica de fora para calibrar a temperatura.
  3. Classes balanceadas: sem isso o modelo aprende a responder sempre "relato".
  4. Cada par (relato, pergunta) é um item — o Laya treina por pergunta, não por texto.

Saída: treino/dados/{treino,validacao,teste}.jsonl
"""
import json
import random
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
SAIDA = AQUI / 'dados'
SAIDA.mkdir(exist_ok=True)
random.seed(2015)

# teto por classe de natureza (evita o esmagamento do "relato")
TETO_NATUREZA = 4000
# teto por marcador booleano, por valor (sim/não equilibrados)
TETO_NOUL = 5000
# qualidades: raras, usa tudo que houver + negativos na mesma medida
TETO_QUALIDADE = 1200
N_VALIDACAO = 2500

QUALIDADES = ['recorrente', 'lucido', 'premonitorio', 'visita_de_morto', 'paralisia', 'erotico']

PERGUNTAS = {
    'natureza': {
        'type': 'choice',
        'instructions': 'Que tipo de texto é este?',
        'criteria': {
            'relato': 'alguém falando da própria vida: sonhos que teve, sentimentos, experiências, desabafo',
            'meta': 'fala SOBRE sonhar sem contar a própria vida: técnica de sonho lúcido, suplemento, aplicativo, pergunta teórica, curiosidade',
            'idiomatico': 'uso solto da palavra sonho: expressão feita, meme, piada, flerte curto, o doce de padaria, título vago',
            'ruido': 'publicidade, SEO de dicionário de sonhos, promoção de produto ou canal, link de divulgação',
        },
    },
    'sonho_dormido': {'type': 'noul',
                      'instructions': 'O texto conta ou menciona um sonho que a pessoa teve dormindo (inclui pesadelo, sonho lúcido, paralisia do sono)?'},
    'desejo': {'type': 'noul',
               'instructions': 'A pessoa expressa um projeto de vida — o que quer ser, ter ou viver? Não conta pedir conselho, querer que algo ruim acabe, nem querer uma técnica.'},
    'sofrimento': {'type': 'noul',
                   'instructions': 'A pessoa DIZ que sente dor, medo, angústia, tristeza ou frustração? Não conta conteúdo assustador sem a pessoa dizer que sentiu.'},
}
for q in QUALIDADES:
    PERGUNTAS[f'q_{q}'] = {
        'type': 'noul',
        'instructions': {
            'recorrente': 'O sonho relatado se repete — a pessoa diz que sonha isso mais de uma vez?',
            'lucido': 'A pessoa percebeu, dentro do sonho, que estava sonhando?',
            'premonitorio': 'O sonho anunciou algo que aconteceu depois, ou a pessoa o trata como aviso?',
            'visita_de_morto': 'Alguém que já morreu aparece no sonho?',
            'paralisia': 'Houve paralisia do sono ou falso despertar?',
            'erotico': 'O sonho relatado tem conteúdo sexual?',
        }[q],
    }


def carregar(con):
    gabarito = {r[0] for r in con.execute(
        "SELECT relato_id FROM anotacoes WHERE versao='v2-gabarito'")}
    linhas = con.execute("""SELECT a.relato_id, r.texto, a.natureza_texto,
            a.tem_sonho_dormido, a.tem_desejo, a.tem_sofrimento, a.qualidades
        FROM anotacoes a JOIN relatos r ON r.id = a.relato_id
        WHERE a.versao='v2.1' AND a.anotador LIKE 'ollama%' AND length(r.texto) > 20""").fetchall()
    return gabarito, [l for l in linhas if l[0] not in gabarito]


def montar_itens(linhas):
    """Cada item: (relato_id, texto, pergunta_id, resposta)."""
    por_classe = defaultdict(list)
    for rid, texto, nat, sonho, desejo, sofr, quals in linhas:
        qs = set(json.loads(quals or '[]'))
        por_classe[('natureza', nat)].append((rid, texto, 'natureza', nat))
        for pid, val in (('sonho_dormido', sonho), ('desejo', desejo), ('sofrimento', sofr)):
            r = 'sim' if val else 'nao'
            por_classe[(pid, r)].append((rid, texto, pid, r))
        if sonho:  # qualidades só fazem sentido quando há sonho
            for q in QUALIDADES:
                r = 'sim' if q in qs else 'nao'
                por_classe[(f'q_{q}', r)].append((rid, texto, f'q_{q}', r))
    return por_classe


def balancear(por_classe):
    itens = []
    for (pid, resposta), lista in por_classe.items():
        random.shuffle(lista)
        if pid == 'natureza':
            teto = TETO_NATUREZA
        elif pid.startswith('q_'):
            teto = TETO_QUALIDADE
        else:
            teto = TETO_NOUL
        itens += lista[:teto]
    random.shuffle(itens)
    return itens


def main():
    con = sqlite3.connect(DB, timeout=180)
    con.execute('PRAGMA busy_timeout=180000')
    gabarito, linhas = carregar(con)
    print(f'{len(linhas)} relatos julgados pelo qwen (fora os {len(gabarito)} do gabarito)')

    itens = balancear(montar_itens(linhas))
    validacao, treino = itens[:N_VALIDACAO], itens[N_VALIDACAO:]

    # teste = os 120 do gabarito humano, em todas as perguntas
    teste = []
    for rid, texto, nat, sonho, desejo, sofr, quals in con.execute(
            """SELECT a.relato_id, r.texto, a.natureza_texto, a.tem_sonho_dormido,
                      a.tem_desejo, a.tem_sofrimento, a.qualidades
               FROM anotacoes a JOIN relatos r ON r.id=a.relato_id
               WHERE a.versao='v2-gabarito'"""):
        qs = set(json.loads(quals or '[]'))
        teste.append((rid, texto, 'natureza', nat))
        for pid, val in (('sonho_dormido', sonho), ('desejo', desejo), ('sofrimento', sofr)):
            teste.append((rid, texto, pid, 'sim' if val else 'nao'))
        if sonho:
            for q in QUALIDADES:
                teste.append((rid, texto, f'q_{q}', 'sim' if q in qs else 'nao'))

    for nome, dados in (('treino', treino), ('validacao', validacao), ('teste', teste)):
        with open(SAIDA / f'{nome}.jsonl', 'w') as f:
            for rid, texto, pid, resp in dados:
                f.write(json.dumps({'id': rid, 'texto': texto[:2000],
                                    'pergunta': pid, 'resposta': resp},
                                   ensure_ascii=False) + '\n')
        c = Counter(f'{d[2]}={d[3]}' for d in dados)
        print(f'{nome}: {len(dados)} itens')
        if nome == 'treino':
            for k, v in sorted(c.items()):
                print(f'    {k}: {v}')

    json.dump(PERGUNTAS, open(SAIDA / 'perguntas.json', 'w'), ensure_ascii=False, indent=1)
    print('perguntas.json salvo')


if __name__ == '__main__':
    main()
