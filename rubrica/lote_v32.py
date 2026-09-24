#!/usr/bin/env python3
"""Serve e grava anotações da rubrica v3.2. Vários anotadores em paralelo.

  pegar:   python3 lote_v31.py pegar --agente=1 --n=90 [--fonte=reanotar|prova]
  gravar:  python3 lote_v31.py gravar --agente=1 < julgamentos.json

Duas fontes, e a diferença entre elas é o ponto:

  `reanotar` — os 519 que já foram julgados na v3, agora relidos com a v3.1.
               São os mesmos textos, então dá para medir o que a rubrica nova
               muda sem que a amostra atrapalhe.

  `prova`    — os 300 sorteados uniformemente (`amostra_prova`). Só eles dizem
               as proporções REAIS do arquivo: as bolsas por palavra foram
               montadas para conter categoria rara, então medir nelas mede a
               pesca, não o arquivo.

O anotador é gravado como `claude:v32:agenteN`, ao lado das anotações v3 do
mesmo relato — nada é sobrescrito, e a comparação entre as duas rubricas
continua possível depois.

JSON de gravação: lista de objetos com `id` e `confianca` obrigatórios, mais
  literal, figurado, devaneio, obra, noticia, propaganda, descartavel,
  meta, copy_paste, falta_contexto, bandeira,
  figura, carga, tom, despertar, memoria, repeticao, modo, presencas,
  atribuicao, desejo_estado, sonhador, nota
Listas podem vir como lista ou string.
"""
import json
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent.parent / 'arquivo' / 'arquivo.db'
PORTAO = ['literal', 'figurado', 'devaneio', 'fala_do_sonhar',
          'obra', 'noticia', 'propaganda', 'descartavel']
MARCAS = ['meta', 'suspeita_circulacao', 'falta_imagem', 'falta_fio',
          'texto_truncado', 'bandeira']
LISTAS = ['figura', 'carga', 'tom', 'despertar', 'memoria', 'repeticao',
          'modo', 'presencas', 'atribuicao', 'desejo_estado', 'sonhador']


def conectar():
    c = sqlite3.connect(DB, timeout=900)
    c.execute('PRAGMA busy_timeout=900000')
    return c


def pegar(agente, n, fonte):
    c = conectar()
    if fonte == 'prova':
        base = ("FROM relatos r JOIN amostra_prova p ON p.relato_id = r.id "
                "WHERE (p.ordem % 8) = ? ")
    else:
        base = ("FROM relatos r WHERE r.id IN (SELECT relato_id FROM anotacoes_v3 "
                "WHERE anotador LIKE 'claude:%' AND anotador NOT LIKE '%v31%') "
                "AND (instr('0123456789abcdef', substr(r.id,-1)) % 8) = ? ")
    linhas = c.execute(
        f"SELECT r.id, r.texto {base} "
        "AND NOT EXISTS (SELECT 1 FROM anotacoes_v3 v WHERE v.relato_id=r.id "
        "                AND v.anotador LIKE 'claude:v31:%') "
        f"ORDER BY r.id LIMIT {int(n)}", (agente % 8,)).fetchall()
    print(f'### {len(linhas)} textos ({fonte}) para o agente {agente}\n')
    for i, (rid, txt) in enumerate(linhas, 1):
        print(f'--- {i} | {rid}')
        print(txt.replace('\n', ' ') + '\n')


def gravar(agente):
    dados = json.load(sys.stdin)
    c = conectar()
    lista = lambda v: v if isinstance(v, list) else ([v] if v else [])
    n = 0
    for d in dados:
        p = {k: int(bool(d.get(k))) for k in PORTAO + MARCAS}
        extra = {k: p[k] for k in PORTAO[3:] + MARCAS if k != 'descartavel'}
        extra.update({k: lista(d.get(k)) for k in
                      ('despertar', 'memoria', 'presencas', 'atribuicao',
                       'repeticao', 'modo', 'desejo_estado', 'sonhador')})
        c.execute("""INSERT OR REPLACE INTO anotacoes_v3
            (relato_id, anotador, tem_literal, tem_figurado, tem_devaneio,
             figura, carga, tom, qualidades, descartavel, meta, confianca,
             nota, bolsa, extra)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'v3.2',?)""",
            (d['id'], f'claude:v32:agente{agente}',
             p['literal'], p['figurado'], p['devaneio'],
             json.dumps(lista(d.get('figura')), ensure_ascii=False),
             json.dumps(lista(d.get('carga')), ensure_ascii=False),
             json.dumps(lista(d.get('tom')), ensure_ascii=False),
             json.dumps(lista(d.get('repeticao')), ensure_ascii=False),
             p['descartavel'], p['meta'], d['confianca'], d.get('nota'),
             json.dumps(extra, ensure_ascii=False)))
        n += 1
    c.commit()
    print(f'{n} anotações gravadas pelo agente {agente} (v3.1)')


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[2:]}
    if sys.argv[1] == 'pegar':
        pegar(int(arg.get('--agente', 1)), int(arg.get('--n', 90)),
              arg.get('--fonte', 'reanotar'))
    elif sys.argv[1] == 'gravar':
        gravar(int(arg.get('--agente', 1)))
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
