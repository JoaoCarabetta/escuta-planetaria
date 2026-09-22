#!/usr/bin/env python3
"""Tapa os buracos que o cursor envenenado abriu na coleta do Bluesky.

A paginação por data usava
    alvo = min(mediana, max(conv[0], anterior - 30 dias))
para se proteger de posts com createdAt forjado. O `min` invertia o sentido:
numa página envenenada ele escolhia justamente o salto de 30 dias e pulava o mês
inteiro. Resultado medido: 28 buracos, 222 dias sem NENHUM post — entre eles 29
dias em agosto/2024, o mês do bloqueio do X no Brasil, quando o Bluesky
brasileiro nasceu. A API confirmou: dentro dos buracos ela devolve páginas
cheias de posts em português e não tínhamos nenhum.

Os dias JÁ coletados estão inteiros (24/24 horas nos dias densos), então basta
varrer as janelas vazias, e não tudo de novo.

Pausar: touch coleta/PAUSAR_BSKY     Retomar: rodar de novo (é idempotente)
Uso: python3 reparar_bluesky.py [--aplicar] [--folga=2]
"""
import datetime
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bluesky import pedir, enxugar, TERMOS, PAUSA, LIMITE_ANTIGO

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
BANDEIRA = AQUI / 'PAUSAR_BSKY'
APLICAR = '--aplicar' in sys.argv
FOLGA = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--folga=')), 2))
MIN_BURACO = 2          # dias seguidos vazios para valer a pena varrer


def buracos(con):
    """Janelas sem nenhum post, com folga de alguns dias de cada lado."""
    dias = {d for (d,) in con.execute(
        """SELECT DISTINCT substr(data_relato,1,10) FROM relatos
           WHERE fonte='bluesky' AND data_relato >= ?""", (LIMITE_ANTIGO[:10],))}
    if not dias:
        return []
    ini, fim = datetime.date.fromisoformat(min(dias)), datetime.date.fromisoformat(max(dias))
    saida, comeco, d = [], None, ini
    while d <= fim:
        vazio = d.isoformat() not in dias
        if vazio and comeco is None:
            comeco = d
        elif not vazio and comeco is not None:
            if (d - comeco).days >= MIN_BURACO:
                saida.append((comeco - datetime.timedelta(days=FOLGA),
                              d + datetime.timedelta(days=FOLGA)))
            comeco = None
        d += datetime.timedelta(days=1)
    if comeco is not None and (fim - comeco).days >= MIN_BURACO:
        saida.append((comeco - datetime.timedelta(days=FOLGA), fim))
    return saida


def varrer(con, termo, de, ate):
    """Pagina para trás de `ate` até `de`, guardando tudo que for português."""
    cursor = ate.strftime('%Y-%m-%dT23:59:59Z')
    limite = de.strftime('%Y-%m-%dT00:00:00Z')
    novos = pedidos = 0
    while cursor and cursor > limite:
        if BANDEIRA.exists():
            return novos, 'pausar'
        d = pedir({'q': termo, 'limit': 100, 'sort': 'latest', 'until': cursor})
        pedidos += 1
        if d is None:
            return novos, 'erro'
        posts = d.get('posts') or []
        if not posts:
            break
        conv = []
        for post in posts:
            rec = post.get('record') or {}
            langs = rec.get('langs') or []
            if langs and not any(str(l).startswith('pt') for l in langs):
                continue
            if not (rec.get('text') or '').strip():
                continue
            antes = con.total_changes
            con.execute("""INSERT OR IGNORE INTO fila_brutos (fonte,lote,payload,id_original)
                           VALUES ('bluesky',?,?,?)""",
                        (f'bluesky:{termo}:reparo',
                         json.dumps(enxugar(post), ensure_ascii=False), post.get('uri')))
            if con.total_changes > antes:
                novos += 1
        for post in posts:                       # cursor: 5º percentil das datas
            x = (post.get('record') or {}).get('createdAt')
            if not x:
                continue
            try:
                dt = datetime.datetime.fromisoformat(x.replace('Z', '+00:00'))
                conv.append(dt.astimezone(datetime.timezone.utc))
            except Exception:
                pass
        con.commit()
        if not conv or len(posts) < 5:
            break
        conv.sort()
        k = min(len(conv) - 1, max(0, len(conv) // 20))
        prox = conv[k].strftime('%Y-%m-%dT%H:%M:%SZ')
        if prox >= cursor:                       # não andou: força um passo
            prox = (datetime.datetime.fromisoformat(cursor.replace('Z', '+00:00'))
                    - datetime.timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:%SZ')
        cursor = prox
        time.sleep(PAUSA)
    return novos, 'ok'


def main():
    con = sqlite3.connect(DB, timeout=900)
    con.execute('PRAGMA busy_timeout=900000')
    if BANDEIRA.exists():
        BANDEIRA.unlink()
    js = buracos(con)
    dias = sum((b - a).days for a, b in js)
    print(f'{len(js)} janelas a varrer · {dias} dias (com {FOLGA} de folga cada lado)')
    for a, b in js:
        print(f'  {a} → {b}  ({(b-a).days} dias)')
    if not APLICAR:
        print('\n(sem --aplicar: nada coletado)')
        return
    total = 0
    for a, b in js:
        for termo in TERMOS:
            n, st = varrer(con, termo, a, b)
            total += n
            print(f'  [{a}→{b}] {termo:20} +{n:>5} novos ({st}) · total {total}', flush=True)
            if st == 'pausar':
                print('⏸ pausado'); return
            time.sleep(1)
    print(f'\n★ reparo concluído: {total} posts novos na fila')


if __name__ == '__main__':
    main()
