#!/usr/bin/env python3
"""O MOINHO — drena fila_brutos → tabela relatos, com tudo que sabemos fazer.

Por relato: idioma (Apple NL) → OCR de mídia (Apple Vision) → anotação v2.1 (Ollama)
          → demografia declarada (regex) → embedding (bge-m3) → relatos + anotacoes

Pausar: touch moinho/PAUSAR    Retomar: rodar de novo    Status: --status
Só PT por padrão; --tudo inclui o inglês adiado.
"""
import json
import sqlite3
import sys
import time
import urllib.request
import hashlib
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent / 'coleta'))
sys.path.insert(0, str(AQUI.parent / 'rubrica'))
sys.path.insert(0, str(AQUI.parent / 'arquivo'))

DB = AQUI.parent / 'arquivo' / 'arquivo.db'
BANDEIRA = AQUI / 'PAUSAR'
MODELO = 'qwen3.5:9b'   # gemma4:e4b tem erros benignos e é mais rápido isolado,
# mas ocupa 9.5GB vs 5.4GB: em 24GB apertado fica MAIS lento (0.36 vs 0.48/s)
VERSAO = 'v2.1'
ANOTADOR = 'ollama:' + MODELO.replace(':', '-')
PARALELO = 4

import anotar_v2  # noqa: E402
anotar_v2.MODELO = MODELO          # o moinho manda o modelo, não o argv
from anotar_v2 import anotar as anotar_llm  # noqa: E402
from apple_ai import detectar_idioma, ocr_imagem  # noqa: E402
sys.path.insert(0, str(AQUI.parent / 'arquivo'))
from extrair_demografia import extrair as extrair_demo  # noqa: E402

UF_POR_SUB = {'saopaulo': 'SP', 'riodejaneiro': 'RJ', 'brasilia': 'DF',
              'curitiba': 'PR', 'portoalegre': 'RS', 'BeloHorizonte': 'MG'}
SUBS_EN = {'Dreams', 'LucidDreaming', 'DreamInterpretation'}


