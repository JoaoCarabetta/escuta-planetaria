#!/usr/bin/env python3
"""Recupera as imagens que o coletor do Bluesky nunca guardou.

O coletor lia o texto do post e ignorava o campo `embed` — e não o guardava nem
no payload cru. Resultado: **nenhum** dos 153.621 relatos do Bluesky tem imagem
registrada, e uma parte do arquivo está muda. Post de piada com imagem, print de
conversa, sonho desenhado: tudo entrou como texto solto e incompleto, e nós dois
lemos como se fosse o post inteiro.

Como o dado não está no arquivo, a única saída é voltar à API, post a post.

  python3 imagens_bluesky.py [--n=1000] [--pausa=2.0]

Guarda em `midias_bluesky`. Nada é baixado aqui: só as URLs, para o OCR depois
decidir o que vale a pena ler.
"""
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DB = Path(__file__).parent.parent / 'arquivo' / 'arquivo.db'
API = 'https://public.api.bsky.app/xrpc/'
LOTE = 25            # o getPosts aceita 25 uris por chamada
PAUSA = 2.0          # o reparo de ontem achou ~11 req/45s antes do 403


def pegar(caminho, espera=PAUSA):
    """Uma chamada, com a escada de recuo que o reparo de ontem ensinou.

    Naquele dia eu matei o processo duas vezes achando que tinha travado — ele
    estava recuando de um 403. Aqui o recuo é explícito e avisado.
    """
    for tentativa, atraso in enumerate((0, 30, 90, 240)):
        if atraso:
            print(f'    recuando {atraso}s (tentativa {tentativa})', flush=True)
            time.sleep(atraso)
        try:
            req = urllib.request.Request(API + caminho,
                                         headers={'User-Agent': 'sonhario/1.0'})
            with urllib.request.urlopen(req, timeout=30) as r:
                time.sleep(espera)
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return None               # post apagado: não adianta insistir
            if e.code not in (429, 403, 502, 503):
                raise
        except Exception:
            pass
    return None


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    n = int(arg.get('--n', 0))
    espera = float(arg.get('--pausa', PAUSA))
    con = sqlite3.connect(DB, timeout=900)
    con.execute('PRAGMA busy_timeout=900000')
    con.execute("""CREATE TABLE IF NOT EXISTS midias_bluesky (
        relato_id TEXT PRIMARY KEY, urls TEXT, alt TEXT, tipo TEXT,
        visto_em TEXT DEFAULT (datetime('now')))""")
    con.execute("""CREATE TABLE IF NOT EXISTS dids_bluesky (
        handle TEXT PRIMARY KEY, did TEXT)""")
    con.commit()

    lim = f'LIMIT {n}' if n else ''
    alvo = con.execute(f"""SELECT id, interno_url FROM relatos
        WHERE fonte='bluesky' AND interno_url IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM midias_bluesky m WHERE m.relato_id = id)
        ORDER BY id {lim}""").fetchall()
    print(f'{len(alvo)} relatos do Bluesky a conferir', flush=True)

    dids = dict(con.execute("SELECT handle, did FROM dids_bluesky"))
    padrao = re.compile(r'/profile/([^/]+)/post/([^/?]+)')
    fila, t0, feitos, com_img = [], time.time(), 0, 0

    for rid, url in alvo:
        m = padrao.search(url or '')
        if not m:
            continue
        handle, rkey = m.group(1), m.group(2)
        if handle not in dids:
            r = pegar(f'com.atproto.identity.resolveHandle?handle={handle}', espera)
            dids[handle] = (r or {}).get('did')
            con.execute("INSERT OR REPLACE INTO dids_bluesky VALUES (?,?)",
                        (handle, dids[handle]))
            con.commit()
        did = dids[handle]
        if not did:
            # conta apagada ou renomeada: registra como conferido e sem mídia,
            # senão a próxima execução tenta de novo para sempre
            con.execute("INSERT OR REPLACE INTO midias_bluesky VALUES (?,?,?,?,datetime('now'))",
                        (rid, None, None, 'handle_perdido'))
            continue
        fila.append((rid, f'at://{did}/app.bsky.feed.post/{rkey}'))

        if len(fila) >= LOTE:
            feitos, com_img = _descarregar(con, fila, feitos, com_img, espera)
            fila = []
            if feitos % 500 < LOTE:
                r = feitos / max(time.time() - t0, 1)
                print(f'  {feitos} conferidos · {com_img} com imagem · '
                      f'{r:.1f}/s · faltam {(len(alvo)-feitos)/max(r,.01)/3600:.1f}h',
                      flush=True)
    if fila:
        _descarregar(con, fila, feitos, com_img, espera)
    print('fim', flush=True)


def _descarregar(con, fila, feitos, com_img, espera):
    uris = '&'.join('uris=' + u for _, u in fila)
    r = pegar('app.bsky.feed.getPosts?' + uris, espera) or {}
    por_uri = {p.get('uri'): p for p in (r.get('posts') or [])}
    for rid, uri in fila:
        p = por_uri.get(uri) or {}
        e = p.get('embed') or {}
        tipo = e.get('$type', '')
        imgs = e.get('images') or (e.get('media') or {}).get('images') or []
        urls = [i.get('fullsize') for i in imgs if i.get('fullsize')]
        alts = [i.get('alt') for i in imgs if i.get('alt')]
        if urls:
            com_img += 1
        con.execute("INSERT OR REPLACE INTO midias_bluesky VALUES (?,?,?,?,datetime('now'))",
                    (rid, json.dumps(urls) if urls else None,
                     json.dumps(alts, ensure_ascii=False) if alts else None,
                     tipo or ('ausente' if p else 'post_sumiu')))
        feitos += 1
    con.commit()
    return feitos, com_img


if __name__ == '__main__':
    main()
