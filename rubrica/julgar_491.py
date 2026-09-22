#!/usr/bin/env python3
"""Ollama (llama3.1:8b) julga os 491 do piloto com a rubrica v1 (rascunho).

Grava em `julgamentos` (julgador='ollama:llama3.1-8b', versao='rubrica-v1-rascunho').
Retomável: pula relatos já julgados por este julgador+versão.
Pausar: touch PAUSAR_JULGAMENTO (neste diretório). Relatório: concordancia.py.
"""
import json
import re
import sqlite3
import time
import urllib.request
from pathlib import Path

AQUI = Path(__file__).parent
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
BANDEIRA = AQUI / 'PAUSAR_JULGAMENTO'
import sys
MODELO = sys.argv[1] if len(sys.argv) > 1 else 'llama3.1:8b'
JULGADOR = 'ollama:' + MODELO.replace(':', '-')
VERSAO = 'rubrica-v1.2'

PROMPT = """Você é o triador do arquivo Escuta Planetária, que cataloga relatos públicos de sonhos (dormindo) e de desejos (acordado). Classifique o texto numa das 7 categorias:

1 relato onírico — narra sonho dormido (inclui lúcido, recorrente, paralisia, premonitório)
2 desejo/aspiração — o CENTRO do texto é um futuro desejado, meta, anseio (inclui desejo negado ou realizado-e-esvaziado)
3 pesadelo/angústia — o CENTRO do texto é sofrimento: pesadelo narrado OU desabafo/angústia (mesmo que mencione desejos de passagem)
4 idiomático/uso próprio — flerte, expressão feita, meme, o doce de padaria, citação
5 ruído comercial — publicidade, SEO "significado dos sonhos", promoção, spam
6 indecidível — sonho E desejo ao mesmo tempo, irredutível (raro e legítimo, ex. poético)
7 meta-discussão — fala SOBRE sonhar sem relatar: técnica, app, pergunta, teoria

REGRA DE OURO: a categoria vem do CENTRO do texto — do que ele principalmente É — nunca de palavras soltas nem do tom emocional. Três consequências:
- Pesadelo NARRADO como história (mesmo horrível, com medo, morte, monstros) → 1. A maioria dos relatos de sonho é escura; escuridão não muda a categoria.
- Só é 3 quando o sofrimento ACORDADO é o assunto principal: desabafo, insônia, desespero da vida — com ou sem sonho mencionado dentro.
- Desejo triste continua 2: se o centro é o que a pessoa quer ou sempre quis, é 2, mesmo em tom melancólico.

EXEMPLOS:
"Sonhei que meu pai morria num acidente, eu gritava e ninguém ouvia. Acordei assustado. O que significa?" → {"categoria": 1, "confianca": 0.9, "tem_relato_onirico": true, "idioma": "pt"}
"Há meses não durmo direito. Toda noite pesadelos, acordo exausta, minha vida está desmoronando e tenho medo de dormir" → {"categoria": 3, "confianca": 0.9, "tem_relato_onirico": true, "idioma": "pt"}
"Meu maior sonho é ter minha casa própria. Trabalho, junto dinheiro, mas parece cada vez mais longe" → {"categoria": 2, "confianca": 0.95, "tem_relato_onirico": false, "idioma": "pt"}
"Não aguento mais as brigas em casa, aprendi a falar baixo, a medir cada palavra. Sempre quis uma família em paz" → {"categoria": 3, "confianca": 0.85, "tem_relato_onirico": false, "idioma": "pt"}
"Last night I dreamt I was flying over my old school and woke up laughing" → {"categoria": 1, "confianca": 0.95, "tem_relato_onirico": true, "idioma": "en"}
"I keep dreaming I'm being chased through my old house by something I can't see. Recurring for years" → {"categoria": 1, "confianca": 0.9, "tem_relato_onirico": true, "idioma": "en"}
"Sempre sonhei em casar e ter uma família, mas ando completamente desanimada com relacionamentos" → {"categoria": 2, "confianca": 0.9, "tem_relato_onirico": false, "idioma": "pt"}
"Sonhar com cobra, o que significa? | Significado dos Sonhos" → {"categoria": 5, "confianca": 0.98, "tem_relato_onirico": false, "idioma": "pt"}
"sonhei com você essa noite 😏 aparece" → {"categoria": 4, "confianca": 0.8, "tem_relato_onirico": false, "idioma": "pt"}
"Comi um sonho de creme na padaria hoje, melhor doce da cidade" → {"categoria": 4, "confianca": 0.95, "tem_relato_onirico": false, "idioma": "pt"}
"How do I lucid dream? I tried WBTB for 22 days and got nothing, any tips?" → {"categoria": 7, "confianca": 0.9, "tem_relato_onirico": false, "idioma": "en"}
"hoje sonhei com você. não queria mais ir embora, queria voar com você. deixo esse registro" → {"categoria": 6, "confianca": 0.6, "tem_relato_onirico": false, "idioma": "pt"}

Responda APENAS o JSON:
{"categoria": N, "confianca": 0.0-1.0, "tem_relato_onirico": true/false, "idioma": "xx"}

tem_relato_onirico = existe narrativa de sonho dormido no texto, em qualquer categoria.

TEXTO:
<<<{texto}>>>"""


