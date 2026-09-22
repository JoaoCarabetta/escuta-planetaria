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
from bluesky import pedir, enxugar, TERMOS, LIMITE_ANTIGO

# Medido: ~11 pedidos a cada 45s e a API corta com 403, liberando em ~60s.
# É janela deslizante, não taxa fixa — 6s de passo gasta menos tempo em castigo
# do que 3s com recuos de um minuto.
PAUSA = 6

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
BANDEIRA = AQUI / 'PAUSAR_BSKY'
APLICAR = '--aplicar' in sys.argv
# folga 0 varre exatamente os dias vazios. Com 1 ou 2, buracos isolados se
# juntam em faixas longas e a maior parte do que se varre já está coletada —
# caro quando a API corta com 403 a cada ~11 pedidos.
FOLGA = int(next((a.split('=')[1] for a in sys.argv if a.startswith('--folga=')), 0))
MIN_BURACO = 3          # dias seguidos vazios, no período rarefeito


DENSO_DESDE = datetime.date(2024, 8, 1)   # migração do X: um dia vazio aqui são milhares


def buracos(con):
    """Janelas sem nenhum post COLETADO, com folga de alguns dias de cada lado.

    Conta em `fila_brutos`, não em `relatos`: o que importa é o que foi buscado,
    não o que já passou pelo moinho. Medir no moído inventava buraco onde só
    havia fila por moer — e fazia varrer o dobro do necessário.

    Antes de agosto de 2024 o Bluesky brasileiro era rarefeito (uns 7 posts por
    dia), e um dia vazio ali pode ser ausência de verdade; exige 3 seguidos.
    Depois da migração do X um único dia vazio são milhares de relatos, e
    qualquer buraco vale a varredura.
    """
    dias = set()
    for (pl,) in con.execute("SELECT payload FROM fila_brutos WHERE fonte='bluesky'"):
        ts = json.loads(pl).get('created_utc') or 0
        if ts:
            d = datetime.datetime.utcfromtimestamp(ts).date()
            if 2023 <= d.year <= 2026:
                dias.add(d)
    if not dias:
        return []
    ini, fim = min(dias), max(dias)
    saida, comeco, d = [], None, ini
    while d <= fim:
        vazio = d not in dias
        if vazio and comeco is None:
            comeco = d
        elif not vazio and comeco is not None:
            minimo = 1 if comeco >= DENSO_DESDE else MIN_BURACO
            if (d - comeco).days >= minimo:
                saida.append((comeco - datetime.timedelta(days=FOLGA),
                              d + datetime.timedelta(days=FOLGA)))
            comeco = None
        d += datetime.timedelta(days=1)
    if comeco is not None:
        saida.append((comeco - datetime.timedelta(days=FOLGA), fim))
    # junta janelas que a folga fez encostar, para não varrer duas vezes o mesmo
    juntas = []
    for a, b in sorted(saida):
        if juntas and a <= juntas[-1][1]:
            juntas[-1] = (juntas[-1][0], max(juntas[-1][1], b))
        else:
            juntas.append((a, b))
    return juntas


def varrer(con, termo, de, ate):
    """Pagina para trás de `ate` até `de`, guardando tudo que for português."""
    cursor = ate.strftime('%Y-%m-%dT23:59:59Z')
    limite = de.strftime('%Y-%m-%dT00:00:00Z')
    novos = pedidos = 0
    while cursor and cursor > limite:
        if BANDEIRA.exists():
            return novos, 'pausar'
        d = None
        for espera in (0, 60, 180, 420):      # 403 é estouro de taxa, não porta fechada
            if espera:
                print(f'      sem resposta; esperando {espera}s', flush=True)
                time.sleep(espera)
                if BANDEIRA.exists():
                    return novos, 'pausar'
            d = pedir({'q': termo, 'limit': 100, 'sort': 'latest', 'until': cursor})
            if d is not None:
                break
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
    pendentes = [(a, b, t) for a, b in js for t in TERMOS]
    refeitas = 0
    while pendentes:
        a, b, termo = pendentes.pop(0)
        n, st = varrer(con, termo, a, b)
        total += n
        print(f'  [{a}→{b}] {termo:20} +{n:>5} novos ({st}) · total {total} '
              f'· restam {len(pendentes)}', flush=True)
        if st == 'pausar':
            print('⏸ pausado'); return
        if st == 'erro' and refeitas < 60:     # volta para o fim, não se perde
            refeitas += 1
            pendentes.append((a, b, termo))
            time.sleep(30)
        time.sleep(1)
    print(f'\n★ reparo concluído: {total} posts novos na fila')


if __name__ == '__main__':
    main()
