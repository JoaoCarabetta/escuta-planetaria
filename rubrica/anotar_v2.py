#!/usr/bin/env python3
"""Rubrica v2 — natureza do texto + marcadores independentes do imaginário.

Uso: python3 anotar_v2.py [modelo] [--amostra]
  --amostra: só os 120 do gabarito (para medir concordância)
Retomável. Pausar: touch PAUSAR_JULGAMENTO
"""
import json
import re
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
BANDEIRA = AQUI / 'PAUSAR_JULGAMENTO'
MODELO = next((a for a in sys.argv[1:] if not a.startswith('--')), 'qwen3.5:9b')
ANOTADOR = 'ollama:' + MODELO.replace(':', '-')
VERSAO = 'v2.1'
SO_AMOSTRA = '--amostra' in sys.argv

PROMPT = """Você cataloga textos públicos para um arquivo de sonhos e desejos. Responda duas coisas sobre o texto.

A) natureza_texto — que tipo de texto é (escolha UM):
"relato"     — alguém falando da própria vida, sonhos, sentimentos ou experiências
"meta"       — fala SOBRE sonhar sem contar a própria vida: técnica de sonho lúcido, suplementos, apps, pergunta teórica, curiosidade
"idiomatico" — uso solto da palavra sonho: expressão feita, meme, piada, flerte curto, o doce de padaria, título vago
"ruido"      — publicidade, SEO de dicionário de sonhos ("Sonhar com X, o que significa"), promoção, link de divulgação

B) três marcadores INDEPENDENTES (cada um sim/não, podem ser todos verdadeiros):
tem_sonho_dormido — o texto conta ou menciona um sonho que a pessoa teve dormindo (inclui pesadelo, sonho lúcido, paralisia do sono)
tem_desejo        — a pessoa expressa um projeto de vida: o que quer ser, ter ou viver ("meu sonho é...", "sempre quis...", "queria muito ter/ser...").
                    NÃO marque por: pedir conselho ou resposta; querer que algo ruim acabe; querer técnica/habilidade (sonhar lúcido, dormir melhor);
                    gostar de algo; desejo de outra pessoa; saudade sozinha.
tem_sofrimento    — a pessoa DIZ que sente dor, medo, angústia, tristeza ou frustração (própria, no presente ou lembrada).
                    NÃO marque por: o sonho ter conteúdo assustador sem a pessoa dizer que sentiu medo; fatos ruins narrados com distanciamento;
                    curiosidade ou estranhamento.

C) qualidades — lista, só se tem_sonho_dormido for verdadeiro. Só marque quando o texto AFIRMA a qualidade; na dúvida, deixe de fora. Termos:
"recorrente" (sonho que se repete), "lucido" (sabia que estava sonhando), "premonitorio" (sonho que se realizou ou anuncia),
"visita_de_morto" (alguém que morreu aparece no sonho), "paralisia" (paralisia do sono ou falso despertar), "erotico" (sonho sexual)

EXEMPLOS:
"Sonhei que meu pai morria num acidente, acordei assustado" → {"natureza_texto":"relato","tem_sonho_dormido":true,"tem_desejo":false,"tem_sofrimento":true,"qualidades":[]}
"Meu maior sonho é ter minha casa própria, mas parece cada vez mais longe" → {"natureza_texto":"relato","tem_sonho_dormido":false,"tem_desejo":true,"tem_sofrimento":true,"qualidades":[]}
"Sonhei que tinha amigos e acordei triste, não tenho ninguém há anos" → {"natureza_texto":"relato","tem_sonho_dormido":true,"tem_desejo":true,"tem_sofrimento":true,"qualidades":[]}
"Minha avó morreu ano passado e ontem ela apareceu no meu sonho, conversamos" → {"natureza_texto":"relato","tem_sonho_dormido":true,"tem_desejo":false,"tem_sofrimento":false,"qualidades":["visita_de_morto"]}
"Faz anos que sonho a mesma coisa: corro por um corredor sem fim" → {"natureza_texto":"relato","tem_sonho_dormido":true,"tem_desejo":false,"tem_sofrimento":false,"qualidades":["recorrente"]}
"How do I lucid dream? Tried WBTB for 22 days, nothing" → {"natureza_texto":"meta","tem_sonho_dormido":false,"tem_desejo":false,"tem_sofrimento":false,"qualidades":[]}
"Sonhar com cobra, o que significa? | Significado dos Sonhos" → {"natureza_texto":"ruido","tem_sonho_dormido":false,"tem_desejo":false,"tem_sofrimento":false,"qualidades":[]}
"Comi um sonho de creme na padaria, melhor doce da cidade" → {"natureza_texto":"idiomatico","tem_sonho_dormido":false,"tem_desejo":false,"tem_sofrimento":false,"qualidades":[]}

Responda APENAS o JSON com as cinco chaves.

TEXTO:
<<<{texto}>>>"""