def julgar(texto):
    req = urllib.request.Request(
        'http://localhost:11434/api/generate',
        data=json.dumps({
            'model': MODELO,
            'prompt': PROMPT.replace('{texto}', texto[:1800]),
            'stream': False, 'format': 'json', 'think': False,
            'options': {'temperature': 0, 'num_predict': 90, 'num_ctx': 2048},
        }).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.load(r)['response']
    d = json.loads(resp)
    cat = int(d.get('categoria', 0))
    if not 1 <= cat <= 7:
        raise ValueError(f'categoria fora da faixa: {d}')
    conf = float(d.get('confianca', 0))
    tro = bool(d.get('tem_relato_onirico', False))
    idioma = re.sub(r'[^a-z]', '', str(d.get('idioma', ''))[:5].lower()) or None
    return cat, conf, tro, idioma


def main():
    con = sqlite3.connect(DB, timeout=120)
    con.execute('PRAGMA busy_timeout=120000')
    pendentes = con.execute("""
        SELECT r.id, r.texto FROM relatos r
        WHERE NOT EXISTS (SELECT 1 FROM julgamentos j
                          WHERE j.relato_id = r.id AND j.julgador = ? AND j.versao = ?)
        ORDER BY r.id""", (JULGADOR, VERSAO)).fetchall()
    print(f'{len(pendentes)} relatos a julgar ({JULGADOR}, {VERSAO})')

    t0 = time.time()
    feitos, erros = 0, 0
    for rid, texto in pendentes:
        if BANDEIRA.exists():
            print('⏸ pausado (remova PAUSAR_JULGAMENTO e rode de novo)')
            return
        try:
            cat, conf, tro, idioma = julgar(texto)
            con.execute("""INSERT INTO julgamentos
                           (relato_id, julgador, versao, categoria, confianca, tem_relato_onirico)
                           VALUES (?,?,?,?,?,?)""",
                        (rid, JULGADOR, VERSAO, cat, conf, tro))
            con.commit()
            feitos += 1
        except Exception as e:
            erros += 1
            print(f'  erro em {rid}: {e}')
            time.sleep(2)
        if feitos and feitos % 50 == 0:
            ritmo = feitos / (time.time() - t0)
            print(f'  {feitos}/{len(pendentes)} ({ritmo:.1f}/s, ~{(len(pendentes)-feitos)/ritmo/60:.0f} min restantes)')

    print(f'✔ concluído: {feitos} julgados, {erros} erros — rode concordancia.py')


if __name__ == '__main__':
    main()
