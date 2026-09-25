#!/usr/bin/env python3
"""Serve levas para anotação v3 e grava o julgamento. Vários anotadores em paralelo.

  pegar:   python3 lote_v3.py pegar --agente=1 --n=60
  gravar:  python3 lote_v3.py gravar --agente=1 < julgamentos.json

O `pegar` distribui por PISTA DE SUPERFÍCIE, nunca pelo rótulo do qwen — senão o
anotador herda a cegueira dele. Cada agente recebe uma fatia disjunta (pelo último
dígito hexadecimal do id — o CAST do prefixo NÃO servia: o SQLite para na
primeira letra, e 65 mil relatos cujo id começa com letra ficavam inalcançáveis), então dois agentes nunca pegam o mesmo texto.

O json de gravação é uma lista de objetos com as chaves:
  id, literal, figurado, devaneio, figura, carga, tom, modo, presencas,
  atribuicao, descartavel, meta, confianca, nota
Só `id` e `confianca` são obrigatórios. Listas podem vir como lista ou string.
"""
import json, sqlite3, sys, textwrap
from pathlib import Path

DB = Path(__file__).parent.parent / 'arquivo' / 'arquivo.db'
BOLSAS = {
 'nucleo_literal': "r.texto LIKE '%onhei que%'",
 'desejo':         "(r.texto LIKE '%meu sonho é%' OR r.texto LIKE '%meu sonho era%' OR r.texto LIKE '%sempre sonhei%')",
 'intensificador': "(r.texto LIKE '%é um pesadelo%' OR r.texto LIKE '%que pesadelo%' OR r.texto LIKE '%um pesadelo%')",
 'devaneio':       "(r.texto LIKE '%sonho acordad%' OR r.texto LIKE '%sonhando acordad%' OR r.texto LIKE '%devanei%' OR r.texto LIKE '%fico imaginando%')",
 'suspeito':       "(a.tem_sonho_dormido=1 AND (r.texto LIKE '%meu sonho é%' OR r.texto LIKE '%é um pesadelo%' OR r.texto LIKE '%sempre sonhei%'))",
 'recorrencia':    "(r.texto LIKE '%de novo%' OR r.texto LIKE '%toda noite%' OR r.texto LIKE '%sempre sonho%')",
 'morto':          "(r.texto LIKE '%morreu%' OR r.texto LIKE '%falecid%')",
 'ausencia':       "(r.texto LIKE '%não sonhei%' OR r.texto LIKE '%nao sonhei%' OR r.texto LIKE '%não lembro%' OR r.texto LIKE '%nem sonhei%')",
 'atribuicao':     "(r.texto LIKE '%significa%' OR r.texto LIKE '%premoni%' OR r.texto LIKE '%aviso%' OR r.texto LIKE '%presságio%')",
 'outra_gaveta':   "a.natureza_texto IN ('idiomatico','ruido','meta')",
 'uniforme':       "1=1",
}
LISTAS = {'modo', 'presencas', 'atribuicao', 'figura'}


def conectar():
    c = sqlite3.connect(DB, timeout=900)
    c.execute('PRAGMA busy_timeout=900000')
    return c


def pegar(agente, n):
    c = conectar()
    por = max(1, n // len(BOLSAS))
    base = ("FROM relatos r JOIN anotacoes a ON a.relato_id=r.id "
            "WHERE a.versao='v2.1' AND a.anotador='ollama:qwen3.5-9b' "
            "AND r.canonico_de IS NULL AND length(r.texto) BETWEEN 25 AND 700 "
            "AND (instr('0123456789abcdef', substr(r.id,-1)) % 8) = ? "
            "AND NOT EXISTS (SELECT 1 FROM anotacoes_v3 v WHERE v.relato_id=r.id)")
    saida, vistos = [], set()
    for bolsa, cond in BOLSAS.items():
        for rid, txt in c.execute(f"SELECT r.id, r.texto {base} AND {cond} "
                                  f"ORDER BY r.id LIMIT {por}", (agente % 8,)):
            if rid in vistos:
                continue
            vistos.add(rid)
            saida.append((rid, bolsa, txt))
    print(f'### {len(saida)} textos para o agente {agente}\n')
    for i, (rid, bolsa, txt) in enumerate(saida, 1):
        print(f'--- {i} | {rid} | {bolsa}')
        print(textwrap.fill(' '.join(txt.split()), 100, initial_indent='  ',
                            subsequent_indent='  '))
        print()


def gravar(agente):
    dados = json.load(sys.stdin)
    c = conectar()
    lista = lambda v: (json.dumps(v) if isinstance(v, list) else v) or None
    n = 0
    for d in dados:
        c.execute("""INSERT OR REPLACE INTO anotacoes_v3
          (relato_id, anotador, tem_literal, tem_figurado, tem_devaneio, figura,
           carga, tom, modo, presencas, atribuicao, descartavel, meta,
           confianca, nota, bolsa)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (d['id'], f'claude:agente{agente}', d.get('literal'), d.get('figurado'),
           d.get('devaneio'), lista(d.get('figura')), d.get('carga'), d.get('tom'),
           lista(d.get('modo')), lista(d.get('presencas')), lista(d.get('atribuicao')),
           d.get('descartavel', 0), d.get('meta', 0), d['confianca'],
           d.get('nota'), d.get('bolsa')))
        n += 1
    c.commit()
    print(f'{n} anotações gravadas pelo agente {agente}')


if __name__ == '__main__':
    arg = lambda k, d: type(d)(next((a.split('=')[1] for a in sys.argv
                                     if a.startswith(f'--{k}=')), d))
    if sys.argv[1] == 'pegar':
        pegar(arg('agente', 1), arg('n', 60))
    else:
        gravar(arg('agente', 1))
