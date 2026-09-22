#!/usr/bin/env python3
"""Coletor Bluesky — o passado (2023→hoje), em português.

A escuta diária/presente é território do João; aqui só o retroativo.
Pagina para trás no tempo com o cursor da searchPosts e normaliza o payload
no MESMO formato do Reddit, para o moinho funcionar sem mudança.

Pausar: touch PAUSAR_BSKY   Retomar: rodar de novo   Status: --status
"""
import json
import sqlite3
import sys
import time
import random
import datetime
import urllib.request
import urllib.parse
import socket
from pathlib import Path

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
BANDEIRA = AQUI / 'PAUSAR_BSKY'
socket.setdefaulttimeout(45)
API = 'https://api.bsky.app/xrpc/app.bsky.feed.searchPosts'
UA = 'escuta-planetaria/0.2 (pesquisa academica UFF; fitbritto@gmail.com)'
PAUSA = 3
LIMITE_ANTIGO = '2023-01-01T00:00:00Z'   # antes disso o Bluesky nem existia

TERMOS = ['sonhei', '"sonhei que"', 'pesadelo', '"meu sonho"', '"sonho que tive"',
          '"tive um sonho"', '"acordei do sonho"', 'sonhos']


def migrar(con):
    cols = [r[1] for r in con.execute('PRAGMA table_info(coleta_jobs)')]
    if 'cursor_txt' not in cols:
        con.execute('ALTER TABLE coleta_jobs ADD COLUMN cursor_txt TEXT')
    ordem = 300
    for t in TERMOS:
        ordem += 1
        con.execute("""INSERT OR IGNORE INTO coleta_jobs
            (job,fonte,comunidade,termo,idioma,geo_pais,ordem,status)
            VALUES (?,'bluesky','bluesky',?,'pt','BR',?,'pendente')""",
            (f'bluesky:{t}', t, ordem))
    con.commit()


def pedir(params, tentativas=5):
    url = API + '?' + urllib.parse.urlencode(params)
    espera = 20
    for _ in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except Exception as e:
            print(f'    rede: {e}; espera {espera}s')
            time.sleep(espera)
            espera = min(espera * 2, 120)
    return None


def camada0_bsky(texto):
    t = texto.strip()
    if len(t) < 25:
        return False
    baixo = t.lower()
    if baixo.startswith(('http', 'rt @')) or baixo.count('http') > 2:
        return False
    if any(k in baixo for k in ('significado dos sonhos', 'compre ', 'link na bio',
                                'promoção', 'cupom', 'siga @')):
        return False
    return True


def enxugar(post):
    """Normaliza no formato que o moinho já entende (chaves do Reddit)."""
    rec = post.get('record') or {}
    uri = post.get('uri') or ''
    handle = (post.get('author') or {}).get('handle', '')
    rkey = uri.rsplit('/', 1)[-1]
    criado = rec.get('createdAt') or ''
    try:
        ts = int(datetime.datetime.fromisoformat(criado.replace('Z', '+00:00')).timestamp())
    except Exception:
        ts = 0
    return {
        'fonte': 'bluesky',
        'id': uri,
        'subreddit': 'bluesky',
        'title': '',
        'selftext': rec.get('text') or '',
        'created_utc': ts,
        'permalink': f'/profile/{handle}/post/{rkey}' if handle else None,
        'author': (post.get('author') or {}).get('did'),
        'url': None,
        'langs': rec.get('langs'),
        'num_comments': post.get('replyCount'),
    }