def _resgatar(bruto):
    """Resgata os 5 campos de um JSON truncado (o modelo às vezes comenta demais)."""
    d = {}
    m = re.search(r'"natureza_texto"\s*:\s*"(\w+)"', bruto)
    if not m:
        raise ValueError('sem natureza_texto no JSON truncado')
    d['natureza_texto'] = m.group(1)
    for c in ('tem_sonho_dormido', 'tem_desejo', 'tem_sofrimento'):
        mm = re.search(rf'"{c}"\s*:\s*(true|false)', bruto)
        if not mm:
            raise ValueError(f'sem {c}')
        d[c] = mm.group(1) == 'true'
    mq = re.search(r'"qualidades"\s*:\s*\[([^\]]*)\]', bruto)
    d['qualidades'] = re.findall(r'"(\w+)"', mq.group(1)) if mq else []
    return d


NATS = {'relato', 'meta', 'idiomatico', 'ruido'}
QUALS = {'recorrente', 'lucido', 'premonitorio', 'visita_de_morto', 'paralisia', 'erotico'}


def anotar(texto, tentativas=3):
    for t in range(tentativas):
        try:
            return _anotar(texto, 200 + 120*t)
        except Exception:
            if t == tentativas - 1:
                raise
    raise RuntimeError('inalcançável')


def _anotar(texto, npred=200):
    req = urllib.request.Request(
        'http://localhost:11434/api/generate',
        data=json.dumps({
            'model': MODELO, 'prompt': PROMPT.replace('{texto}', texto[:1800]),
            'stream': False, 'think': False,
            'format': {  # esquema rígido: impede o modelo de inventar chaves extras
                'type': 'object',
                'properties': {
                    'natureza_texto': {'type': 'string',
                                       'enum': ['relato', 'meta', 'idiomatico', 'ruido']},
                    'tem_sonho_dormido': {'type': 'boolean'},
                    'tem_desejo': {'type': 'boolean'},
                    'tem_sofrimento': {'type': 'boolean'},
                    'qualidades': {'type': 'array', 'items': {'type': 'string'}},
                },
                'required': ['natureza_texto', 'tem_sonho_dormido', 'tem_desejo',
                             'tem_sofrimento', 'qualidades'],
            },
            'options': {'temperature': 0, 'num_predict': npred, 'num_ctx': 2048},
        }).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        bruto = json.load(r)['response']
    try:
        d = json.loads(bruto)
    except json.JSONDecodeError:
        d = _resgatar(bruto)
    nat = str(d.get('natureza_texto', '')).lower().strip()
    if nat not in NATS:
        raise ValueError(f'natureza inválida: {nat}')
    quals = [q for q in (d.get('qualidades') or []) if str(q).lower() in QUALS]
    return (nat, int(bool(d.get('tem_sonho_dormido'))), int(bool(d.get('tem_desejo'))),
            int(bool(d.get('tem_sofrimento'))), json.dumps(quals))


def main():
    con = sqlite3.connect(DB, timeout=120)
    con.execute('PRAGMA busy_timeout=120000')
    filtro = ("AND r.id IN (SELECT relato_id FROM anotacoes WHERE versao='v2-gabarito')"
              if SO_AMOSTRA else "")
    pend = con.execute(f"""SELECT r.id, r.texto FROM relatos r
        WHERE NOT EXISTS (SELECT 1 FROM anotacoes a WHERE a.relato_id=r.id
                          AND a.anotador=? AND a.versao=?) {filtro}
        ORDER BY r.id""", (ANOTADOR, VERSAO)).fetchall()
    print(f'{len(pend)} a anotar ({ANOTADOR})')
    t0, ok, err = time.time(), 0, 0
    for rid, texto in pend:
        if BANDEIRA.exists():
            print('⏸ pausado'); return
        try:
            nat, s, d, so, q = anotar(texto)
            con.execute("""INSERT OR REPLACE INTO anotacoes (relato_id, anotador, versao,
                natureza_texto, tem_sonho_dormido, tem_desejo, tem_sofrimento, qualidades)
                VALUES (?,?,?,?,?,?,?,?)""", (rid, ANOTADOR, VERSAO, nat, s, d, so, q))
            con.commit(); ok += 1
        except Exception as e:
            err += 1
            if err < 5: print(f'  erro {rid}: {e}')
        if ok and ok % 40 == 0:
            r = ok / (time.time() - t0)
            print(f'  {ok}/{len(pend)} ({r:.2f}/s)')
    print(f'✔ {ok} anotados, {err} erros')


if __name__ == '__main__':
    main()
