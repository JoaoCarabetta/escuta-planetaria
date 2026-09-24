#!/usr/bin/env python3
"""Roda o aluno sobre o arquivo e grava o que ele achou, com a confiança dele.

O ponto de guardar a confiança: o plano é o aprendizado ativo. O modelo rotula
tudo, e só os casos em que ele fica em dúvida voltam para anotação cara. Sem a
margem gravada, não há como escolher quais são.

  python3 inferir.py --n=5000            (o primeiro teste, como o Fitipe pediu)
  python3 inferir.py --n=0               (tudo: n=0 quer dizer sem limite)

Grava em `predicoes_v32`, que é tabela separada de `anotacoes_v3` de propósito:
julgamento de máquina não se mistura com julgamento de anotador no mesmo lugar.
"""
import json
import sqlite3
import sys
import time
from pathlib import Path

import torch
from transformers import AutoTokenizer

from dados import CARGA, PORTAO, SONHADOR, TOM
from modelo import BASE, Aluno
from treinar import MAX_LEN, memoria_livre

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
FOLGA_MIN = 12


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    n = int(arg.get('--n', 5000))
    ap = arg.get('--aparelho', 'cpu')
    lote = int(arg.get('--lote', 32))
    torch.set_num_threads(int(arg.get('--linhas', 4)))

    con = sqlite3.connect(DB, timeout=900)
    con.execute('PRAGMA busy_timeout=900000')
    con.execute("""CREATE TABLE IF NOT EXISTS predicoes_v32 (
        relato_id TEXT PRIMARY KEY, portao TEXT, tem_conteudo INTEGER,
        carga TEXT, tom TEXT, margem REAL, p_literal REAL, p_figurado REAL,
        feito_em TEXT DEFAULT (datetime('now')))""")

    # ordem por id para ser reproduzível; exclui o que já foi predito
    lim = f'LIMIT {n}' if n else ''
    # --fora roda justamente o que a faixa de treino excluía: os muito curtos
    # (onde mora 'pesadelo' escrito por 138 pessoas na mesma semana) e os muito
    # longos. O modelo não viu textos assim treinando, então o resultado precisa
    # ser olhado, não assumido.
    faixa = ('length(r.texto) NOT BETWEEN 25 AND 700' if '--fora' in sys.argv
             else 'length(r.texto) BETWEEN 25 AND 700')
    linhas = con.execute(f"""SELECT r.id, r.texto FROM relatos r
        WHERE r.canonico_de IS NULL AND {faixa}
          AND NOT EXISTS (SELECT 1 FROM predicoes_v32 p WHERE p.relato_id = r.id)
        ORDER BY r.id {lim}""").fetchall()
    print(f'{len(linhas)} relatos a classificar', flush=True)
    if not linhas:
        return

    tk = AutoTokenizer.from_pretrained(BASE)
    modelo = Aluno().to(ap)
    modelo.load_state_dict(torch.load(AQUI / 'aluno.pt', map_location=ap))
    modelo.eval()

    t0, feitos, buffer = time.time(), 0, []
    with torch.no_grad():
        for i in range(0, len(linhas), lote):
            if memoria_livre() < FOLGA_MIN:
                print('  memória apertada: pausando 20 s', flush=True)
                time.sleep(20)
            bloco = linhas[i:i + lote]
            e = tk([t for _, t in bloco], truncation=True, max_length=MAX_LEN,
                   padding=True, return_tensors='pt')
            s = modelo(e['input_ids'].to(ap), e['attention_mask'].to(ap))
            pp = torch.sigmoid(s['portao'])
            cc = torch.softmax(s['carga'], 1)
            kk = torch.softmax(s['conteudo'], 1)
            tt = torch.sigmoid(s['tom'])
            for j, (rid, _) in enumerate(bloco):
                portao = [PORTAO[k] for k in range(len(PORTAO)) if pp[j, k] > 0.5]
                tom = [TOM[k] for k in range(len(TOM)) if tt[j, k] > 0.5]
                # margem: quão longe do muro de 0,5 está a decisão mais apertada
                # do portão. Perto de zero = o modelo não sabe, e é o que volta
                # para anotação cara.
                margem = float((pp[j] - 0.5).abs().min())
                # o conteúdo é do sonho: sem sonho literal, a pergunta não existe
                tem_c = int(kk[j].argmax()) if 'literal' in portao else None
                carga = (CARGA[int(cc[j].argmax())]
                         if ('literal' in portao and tem_c == 1) else None)
                buffer.append((rid, json.dumps(portao), tem_c, carga,
                               json.dumps(tom, ensure_ascii=False), margem,
                               float(pp[j, 0]), float(pp[j, 1])))
            feitos += len(bloco)
            if len(buffer) >= 2000:
                con.executemany("""INSERT OR REPLACE INTO predicoes_v32
                    (relato_id,portao,tem_conteudo,carga,tom,margem,p_literal,p_figurado)
                    VALUES (?,?,?,?,?,?,?,?)""", buffer)
                con.commit(); buffer = []
                dt = time.time() - t0
                print(f'  {feitos}/{len(linhas)} · {feitos/dt:.0f} textos/s · '
                      f'faltam {(len(linhas)-feitos)/(feitos/dt)/60:.0f} min · '
                      f'livre {memoria_livre()}%', flush=True)
    if buffer:
        con.executemany("""INSERT OR REPLACE INTO predicoes_v32
            (relato_id,portao,tem_conteudo,carga,tom,margem,p_literal,p_figurado)
                    VALUES (?,?,?,?,?,?,?,?)""", buffer)
        con.commit()
    dt = time.time() - t0
    print(f'fim · {feitos} relatos em {dt/60:.1f} min · {feitos/dt:.0f} por segundo',
          flush=True)


if __name__ == '__main__':
    main()
