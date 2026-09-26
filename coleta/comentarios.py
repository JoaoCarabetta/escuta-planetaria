#!/usr/bin/env python3
"""Coletor de COMENTÁRIOS do Reddit, 2015→hoje, via Arctic Shift. Pausável e retomável.

Pedido do Fitipe (26/09): muito sonho é contado em comentário, em resposta a
outro relato. Mesmos subs brasileiros da coleta de posts; termos pelas RAÍZES
sonh*/pesadel* — mas a API não aceita curinga ("sonh*" devolve zero, medido),
então as raízes viram a lista das formas (TERMOS abaixo).

A busca por texto em comentários dá TIMEOUT em períodos longos: a janela de
tempo é ADAPTATIVA — começa em 180 dias, cai pela metade a cada timeout
(mínimo 3 dias) e dobra quando vem pouca coisa.

Cada comentário entra em fila_brutos com id 't1_<id>' (não colide com posts)
e payload no formato do post (title vazio, selftext = corpo), então o moinho
processa sem mudança. Estado em coleta_jobs (job 'reddit_c:<sub>:<termo>').

  python3 comentarios.py            rodar / retomar
  python3 comentarios.py --status   acompanhar
  touch coleta/PAUSAR_COM           pausar limpo
"""
import datetime
import json
import random
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from filtros import camada0

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
PAUSA = AQUI / 'PAUSAR_COM'
API = 'https://arctic-shift.photon-reddit.com/api/comments/search'
INICIO = datetime.datetime(2015, 1, 1).timestamp()
DIA = 86400
PAUSA_REQ = 8
TERMOS = ['sonhei', 'sonho', 'sonhos', 'sonhar', 'sonhando', 'sonhou', 'sonhava',
          'pesadelo', 'pesadelos']
SUBS = ['desabafos', 'desabafo', 'relacionamentos', 'brasil', 'conversas', 'PsicologiaBR',
        'Umbanda', 'Espiritismo', 'conselhodecarreira', 'circojeca',
        'saopaulo', 'riodejaneiro', 'brasilia', 'curitiba', 'portoalegre', 'BeloHorizonte']
UF = {'saopaulo': 'SP', 'riodejaneiro': 'RJ', 'brasilia': 'DF', 'curitiba': 'PR',
      'portoalegre': 'RS', 'BeloHorizonte': 'MG'}
RAIZ = re.compile(r'sonh|pesadel', re.I)


def plano():
    jobs, ordem = [], 0
    for s in ['Sonho'] + SUBS:                 # r/Sonho: sub dedicado, tudo
        for t in ([None] if s == 'Sonho' else TERMOS):
            ordem += 1
            jobs.append((f"reddit_c:{s}:{t or 'tudo'}", 'reddit', s, t, 'pt', 'BR', UF.get(s), ordem))
    return jobs


def pedir(params):
    """→ lista, 'timeout' ou None (erro persistente)."""
    url = API + '?' + urllib.parse.urlencode({k: v for k, v in params.items() if v})
    espera = 30
    for _ in range(5):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'escuta-planetaria/0.3 (pesquisa academica UFF)'})
            with urllib.request.urlopen(req, timeout=150) as r:
                resp = json.load(r)
            err = (resp.get('error') or '').lower()
            if 'timeout' in err:
                return 'timeout'
            if 'slow down' in err:
                time.sleep(espera); espera = min(espera * 2, 480); continue
            if err:
                print(f'    erro da API: {resp["error"][:120]}'); return None
            return resp.get('data') or []
        except Exception as e:
            print(f'    rede: {e}; esperando {espera}s')
            time.sleep(espera); espera = min(espera * 2, 480)
    return None


def como_post(c):
    """Comentário no formato de post que a camada 0 e o moinho já entendem."""
    return {'id': 't1_' + str(c.get('id')), 'subreddit': c.get('subreddit'), 'title': '',
            'selftext': c.get('body'), 'created_utc': c.get('created_utc'),
            'permalink': c.get('permalink'), 'author': c.get('author'), 'url': None,
            'tipo': 'comentario', 'link_id': c.get('link_id'), 'parent_id': c.get('parent_id')}


