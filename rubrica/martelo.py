#!/usr/bin/env python3
"""Monta a página onde o Fitipe bate o martelo — e a monta CEGA.

Ele julga 70 relatos sem ver o que eu anotei. A seleção mistura TODAS as minhas
dúvidas com uma fatia das minhas certezas, embaralhadas, sem marca de qual é
qual. Sem as certezas escondidas, o exercício só mede os casos difíceis; com
elas, mede também se a minha confiança vale alguma coisa — que é a pergunta
mais incômoda e a mais útil.

A semente é fixa: a mesma lista tem de sair de novo se alguém repetir isto.

  python3 martelo.py > /tmp/martelo.html

Depois é publicado como Artifact com a capacidade `db`; as respostas caem na
coleção `respostas`, uma doc por relato, e voltam por ArtifactData.
Página viva em https://claude.ai/artifact/Tc3pasenpWBfTuRk6LQ2Yv
"""
import json
import random
import sqlite3
from pathlib import Path

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
SEMENTE = 2015
N_ALTA, N_MEDIA = 18, 6      # as certezas escondidas no meio das dúvidas


def buscar(con, confianca):
    return [dict(r) for r in con.execute(
        """SELECT a.relato_id, r.texto, r.fonte, r.data_relato
           FROM anotacoes_v3 a JOIN relatos r ON r.id = a.relato_id
           WHERE a.confianca = ?""", (confianca,))]


def main():
    con = sqlite3.connect(DB, timeout=300)
    con.row_factory = sqlite3.Row
    rng = random.Random(SEMENTE)
    alta, media = buscar(con, 'alta'), buscar(con, 'media')
    rng.shuffle(alta)
    rng.shuffle(media)
    sel = buscar(con, 'duvida') + alta[:N_ALTA] + media[:N_MEDIA]
    rng.shuffle(sel)
    for i, s in enumerate(sel, 1):
        s['n'] = i
    # < no lugar de '<' para nenhum texto poder fechar a <script> da página
    dados = json.dumps(sel, ensure_ascii=False).replace('<', '\\u003c')
    print((AQUI / 'martelo_modelo.html').read_text().replace('/*ITENS*/', dados))


if __name__ == '__main__':
    main()
