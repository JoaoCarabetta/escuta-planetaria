#!/usr/bin/env python3
"""Pulso agregado — Google Trends (BR): série temporal + interesse por UF.

Não são relatos: é a sombra estatística do que se busca sobre sonhar,
com a geografia que os relatos individuais não têm. Vai para a tabela `pulso`.

Uso: python3 trends.py [--serie] [--uf] [--termo "x"]
Retomável: pula o que já está gravado. Pausar: touch PAUSAR_TRENDS
"""
import sqlite3
import sys
import time
import random
from pathlib import Path
from trendspy import Trends

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
BANDEIRA = AQUI / 'PAUSAR_TRENDS'
PAUSA = 12  # segundos entre consultas (educação com o Google)

# o que o Brasil pergunta ao Google sobre sonhar
TERMOS = [
    # os clássicos do dicionário onírico brasileiro
    'sonhar com cobra', 'sonhar com dente caindo', 'sonhar com água',
    'sonhar com morto', 'sonhar com cachorro', 'sonhar com gravidez',
    'sonhar com dinheiro', 'sonhar com fogo', 'sonhar com casa',
    'sonhar com traição', 'sonhar com barata', 'sonhar com aranha',
    # o acontecimento entrando no sonho
    'sonhar com enchente', 'sonhar com doença', 'sonhar com vacina',
    'sonhar com morte', 'sonhar com polícia', 'sonhar com fome',
    # o sonhar como fenômeno
    'sonho lúcido', 'pesadelo', 'paralisia do sono', 'significado dos sonhos',
    'sonho premonitório', 'por que sonhamos',
]


def garantir(con):
    con.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_pulso_unico
                   ON pulso(fonte, termo, COALESCE(geo_regiao,''), data)""")
    con.commit()


def ja_tem(con, termo, tipo):
    q = ("SELECT COUNT(*) FROM pulso WHERE fonte='trends' AND termo=? AND geo_regiao IS NULL"
         if tipo == 'serie' else
         "SELECT COUNT(*) FROM pulso WHERE fonte='trends' AND termo=? AND geo_regiao IS NOT NULL")
    return con.execute(q, (termo,)).fetchone()[0] > 0


def serie(tr, con, termo):
    """Série semanal 2015→hoje, Brasil inteiro."""
    df = tr.interest_over_time([termo], geo='BR', timeframe='2015-01-01 2026-12-31')
    n = 0
    for data, linha in df.iterrows():
        if linha.get('isPartial'):
            continue
        con.execute("""INSERT OR IGNORE INTO pulso
            (fonte,termo,geo_pais,geo_regiao,data,granularidade,valor,unidade)
            VALUES ('trends',?,'BR',NULL,?,'mes',?,'indice_0_100')""",
            (termo, str(data)[:10], float(linha[termo])))
        n += 1
    con.commit()
    return n


def por_uf(tr, con, termo):
    """Interesse por estado, acumulado 2015→hoje."""
    df = tr.interest_by_region([termo], geo='BR', resolution='REGION',
                               timeframe='2015-01-01 2026-12-31')
    n = 0
    for _, linha in df.iterrows():
        uf = str(linha['geoCode']).replace('BR-', '')  # SP, RJ, AP...
        con.execute("""INSERT OR IGNORE INTO pulso
            (fonte,termo,geo_pais,geo_regiao,data,granularidade,valor,unidade)
            VALUES ('trends',?,'BR',?,'2015-2026','periodo',?,'indice_0_100')""",
            (termo, uf, float(linha[termo])))
        n += 1
    con.commit()
    return n


def main():
    con = sqlite3.connect(DB, timeout=180)
    con.execute('PRAGMA busy_timeout=180000')
    garantir(con)
    tr = Trends()
    termos = [a.split('--termo ')[-1]] if (a := ' '.join(sys.argv)) and '--termo ' in a else TERMOS
    fazer_serie = '--uf' not in sys.argv
    fazer_uf = '--serie' not in sys.argv

    for termo in termos:
        if BANDEIRA.exists():
            print('⏸ pausado'); return
        for tipo, fn, ativo in (('serie', serie, fazer_serie), ('uf', por_uf, fazer_uf)):
            if not ativo or ja_tem(con, termo, tipo):
                continue
            for tentativa in range(4):
                try:
                    n = fn(tr, con, termo)
                    print(f'  {termo} [{tipo}]: {n} pontos')
                    break
                except Exception as e:
                    espera = 60 * (2 ** tentativa)
                    print(f'  {termo} [{tipo}] erro ({type(e).__name__}); espera {espera}s')
                    time.sleep(espera)
            time.sleep(PAUSA + random.uniform(0, 6))
    tot = con.execute("SELECT COUNT(*) FROM pulso WHERE fonte='trends'").fetchone()[0]
    print(f'★ pulso total: {tot} pontos')


if __name__ == '__main__':
    main()
