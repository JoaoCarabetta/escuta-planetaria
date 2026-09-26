#!/usr/bin/env python3
"""Fase A — coletor Reddit 2015→hoje via Arctic Shift, pausável e retomável.

Estado vive no arquivo.db (tabela coleta_jobs, cursor por job; commit a cada lote):
matar o processo a qualquer momento não perde nada — rodar de novo retoma.

Pausar limpo:   touch PAUSAR   (no diretório coleta/)
Retomar:        python3 coletor.py
Acompanhar:     python3 coletor.py --status
"""
import json
import sqlite3
import sys
import time
import datetime
import random
import urllib.request
import urllib.parse
from pathlib import Path

from filtros import camada0, enxugar

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
BANDEIRA = AQUI / 'PAUSAR'
API = 'https://arctic-shift.photon-reddit.com/api/posts/search'
PAUSA_REQ = 8          # segundos entre requisições (educação com o Arctic Shift)
INICIO = '2015-01-01'
ATE = next((a.split('=')[1] for a in sys.argv if a.startswith('--ate=')), None)

# ————— plano de coleta —————
TERMOS_PT = ['sonhei', 'sonho', 'sonhos', 'pesadelo', 'pesadelos']
SUBS_GERAIS_BR = ['desabafos', 'brasil', 'relacionamentos', 'conselhodecarreira']
SUBS_CIDADES = [('saopaulo', 'SP'), ('riodejaneiro', 'RJ'), ('brasilia', 'DF'),
                ('curitiba', 'PR'), ('portoalegre', 'RS'), ('BeloHorizonte', 'MG')]
SUBS_DEDICADOS_PT = ['Sonhos']
SUBS_DEDICADOS_EN = ['Dreams', 'LucidDreaming', 'DreamInterpretation']


def plano():
    ordem = 0
    jobs = []

    def add(comunidade, termo, idioma, pais, regiao=None):
        nonlocal ordem
        ordem += 1
        jid = f"reddit:{comunidade}:{termo or 'tudo'}"
        jobs.append((jid, 'reddit', comunidade, termo, idioma, pais, regiao, ordem))

    for s in SUBS_DEDICADOS_PT:
        add(s, None, 'pt', 'BR')
    for s in SUBS_GERAIS_BR:
        for t in TERMOS_PT:
            add(s, t, 'pt', 'BR')
    for s, uf in SUBS_CIDADES:
        for t in TERMOS_PT:
            add(s, t, 'pt', 'BR', uf)
    for s in SUBS_DEDICADOS_EN:          # EN: baixa junto, processa depois
        add(s, None, 'en', None)
    return jobs


