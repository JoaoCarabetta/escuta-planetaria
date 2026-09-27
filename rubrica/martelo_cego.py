#!/usr/bin/env python3
"""Página da revisão às cegas de 26/09: 83 relatos (33 longos anotados pelo
Sonnet, 50 de afeto pelo Opus), sem nenhuma marca de quem anotou nem com que
confiança. O gabarito fica em lotes/revisao_cega_GABARITO_nao_abrir.jsonl e só
entra na comparação depois.

  python3 martelo_cego.py > /tmp/revisao_cega.html

Publicada como Artifact com `db`; respostas na coleção `respostas`, uma doc por
relato (id), com portao/carga/despertar/tom/comentario.
Página viva em https://claude.ai/artifact/YTfNzT4tmmnAGKDuSnrZuF
"""
import json
from pathlib import Path

AQUI = Path(__file__).parent


def main():
    itens = [json.loads(l) for l in open(AQUI / 'lotes' / 'revisao_cega_fitipe.jsonl')]
    # só o que a página precisa: nada de tipo, anotador ou confiança
    itens = [{'n': i['n'], 'id': i['id'], 'texto': i['texto']} for i in itens]
    dados = json.dumps(itens, ensure_ascii=False).replace('<', '\\u003c')
    print((AQUI / 'martelo_cego_modelo.html').read_text().replace('/*ITENS*/', dados))


if __name__ == '__main__':
    main()
