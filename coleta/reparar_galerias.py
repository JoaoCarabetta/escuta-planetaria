#!/usr/bin/env python3
"""Recupera as URLs de imagem que a camada 0 jogou fora.

`enxugar` reduzia `media_metadata` a um booleano, e como o post de galeria tem
url 'reddit.com/gallery/...' (que vira None), o relato ficava só com o título —
o texto do sonho, que estava dentro da imagem, sumia sem deixar rastro.

O payload guardado não tem mais as urls, mas tem o id do post: o Arctic Shift
devolve o original. Aqui os payloads são remendados e os itens já moídos voltam
para 'pendente', para o moinho refazê-los com o OCR.

Uso: python3 reparar_galerias.py [--aplicar]
"""
import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from filtros import urls_de_galeria

DB = Path(__file__).parent.parent / 'arquivo' / 'arquivo.db'
API = 'https://arctic-shift.photon-reddit.com/api/posts/ids?ids='
UA = {'User-Agent': 'escuta-planetaria/0.2 (pesquisa academica UFF; fitbritto@gmail.com)'}
APLICAR = '--aplicar' in sys.argv
LOTE = 50


def buscar(ids):
    for tentativa in range(4):
        try:
            req = urllib.request.Request(API + ','.join(ids), headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
            return d.get('data') or d.get('posts') or []
        except Exception as e:
            print(f'    tentativa {tentativa+1} falhou: {e}')
            time.sleep(10 * (tentativa + 1))
    return []


def main():
    con = sqlite3.connect(DB, timeout=900)
    con.execute('PRAGMA busy_timeout=900000')
    alvos = con.execute("""SELECT id, id_original, status FROM fila_brutos
        WHERE payload LIKE '%"tem_media_metadata": true%'
          AND payload NOT LIKE '%"imagens":%'""").fetchall()
    print(f'{len(alvos)} itens de galeria sem as urls')
    if not APLICAR:
        print('(sem --aplicar: nada gravado)')
        return

    achou = refazer = 0
    for i in range(0, len(alvos), LOTE):
        fatia = alvos[i:i + LOTE]
        por_oid = {o: (fid, st) for fid, o, st in fatia}
        for p in buscar(list(por_oid)):
            urls = urls_de_galeria(p)
            if not urls:
                continue
            fid, status = por_oid.get(p.get('id'), (None, None))
            if fid is None:
                continue
            bruto = con.execute('SELECT payload FROM fila_brutos WHERE id=?', (fid,)).fetchone()[0]
            d = json.loads(bruto)
            d['imagens'] = urls
            con.execute('UPDATE fila_brutos SET payload=? WHERE id=?',
                        (json.dumps(d, ensure_ascii=False), fid))
            achou += 1
            if status == 'triado':      # já virou relato sem a imagem: refaz
                con.execute("UPDATE fila_brutos SET status='pendente' WHERE id=?", (fid,))
                refazer += 1
        con.commit()
        print(f'  {min(i+LOTE, len(alvos))}/{len(alvos)} · urls recuperadas {achou} · a refazer {refazer}')
        time.sleep(3)
    print(f'\n{achou} payloads remendados · {refazer} relatos voltaram para a fila')


if __name__ == '__main__':
    main()