def rodar_job(con, job, termo, cursor):
    print(f'▶ bluesky {termo} (cursor: {"novo" if not cursor else "retomando"})')
    con.execute("UPDATE coleta_jobs SET status='rodando' WHERE job=?", (job,))
    con.commit()
    params = {'q': termo, 'limit': 100, 'sort': 'latest'}
    novos = desc = 0
    while True:
        if BANDEIRA.exists():
            con.execute("UPDATE coleta_jobs SET status='pausado', cursor_txt=? WHERE job=?", (cursor, job))
            con.commit()
            return 'pausar'
        p = dict(params)
        if cursor:
            p['until'] = cursor          # pagina para trás por DATA (cursor dá 403)
        d = pedir(p)
        if d is None:
            con.execute("UPDATE coleta_jobs SET status='erro', cursor_txt=? WHERE job=?", (cursor, job))
            con.commit()
            return 'erro'
        posts = d.get('posts') or []
        for post in posts:
            rec = post.get('record') or {}
            langs = rec.get('langs') or []
            if langs and not any(str(l).startswith('pt') for l in langs):
                desc += 1
                continue
            texto = rec.get('text') or ''
            if not camada0_bsky(texto):
                desc += 1
                continue
            antes = con.total_changes
            con.execute("""INSERT OR IGNORE INTO fila_brutos (fonte,lote,payload,id_original)
                           VALUES ('bluesky',?,?,?)""",
                        (job, json.dumps(enxugar(post), ensure_ascii=False), post.get('uri')))
            if con.total_changes > antes:
                novos += 1
        # próxima página: até o post mais antigo desta (menos 1s)
        datas = [ (pp.get('record') or {}).get('createdAt') for pp in posts ]
        # Bluesky permite createdAt forjado: um único post com data falsa de 2018
        # envenenava o cursor e encerrava o job. Usa a MEDIANA e limita o salto.
        conv = []
        for x in datas:
            if not x:
                continue
            try:
                dt = datetime.datetime.fromisoformat(x.replace('Z', '+00:00'))
                if dt.tzinfo is None:                      # data sem fuso: assume UTC
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
                conv.append(dt.astimezone(datetime.timezone.utc))
            except Exception:
                pass
        conv.sort()
        if conv:
            anterior = datetime.datetime.now(datetime.timezone.utc)
            if cursor:
                anterior = datetime.datetime.fromisoformat(
                    cursor.replace('Z', '+00:00')).astimezone(datetime.timezone.utc)
            mediana = conv[len(conv) // 2]
            menor_plausivel = max(conv[0], anterior - datetime.timedelta(days=30))
            alvo = min(mediana, menor_plausivel)
            if alvo >= anterior:
                alvo = anterior - datetime.timedelta(hours=6)
            cursor = alvo.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            cursor = None
        if cursor and cursor < LIMITE_ANTIGO:
            cursor = None
        con.execute("""UPDATE coleta_jobs SET cursor_txt=?, coletados=coletados+?,
                       descartados=descartados+?, atualizado_em=datetime('now') WHERE job=?""",
                    (cursor, novos, desc, job))
        con.commit()
        novos = desc = 0
        if not cursor or not posts or len(posts) < 5:
            con.execute("UPDATE coleta_jobs SET status='concluido' WHERE job=?", (job,))
            con.commit()
            t = con.execute('SELECT coletados,descartados FROM coleta_jobs WHERE job=?', (job,)).fetchone()
            print(f'  ✔ {t[0]} na fila, {t[1]} descartados')
            return 'ok'
        time.sleep(PAUSA + random.uniform(0, 2))


def main():
    con = sqlite3.connect(DB, timeout=180)
    con.execute('PRAGMA busy_timeout=180000')
    migrar(con)
    if '--status' in sys.argv:
        for r in con.execute("""SELECT termo,status,coletados,descartados FROM coleta_jobs
                                WHERE fonte='bluesky' ORDER BY ordem"""):
            print(f'  {r[0]:20s} {r[1]:10s} {r[2]:>6} na fila, {r[3]:>6} fora')
        return
    if BANDEIRA.exists():
        BANDEIRA.unlink()
    while True:
        j = con.execute("""SELECT job,termo,cursor_txt FROM coleta_jobs
            WHERE fonte='bluesky' AND status IN ('pendente','pausado','rodando','erro')
            ORDER BY ordem LIMIT 1""").fetchone()
        if not j:
            print('★ Bluesky retroativo completo.')
            return
        if rodar_job(con, *j) == 'pausar':
            print('⏸ pausado')
            return
        time.sleep(4)


if __name__ == '__main__':
    main()