def embed(texto):
    req = urllib.request.Request(
        'http://localhost:11434/api/embed',
        data=json.dumps({'model': 'bge-m3', 'input': texto[:2000]}).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        import numpy as np
        return np.array(json.load(r)['embeddings'][0], dtype='float32').tobytes()


def baixar_e_ocr(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=25) as r:
            dados = r.read(8_000_000)
        ext = '.png' if url.lower().endswith('.png') else '.jpg'
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(dados)
            caminho = f.name
        txt = ocr_imagem(caminho)
        os.unlink(caminho)
        return txt.strip()
    except Exception:
        return ''


def preparar(linha, com_ocr=True):
    fid, lote, payload = linha
    p = json.loads(payload)
    sub = p.get('subreddit') or ''
    texto = ((p.get('title') or '') + '\n' + (p.get('selftext') or '')).strip()

    # extração multimodal
    midia = 0
    if com_ocr and p.get('url') and len((p.get('selftext') or '').strip()) < 40:
        u = p['url']
        if any(k in u for k in ('i.redd.it', 'imgur', '.jpg', '.png', '.jpeg')):
            midia = 1
            extra = baixar_e_ocr(u if 'imgur.com/' not in u or '/a/' in u
                                 else u.replace('imgur.com/', 'i.imgur.com/') + '.jpg')
            if extra:
                texto += '\n\n[texto extraído da imagem] ' + extra

    idioma, _ = detectar_idioma(texto)
    nat, sonho, desejo, sofr, quals = anotar_llm(texto)
    idade, genero = extrair_demo(texto, idioma or 'pt')

    fonte = p.get('fonte', 'reddit')
    rid = hashlib.sha256(f"{fonte}:{p.get('id')}".encode()).hexdigest()[:16]
    ts = p.get('created_utc') or 0
    import datetime
    data = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ') if ts else None
    eh_en = sub in SUBS_EN

    return dict(fid=fid, rid=rid, fonte=fonte, sub=sub, data=data, idioma=idioma,
                texto=texto, midia=midia, sonho=sonho, desejo=desejo, sofr=sofr,
                quals=quals, idade=idade, genero=genero, eh_en=eh_en, nat=nat,
                emb=embed(texto), permalink=p.get('permalink'), oid=p.get('id'))


def gravar(con, r):
    fid, rid, fonte, sub = r['fid'], r['rid'], r['fonte'], r['sub']
    data, idioma, texto = r['data'], r['idioma'], r['texto']
    midia, sonho, eh_en = r['midia'], r['sonho'], r['eh_en']
    idade, genero = r['idade'], r['genero']
    p = {'permalink': r['permalink'], 'id': r['oid']}
    con.execute("""INSERT OR REPLACE INTO relatos
        (id,natureza,fonte,comunidade,data_relato,precisao_data,data_coleta,idioma,texto,
         tem_midia,midia_extraida,tem_relato_onirico,julgador,embedding,
         geo_pais,geo_regiao,geo_metodo,geo_confianca,
         sonhador_idade,sonhador_genero,demo_metodo,demo_confianca,
         interno_url,interno_id_original)
        VALUES (?,'escrito',?,?,?,'hora',date('now'),?,?,?,?,?,?,?,?,?,'comunidade',?,?,?,?,?,?,?)""",
        (rid, fonte, sub, data, idioma, texto, midia, midia, sonho, ANOTADOR, r['emb'],
         None if eh_en else 'BR', UF_POR_SUB.get(sub),
         0.85 if sub in UF_POR_SUB else (0.3 if eh_en else 0.7),
         idade, genero, 'declarado' if (idade or genero) else None,
         0.85 if (idade or genero) else None,
         ((('https://bsky.app' if fonte == 'bluesky' else 'https://www.reddit.com')
           + p['permalink']) if p.get('permalink') else None),
         p.get('id')))
    con.execute("""INSERT OR REPLACE INTO anotacoes (relato_id,anotador,versao,natureza_texto,
        tem_sonho_dormido,tem_desejo,tem_sofrimento,qualidades)
        VALUES (?,?,?,?,?,?,?,?)""", (rid, ANOTADOR, VERSAO, r['nat'], sonho,
                                       r['desejo'], r['sofr'], r['quals']))
    con.execute("UPDATE fila_brutos SET status='triado' WHERE id=?", (fid,))
    con.commit()


def _tentar(linha):
    try:
        return preparar(linha)
    except Exception as e:
        return e


def main():
    con = sqlite3.connect(DB, timeout=180)
    con.execute('PRAGMA busy_timeout=180000')
    if '--status' in sys.argv:
        for r in con.execute("SELECT status, COUNT(*) FROM fila_brutos GROUP BY status"):
            print(f'  fila {r[0]}: {r[1]}')
        print('  relatos:', con.execute('SELECT COUNT(*) FROM relatos').fetchone()[0])
        return
    if BANDEIRA.exists():
        BANDEIRA.unlink()
    filtro = "" if '--tudo' in sys.argv else \
        "AND lote NOT LIKE '%Dreams%' AND lote NOT LIKE '%Lucid%'"
    t0, ok, err = time.time(), 0, 0
    print('Moinho ligado. Pausar: touch moinho/PAUSAR')
    while True:
        if BANDEIRA.exists():
            print(f'⏸ pausado após {ok} relatos'); return
        lote = con.execute(f"""SELECT id, lote, payload FROM fila_brutos
            WHERE status='pendente' {filtro} ORDER BY id LIMIT 24""").fetchall()
        if not lote:
            print(f'★ fila vazia. {ok} moídos nesta sessão.'); return
        with ThreadPoolExecutor(max_workers=PARALELO) as pool:
            resultados = list(pool.map(lambda l: (l, _tentar(l)), lote))
        for linha, res in resultados:
            if isinstance(res, dict):
                try:
                    gravar(con, res)
                    ok += 1
                    continue
                except Exception as e:
                    res = e
            err += 1
            con.execute("UPDATE fila_brutos SET status='erro' WHERE id=?", (linha[0],))
            con.commit()
            if err <= 5:
                print(f'  erro {linha[0]}: {type(res).__name__}: {res}')
            if ok and ok % 100 == 0:
                r = ok / (time.time() - t0)
                falta = con.execute(f"SELECT COUNT(*) FROM fila_brutos WHERE status='pendente' {filtro}").fetchone()[0]
                print(f'  {ok} moídos ({r:.2f}/s) · faltam {falta} · ~{falta/r/3600:.1f}h')


if __name__ == '__main__':
    main()
