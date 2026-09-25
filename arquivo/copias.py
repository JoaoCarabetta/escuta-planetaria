#!/usr/bin/env python3
"""GRUPOS DE CÓPIA — o mesmo texto em contas diferentes, que NÃO é duplicata.

Duplicata é a mesma pessoa repetindo: some do planeta, fica uma. Isto é outra
coisa — gente diferente postando o mesmo texto — e esconder 23 de 24 cópias
apagaria o dado de que 24 pessoas escolheram repostar aquilo.

Então aqui ninguém some. Marca-se o grupo, o planeta desenha UM ponto e oferece
"24 cópias", e a contagem continua existindo.

Comprimento × tempo separa quatro coisas que pareciam uma só:

  curto  + janela de dias  → frase comum   ("pesadelo", 138 pessoas: coincidência
                                             de língua, não circulação)
  curto  + janela de dias
         + fala de sonho   → SONHO COLETIVO ("sonhei que tinha voltado o twitter",
                                             789 contas em 3 semanas — o achado)
  longo  + janela de dias  → COPY-PASTE     (24 cópias, 3 dias, 239 chars: ninguém
                                             escreve 239 caracteres iguais por acaso)
  longo  + ANOS            → OBRA           (quase tudo nessa faixa é letra de
                                             música; o corte de 45 dias virou um
                                             detector de canção sozinho)

O complemento vale mais que o detector: relato SEM gêmeo distante é, por
construção, fala de alguém.

  python3 copias.py [--aplicar]
"""
import datetime
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

DB = Path(__file__).parent / 'arquivo.db'
APLICAR = '--aplicar' in sys.argv
LIM = 0.97          # similaridade que define "o mesmo texto"
CURTO = 60          # abaixo disso, gente diferente escreve igual de verdade
DIAS_OBRA = 45      # acima disso, o texto atravessa o tempo: é obra, não assunto


def agrupar(con):
    """Componentes conexas do grafo de ecos entre contas diferentes."""
    pai = {}

    def raiz(x):
        while pai.get(x, x) != x:
            pai[x] = pai.get(pai[x], pai[x])
            x = pai[x]
        return x

    for a, b in con.execute(
            "SELECT a, b FROM ecos WHERE mesmo_autor=0 AND similaridade>=?", (LIM,)):
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            pai[ra] = rb
    grupos = defaultdict(list)
    for x in set(list(pai) + [raiz(x) for x in pai]):
        grupos[raiz(x)].append(x)
    return [g for g in grupos.values() if len(g) >= 3]


def classificar(g, dados):
    tam = sum(dados[i][0] for i in g) / len(g)
    datas = sorted(d for i in g if (d := dados[i][1]))
    if len(datas) >= 2:
        f = lambda s: datetime.datetime.fromisoformat(s.replace('Z', ''))
        vao = (f(datas[-1]) - f(datas[0])).days
    else:
        vao = 0
    if tam < CURTO:
        return 'frase_comum', vao
    return ('obra' if vao > DIAS_OBRA else 'copy_paste'), vao


def main():
    con = sqlite3.connect(DB, timeout=600)
    con.execute('PRAGMA busy_timeout=600000')
    dados = {i: (t, d) for i, t, d in
             con.execute("SELECT id, length(texto), data_relato FROM relatos")}
    grupos = agrupar(con)
    print(f'{len(grupos)} grupos de 3 cópias ou mais entre contas diferentes')

    linhas, contagem = [], defaultdict(lambda: [0, 0])
    for n, g in enumerate(grupos, 1):
        tipo, vao = classificar(g, dados)
        contagem[tipo][0] += 1
        contagem[tipo][1] += len(g)
        for rid in g:
            linhas.append((rid, n, tipo, len(g), vao))
    for tipo, (ng, nr) in sorted(contagem.items()):
        print(f'  {tipo:12s} {ng:4d} grupos · {nr:5d} relatos')

    if not APLICAR:
        print('\n(sem --aplicar: nada gravado)')
        return
    con.execute("""CREATE TABLE IF NOT EXISTS grupos_copia (
        relato_id TEXT PRIMARY KEY, grupo INTEGER, tipo TEXT,
        copias INTEGER, dias INTEGER)""")
    con.execute("DELETE FROM grupos_copia")          # recalcula, não acumula
    con.executemany("INSERT INTO grupos_copia VALUES (?,?,?,?,?)", linhas)
    con.commit()
    print(f'\n{len(linhas)} relatos marcados em grupos_copia')


if __name__ == '__main__':
    main()
