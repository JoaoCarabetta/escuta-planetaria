#!/usr/bin/env python3
"""Backfill de embedding: preenche todo relato com `embed_versao` nulo.

Nulo quer dizer: nunca embeddado (moinho rodou com --sem-embed) ou embeddado
pelo método antigo que cortava em 2.000 caracteres. O embedder é o mesmo do
moinho (`embedder.py`). Enormes (corte no teto de 8.192 tokens) vão para a
tabela `revisao`.

Retomável (o filtro é o próprio nulo). Pausar: touch arquivo/PAUSAR_EMBED
Depois de rodar: a régua precisa ser refeita — duplicata só se acha com vetor.
"""
import sqlite3
import sys
import time
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import embedder  # noqa: E402
import revisao  # noqa: E402

DB = AQUI / 'arquivo.db'
PAUSA = AQUI / 'PAUSAR_EMBED'
LOTE_CURTO = 4000   # abaixo disto nenhum texto chega perto do teto: vai em lote
TAM_LOTE = 32


def main():
    con = sqlite3.connect(DB, timeout=300)
    con.execute('PRAGMA busy_timeout=300000')
    if PAUSA.exists():
        PAUSA.unlink()
    total = con.execute("SELECT COUNT(*) FROM relatos WHERE embed_versao IS NULL").fetchone()[0]
    print(f'a embeddar: {total}', flush=True)
    t0, feitos, enormes = time.time(), 0, 0
    while True:
        if PAUSA.exists():
            print(f'⏸ pausado após {feitos}'); return
        linhas = con.execute("""SELECT id, texto FROM relatos WHERE embed_versao IS NULL
                                ORDER BY id LIMIT 256""").fetchall()
        if not linhas:
            break
        curtos = [l for l in linhas if len(l[1] or '') <= LOTE_CURTO]
        longos = [l for l in linhas if len(l[1] or '') > LOTE_CURTO]
        saida = []   # (id, bytes)
        for i in range(0, len(curtos), TAM_LOTE):
            parte = curtos[i:i + TAM_LOTE]
            vs = embedder.embeddar_lote([t or ' ' for _, t in parte])
            assert len(vs) == len(parte)
            saida += list(zip([r for r, _ in parte], vs))
        for rid, texto in longos:
            v, cortado = embedder.embeddar(texto)
            saida.append((rid, v))
            if cortado:
                enormes += 1
                revisao.abrir(con, rid, 'enorme', {'chars': len(texto)})
        for rid, v in saida:
            n = con.execute("UPDATE relatos SET embedding=?, embed_versao=? WHERE id=?",
                            (v, embedder.VERSAO, rid)).rowcount
            assert n == 1, rid
        con.commit()
        feitos += len(saida)
        r = feitos / (time.time() - t0)
        print(f'  {feitos}/{total} ({r:.1f}/s, ~{(total - feitos) / r / 60:.0f} min) · '
              f'enormes {enormes}', flush=True)
    print(f'★ fim: {feitos} embeddados, {enormes} enormes, {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
