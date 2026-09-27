#!/usr/bin/env python3
"""Lotes de CORREÇÃO para a rubrica v3.5 (27/09, noite) — e a amostra-prova.

Parte da anotação v3.4 (lotes/v34/final_v34.jsonl) e manda de volta só os
textos que as decisões novas do Fitipe podem mudar:

  choro        literal com choro no texto (choro de emoção = acordou_bem)
  nao_real     "não era real"/"queria voltar"… (prazerosa ou mista + decepção)
  entidade     atribuição sem origem dita, ou entidade/morto no sonho
  quem         atribuição com pista de livro, doutrina, terapia, oráculo,
               herança ou desconhecido (valores novos de atribuicao_quem)
  bandeira     toda bandeira (ódio a si sem intenção não levanta mais)
  figura       votos/escape/figura vazia (escape × metafora, votos_no_fim)
  repeticao    "de novo" / literal+fala (o "sonhei de novo" deixa de ser hábito)

E a AMOSTRA-PROVA (300 sorteados, nunca vistos pelo aluno) sai inteira em
lotes à parte, para ser anotada do zero pela v3.5: é a régua do retreino.

  python3 lotes_v35.py  →  rubrica/lotes/v35/corr_<k>.jsonl e prova_<k>.jsonl
"""
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).parent
V34 = AQUI / 'lotes' / 'v34' / 'final_v34.jsonl'
SAIDA = AQUI / 'lotes' / 'v35'
DB = AQUI.parent / 'arquivo' / 'arquivo.db'
LIMITE, MAX_ITENS = 140_000, 200

R_CHORO = re.compile(r'chor', re.I)
R_NAOREAL = re.compile(r'n[ãa]o (era|é|foi) (real|verdade)|era s[óo] um sonho|queria (voltar|continuar)|'
                       r'n[ãa]o queria acordar|pena que (era|foi) sonho', re.I)
R_ENTIDADE = re.compile(r'orix|xang|ogum|iemanj|oxum|exu|pomba ?gira|pilintra|caboclo|preto velho|preta velha|'
                        r'guia|mentor|santo|anjo|jesus|deus|esp[íi]rito', re.I)
R_QUEM = re.compile(r'kardec|livro|doutrina|divaldo|freud|jung|psican|psic[óo]log|analista|terapeut|terapia|'
                    r'psiquiatr|b[úu]zios|tar[ôo]|cartomante|baralho|cigan|bisav|curandeir|ancestr|'
                    r'minha fam[íi]lia|tradi[çc]|algu[ée]m (me )?disse|perguntei pra', re.I)


def motivos(a, t):
    p, m = a['portao'], []
    if 'literal' in p and R_CHORO.search(t):
        m.append('choro')
    if 'literal' in p and R_NAOREAL.search(t):
        m.append('nao_real')
    if a.get('atribuicao_palavra') and ('nao_diz' in a.get('atribuicao_origem', []) or R_ENTIDADE.search(t)):
        m.append('entidade')
    if (a.get('atribuicao_palavra') or 'literal' in p) and R_QUEM.search(t):
        m.append('quem')
    if 'bandeira' in (a.get('marcas') or []):
        m.append('bandeira')
    if set(a.get('figura') or []) & {'votos', 'escape'} or ('figurado' in p and not a.get('figura')):
        m.append('figura')
    if ('literal' in p and 'fala_do_sonhar' in p) or re.search(r'de novo|dnv|novamente|outra vez', t, re.I):
        m.append('repeticao')
    return m


def gravar(itens, prefixo):
    lote, tam, k = [], 0, 1
    for x in itens:
        if lote and (tam + len(x['texto']) > LIMITE or len(lote) >= MAX_ITENS):
            (SAIDA / f'{prefixo}_{k}.jsonl').write_text(''.join(json.dumps(y, ensure_ascii=False) + '\n' for y in lote))
            lote, tam, k = [], 0, k + 1
        lote.append(x); tam += len(x['texto'])
    if lote:
        (SAIDA / f'{prefixo}_{k}.jsonl').write_text(''.join(json.dumps(y, ensure_ascii=False) + '\n' for y in lote))
    return k


def main():
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=300)
    SAIDA.mkdir(parents=True, exist_ok=True)
    for p in SAIDA.glob('*.jsonl'):
        if not p.name.endswith('_anotado.jsonl'):
            p.unlink()
    anot = [json.loads(l) for l in open(V34)]
    textos = dict(con.execute(f"SELECT id, texto FROM relatos WHERE id IN ({','.join('?' * len(anot))})",
                              [a['id'] for a in anot]))
    itens = []
    for a in anot:
        m = motivos(a, textos[a['id']])
        if m:
            base = {k: v for k, v in a.items() if k not in ('mudou', 'versao')}
            itens.append({'id': a['id'], 'bolsa': a['bolsa'], 'motivos': m,
                          'anotacao_v34': base, 'texto': textos[a['id']]})
    k = gravar(itens, 'corr')
    print(f'correção: {len(itens)} textos em {k} lotes')
    print(' ', Counter(m for x in itens for m in x['motivos']))

    prova = [{'id': r[0], 'bolsa': 'prova', 'fonte': r[2], 'forma': r[3], 'texto': r[1]} for r in con.execute(
        """SELECT r.id, r.texto, r.fonte, r.forma FROM amostra_prova p JOIN relatos r ON r.id = p.relato_id
           ORDER BY p.rowid""")]
    k = gravar(prova, 'prova')
    print(f'amostra-prova: {len(prova)} textos em {k} lotes (anotar do zero pela v3.5)')


if __name__ == '__main__':
    main()
