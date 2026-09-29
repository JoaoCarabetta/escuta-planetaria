#!/usr/bin/env python3
"""Separa, no Bluesky, post de comentário — a regra permanente do Fitipe
(26/09): saber sempre post × comentário.

A busca por palavra trouxe posts e respostas misturados, e o arquivo guarda
só o texto: todos ficaram como 'bluesky_nao_verificado'. Aqui cada URI vai à
API pública (getPosts, 25 por chamada) e o `record.reply` decide:

  sem reply                              → post
  reply a outra pessoa                   → comentario
  reply a si mesmo, num fio que é seu    → continuacao  (o próprio autor
                                           emendando o post; não é conversa)
  a API não devolve (apagado, conta
  fechada, bloqueio a quem não loga)     → fica 'bluesky_nao_verificado'

O detalhe (pai, raiz, se tem imagem) vai para a tabela bluesky_forma, que
também serve de ponto de retomada e, depois, para recuperar as imagens.

  python3 forma_bluesky.py            roda (retomável)
  python3 forma_bluesky.py --status   acompanhar
  touch coleta/PAUSAR_BSKY            pausar limpo
"""
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
PAUSA = AQUI / 'PAUSAR_BSKY'
API = 'https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts'
LOTE = 25
INTERVALO = 0.25        # ~4 chamadas/s, bem abaixo do limite da AppView


def did(uri):
    return uri.split('/')[2] if uri and uri.startswith('at://') else None


def classificar(post):
    rec = post.get('record') or {}
    reply = rec.get('reply')
    autor = post.get('author', {}).get('did') or did(post['uri'])
    embed = post.get('embed') or {}
    tipo_embed = embed.get('$type', '')
    tem_imagem = int('images' in tipo_embed or 'images' in json.dumps(embed.get('media') or {})[:200])
    if not reply:
        return 'post', None, None, tem_imagem
    pai = reply.get('parent', {}).get('uri')
    raiz = reply.get('root', {}).get('uri')
    if did(pai) == autor and did(raiz) == autor:
        return 'continuacao', pai, raiz, tem_imagem
    return 'comentario', pai, raiz, tem_imagem


def buscar(uris):
    q = urllib.parse.urlencode([('uris', u) for u in uris])
    espera = 5
    while True:
        try:
            with urllib.request.urlopen(f'{API}?{q}', timeout=60) as r:
                return json.load(r).get('posts', [])
        except urllib.error.HTTPError as e:
            if e.code == 400:
                # uma URI malformada derruba o lote inteiro: vai uma a uma
                if len(uris) == 1:
                    return []
                return [p for u in uris for p in buscar([u])]
            print(f'  HTTP {e.code}; esperando {espera}s', flush=True)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            print(f'  rede: {e}; esperando {espera}s', flush=True)
        time.sleep(espera)
        espera = min(espera * 2, 600)


def main():
    con = sqlite3.connect(DB, timeout=300)
    con.execute('PRAGMA busy_timeout=300000')
    con.execute("""CREATE TABLE IF NOT EXISTS bluesky_forma (
        relato_id TEXT PRIMARY KEY, uri TEXT, forma TEXT, pai TEXT, raiz TEXT,
        tem_imagem INTEGER, visto_em TEXT DEFAULT (datetime('now')))""")
    if '--status' in sys.argv:
        for r in con.execute("SELECT forma, COUNT(*) FROM bluesky_forma GROUP BY forma"):
            print(' ', r)
        falta = con.execute("""SELECT COUNT(*) FROM relatos r WHERE r.fonte='bluesky'
            AND NOT EXISTS (SELECT 1 FROM bluesky_forma b WHERE b.relato_id=r.id)""").fetchone()[0]
        print('  falta consultar:', falta)
        return
    if PAUSA.exists():
        PAUSA.unlink()
    linhas = con.execute("""SELECT r.id, r.interno_id_original FROM relatos r
        WHERE r.fonte='bluesky' AND r.interno_id_original LIKE 'at://%'
          AND NOT EXISTS (SELECT 1 FROM bluesky_forma b WHERE b.relato_id=r.id)""").fetchall()
    print(f'{len(linhas)} a consultar', flush=True)
    t0 = time.time()
    for i in range(0, len(linhas), LOTE):
        if PAUSA.exists():
            print('⏸ pausado'); return
        bloco = linhas[i:i + LOTE]
        por_uri = {u: rid for rid, u in bloco}
        vistos = {}
        for p in buscar(list(por_uri)):
            vistos[p['uri']] = classificar(p)
        gravar = []
        for u, rid in por_uri.items():
            forma, pai, raiz, img = vistos.get(u, ('indisponivel', None, None, None))
            gravar.append((rid, u, forma, pai, raiz, img))
        with con:
            con.executemany("""INSERT OR REPLACE INTO bluesky_forma
                (relato_id, uri, forma, pai, raiz, tem_imagem) VALUES (?,?,?,?,?,?)""", gravar)
            con.executemany("UPDATE relatos SET forma=? WHERE id=?",
                            [(g[2], g[0]) for g in gravar if g[2] != 'indisponivel'])
        feitos = i + len(bloco)
        if (i // LOTE) % 200 == 0:
            ritmo = feitos / max(time.time() - t0, 1)
            print(f'  {feitos}/{len(linhas)} · {ritmo:.0f}/s · faltam ~'
                  f'{(len(linhas) - feitos) / max(ritmo, 1) / 60:.0f} min', flush=True)
        time.sleep(INTERVALO)
    print('★ bluesky: forma conferida em tudo', flush=True)


if __name__ == '__main__':
    main()
