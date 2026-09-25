#!/usr/bin/env python3
"""A AMOSTRA-PROVA: 300 relatos sorteados sem pista nenhuma.

Os 519 primeiros vieram de BOLSAS por palavra ("de novo", "meu sonho é",
"significa"), que é a coisa certa a fazer para ter exemplos de categoria rara —
sorteando ao acaso não sairia nenhuma premonição para calibrar. Mas as bolsas
mentem: os cinco anotadores mostraram que em ~40% dos casos a palavra pescada
pertence à cena e não ao fenômeno ("sonhei que tava trabalhando DE NOVO").

Duas consequências, e a segunda é grave:
  · as proporções da amostra não são as do arquivo;
  · um classificador treinado só ali aprende que "de novo" prediz recorrência,
    porque no conjunto de treino prediz mesmo — fui eu que montei a correlação.
    Ele aprenderia a bolsa, não o fenômeno.

Então: treinar nas bolsas (sem elas, classe rara tem dois exemplos), MEDIR aqui.

O sorteio é feito UMA vez e gravado em `amostra_prova`. Se ele mudasse a cada
execução, deixaria de ser prova — daria para escolher, sem querer, a amostra que
confirma o que a gente espera.

  sortear:  python3 amostra_aleatoria.py sortear --n=300
  pegar:    python3 amostra_aleatoria.py pegar --agente=1 --n=60
"""
import random
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent.parent / 'arquivo' / 'arquivo.db'
SEMENTE = 2015


def conectar():
    c = sqlite3.connect(DB, timeout=900)
    c.execute('PRAGMA busy_timeout=900000')
    return c


def sortear(n):
    c = conectar()
    c.execute("""CREATE TABLE IF NOT EXISTS amostra_prova (
                   relato_id TEXT PRIMARY KEY, ordem INTEGER, sorteado_em TEXT
                   DEFAULT (datetime('now')))""")
    ja = c.execute("SELECT COUNT(*) FROM amostra_prova").fetchone()[0]
    if ja:
        print(f'já sorteada: {ja} relatos. Apague a tabela para refazer '
              f'(e perca a comparabilidade com o que já foi medido).')
        return
    # Sem JOIN com anotacoes: condicionar a "o qwen já passou por aqui" seria
    # amostrar a parte PROCESSADA do arquivo, que é a mais antiga — um viés de
    # tempo escondido dentro de um sorteio que se anuncia uniforme.
    ids = [r[0] for r in c.execute(
        "SELECT id FROM relatos WHERE canonico_de IS NULL "
        "AND length(texto) BETWEEN 25 AND 700 ORDER BY id")]
    print(f'universo: {len(ids)} relatos elegíveis')
    escolhidos = random.Random(SEMENTE).sample(ids, min(n, len(ids)))
    c.executemany("INSERT INTO amostra_prova (relato_id, ordem) VALUES (?,?)",
                  [(r, i) for i, r in enumerate(escolhidos)])
    c.commit()
    print(f'{len(escolhidos)} sorteados com semente {SEMENTE} · gravados em amostra_prova')


def pegar(agente, n):
    c = conectar()
    linhas = c.execute(
        """SELECT p.relato_id, r.texto FROM amostra_prova p JOIN relatos r ON r.id=p.relato_id
           WHERE (p.ordem % 8) = ?
             AND NOT EXISTS (SELECT 1 FROM anotacoes_v3 v WHERE v.relato_id=p.relato_id)
           ORDER BY p.ordem LIMIT ?""", (agente % 8, n)).fetchall()
    print(f'### {len(linhas)} textos da amostra-prova para o agente {agente}\n')
    for i, (rid, txt) in enumerate(linhas, 1):
        print(f'--- {i} | {rid} | sorteado')
        print(txt.replace('\n', ' ') + '\n')


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[2:]}
    if len(sys.argv) < 2:
        print(__doc__); return
    if sys.argv[1] == 'sortear':
        sortear(int(arg.get('--n', 300)))
    elif sys.argv[1] == 'pegar':
        pegar(int(arg.get('--agente', 1)), int(arg.get('--n', 60)))
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