def migrar(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS coleta_jobs (
      job TEXT PRIMARY KEY,
      fonte TEXT, comunidade TEXT, termo TEXT,
      idioma TEXT, geo_pais TEXT, geo_regiao TEXT,
      ordem INTEGER,
      cursor_utc INTEGER DEFAULT 0,
      status TEXT DEFAULT 'pendente',
      coletados INTEGER DEFAULT 0,
      descartados INTEGER DEFAULT 0,
      atualizado_em TEXT
    );
    """)
    cols = [r[1] for r in con.execute('PRAGMA table_info(fila_brutos)')]
    if 'id_original' not in cols:
        con.execute('ALTER TABLE fila_brutos ADD COLUMN id_original TEXT')
    con.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_fila_idorig '
                'ON fila_brutos(id_original)')
    for j in plano():
        con.execute("""INSERT OR IGNORE INTO coleta_jobs
                       (job,fonte,comunidade,termo,idioma,geo_pais,geo_regiao,ordem)
                       VALUES (?,?,?,?,?,?,?,?)""", j)
    con.commit()


def pedir(params, tentativas=6):
    """GET com backoff; devolve lista de posts ou None (erro persistente)."""
    url = API + '?' + urllib.parse.urlencode({k: v for k, v in params.items() if v})
    espera = 60
    for _ in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'escuta-planetaria/0.2 (pesquisa academica UFF; fitbritto@gmail.com)'})
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
            if resp.get('error'):
                if 'slow down' in resp['error'].lower() or 'timeout' in resp['error'].lower():
                    time.sleep(espera + random.uniform(0, 10))
                    espera = min(espera * 2, 480)
                    continue
                print(f"    erro da API: {resp['error']}")
                return None
            return resp.get('data') or []
        except Exception as e:
            print(f"    rede: {e}; esperando {espera}s")
            time.sleep(espera)
            espera = min(espera * 2, 480)
    return None


def quer_pausar():
    return BANDEIRA.exists()


def rodar_job(con, job):
    jid, comunidade, termo, cursor = job['job'], job['comunidade'], job['termo'], job['cursor_utc']
    fim_epoch = time.time()
    print(f"▶ {jid} (cursor: {datetime.datetime.utcfromtimestamp(cursor).date() if cursor else INICIO})")
    con.execute("UPDATE coleta_jobs SET status='rodando', atualizado_em=datetime('now') WHERE job=?", (jid,))
    con.commit()

    while True:
        if quer_pausar():
            con.execute("UPDATE coleta_jobs SET status='pausado', atualizado_em=datetime('now') WHERE job=?", (jid,))
            con.commit()
            return 'pausar'

        after = (datetime.datetime.utcfromtimestamp(cursor).strftime('%Y-%m-%dT%H:%M:%S')
                 if cursor else INICIO)
        params = {'subreddit': comunidade, 'query': termo, 'after': after,
                  'sort': 'asc', 'limit': 100}
        if ATE:
            params['before'] = ATE
        dados = pedir(params)
        if dados is None:
            con.execute("UPDATE coleta_jobs SET status='erro', atualizado_em=datetime('now') WHERE job=?", (jid,))
            con.commit()
            return 'erro'

        novos, desc = 0, 0
        for p in dados:
            ts = p.get('created_utc') or 0
            cursor = max(cursor, int(ts))
            ok, motivo = camada0(p)
            if not ok:
                desc += 1
                continue
            try:
                antes = con.total_changes
                con.execute("""INSERT OR IGNORE INTO fila_brutos
                               (fonte, lote, payload, id_original)
                               VALUES ('reddit', ?, ?, ?)""",
                            (jid, json.dumps(enxugar(p), ensure_ascii=False), p.get('id')))
                if con.total_changes > antes:
                    novos += 1
            except sqlite3.Error:
                pass
        con.execute("""UPDATE coleta_jobs SET cursor_utc=?, coletados=coletados+?,
                       descartados=descartados+?, atualizado_em=datetime('now') WHERE job=?""",
                    (cursor, novos, desc, jid))
        con.commit()

        if len(dados) < 100 or cursor >= fim_epoch:
            con.execute("UPDATE coleta_jobs SET status='concluido', atualizado_em=datetime('now') WHERE job=?", (jid,))
            con.commit()
            tot = con.execute('SELECT coletados, descartados FROM coleta_jobs WHERE job=?', (jid,)).fetchone()
            print(f"  ✔ concluído: {tot[0]} na fila, {tot[1]} descartados (camada 0)")
            return 'ok'

        time.sleep(PAUSA_REQ + random.uniform(0, 3))


def status(con):
    print(f"{'job':44s} {'status':10s} {'fila':>7s} {'desc':>6s}  cursor")
    for r in con.execute("""SELECT job,status,coletados,descartados,cursor_utc
                            FROM coleta_jobs ORDER BY ordem"""):
        c = datetime.datetime.utcfromtimestamp(r[4]).date() if r[4] else '—'
        print(f"{r[0]:44s} {r[1]:10s} {r[2]:>7d} {r[3]:>6d}  {c}")
    tot = con.execute('SELECT COUNT(*) FROM fila_brutos').fetchone()[0]
    print(f"\nfila_brutos total: {tot}")


def main():
    con = sqlite3.connect(DB)
    migrar(con)
    if '--status' in sys.argv:
        status(con)
        return
    if BANDEIRA.exists():
        BANDEIRA.unlink()   # retomada limpa a bandeira
    print("Coletor Fase A — pausar: touch coleta/PAUSAR | status: coletor.py --status\n")
    pular = set()   # jobs com erro persistente nesta rodada (retentados na próxima execução)
    while True:
        job = None
        for cand in con.execute("""SELECT job, comunidade, termo, cursor_utc FROM coleta_jobs
                                   WHERE status IN ('pendente','pausado','rodando','erro')
                                   AND job NOT LIKE 'reddit_c:%'   -- comentários: coleta/comentarios.py
                                   ORDER BY ordem"""):
            if cand[0] not in pular:
                job = cand
                break
        if not job:
            print("\n★ Fase A completa (jobs com erro, se houver, retentam na próxima execução).")
            status(con)
            return
        r = rodar_job(con, dict(zip(('job', 'comunidade', 'termo', 'cursor_utc'), job)))
        if r == 'erro':
            pular.add(job[0])
        if r == 'pausar':
            print("\n⏸ pausado limpo (remova coleta/PAUSAR e rode de novo para retomar)")
            return
        if r == 'erro':
            print("  (job marcado como erro; seguindo para o próximo — rodar de novo retenta)")
        time.sleep(5)


if __name__ == '__main__':
    main()