def rodar_job(con, jid, sub, termo, cursor):
    agora = time.time()
    cursor = cursor or INICIO
    janela = 180 * DIA
    print(f'▶ {jid} desde {datetime.datetime.utcfromtimestamp(cursor).date()}', flush=True)
    while cursor < agora:
        if PAUSA.exists():
            return 'pausar'
        antes = min(cursor + janela, agora)
        dados = pedir({'subreddit': sub, 'body': termo,
                       'after': datetime.datetime.utcfromtimestamp(cursor).strftime('%Y-%m-%dT%H:%M:%S'),
                       'before': datetime.datetime.utcfromtimestamp(antes).strftime('%Y-%m-%dT%H:%M:%S'),
                       'sort': 'asc', 'limit': 100})
        if dados == 'timeout':
            janela = max(3 * DIA, janela / 2)
            time.sleep(PAUSA_REQ * 2); continue
        if dados is None:
            return 'erro'
        novos = desc = 0
        for c in dados:
            p = como_post(c)
            if not RAIZ.search(p['selftext'] or '') and termo:
                desc += 1; continue
            ok, _ = camada0(p)
            if not ok:
                desc += 1; continue
            n0 = con.total_changes
            con.execute("INSERT OR IGNORE INTO fila_brutos (fonte, lote, payload, id_original) "
                        "VALUES ('reddit', ?, ?, ?)", (jid, json.dumps(p, ensure_ascii=False), p['id']))
            novos += con.total_changes > n0
        if len(dados) == 100:
            cursor = max(cursor + 1, int(dados[-1].get('created_utc') or cursor) + 1)
        else:
            cursor = antes
            if len(dados) < 30: janela = min(365 * DIA, janela * 2)
        con.execute("""UPDATE coleta_jobs SET cursor_utc=?, coletados=coletados+?, descartados=descartados+?,
                       status='rodando', atualizado_em=datetime('now') WHERE job=?""", (int(cursor), novos, desc, jid))
        con.commit()
        time.sleep(PAUSA_REQ + random.uniform(0, 3))
    con.execute("UPDATE coleta_jobs SET status='concluido', atualizado_em=datetime('now') WHERE job=?", (jid,))
    con.commit()
    n = con.execute('SELECT coletados, descartados FROM coleta_jobs WHERE job=?', (jid,)).fetchone()
    print(f'  ✔ {jid}: {n[0]} na fila, {n[1]} descartados', flush=True)
    return 'ok'


def main():
    con = sqlite3.connect(DB, timeout=300)
    con.execute('PRAGMA busy_timeout=300000')
    for j in plano():
        con.execute("""INSERT OR IGNORE INTO coleta_jobs (job,fonte,comunidade,termo,idioma,geo_pais,geo_regiao,ordem)
                       VALUES (?,?,?,?,?,?,?,?)""", j)
    con.commit()
    if '--status' in sys.argv:
        tot = con.execute("""SELECT status, COUNT(*), SUM(coletados), SUM(descartados) FROM coleta_jobs
                             WHERE job LIKE 'reddit_c:%' GROUP BY status""").fetchall()
        for r in tot: print(r)
        return
    if PAUSA.exists(): PAUSA.unlink()
    pular = set()
    while True:
        job = next((r for r in con.execute("""SELECT job, comunidade, termo, cursor_utc FROM coleta_jobs
                     WHERE job LIKE 'reddit_c:%' AND status IN ('pendente','rodando','pausado','erro')
                     ORDER BY ordem""") if r[0] not in pular), None)
        if not job:
            print('★ comentários: todos os jobs concluídos'); return
        r = rodar_job(con, *job)
        if r == 'pausar':
            print('⏸ pausado'); return
        if r == 'erro':
            con.execute("UPDATE coleta_jobs SET status='erro' WHERE job=?", (job[0],)); con.commit()
            pular.add(job[0])


if __name__ == '__main__':
    main()
