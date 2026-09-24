#!/usr/bin/env python3
"""O aluno no lugar do qwen, dentro do moinho.

O passo caro do moinho era a anotação pelo modelo generativo: ~1,1 s por texto,
o que punha os 335 mil pendentes em quatro dias. O classificador faz o mesmo
julgamento em ~25 ms, e com 91% de acerto contra um teto humano de 93% —
medido em 300 relatos sorteados que ele nunca viu.

O que ele NÃO faz: `desejo`, `sofrimento` e as qualidades da v2.1, que o qwen
inventava com a rubrica velha e que a v3.2 substituiu. Esses campos passam a
sair vazios, e é ganho: eram justamente os que a retro-avaliação mostrou
errados em 1 de cada 5 casos.
"""
import json
from pathlib import Path

import torch
from transformers import AutoTokenizer

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'aluno'))
from dados import CARGA, PORTAO          # noqa: E402
from modelo import BASE, Aluno           # noqa: E402

_estado = {}


def _carregar():
    if _estado:
        return _estado
    torch.set_num_threads(4)
    m = Aluno()
    m.load_state_dict(torch.load(Path(__file__).parent.parent / 'aluno' / 'aluno.pt',
                                 map_location='cpu'))
    m.eval()
    _estado['modelo'] = m
    _estado['tk'] = AutoTokenizer.from_pretrained(BASE)
    return _estado


def anotar(texto):
    """Devolve (natureza, tem_sonho_dormido, extra) para o moinho.

    O mapeamento para o vocabulário da v2.1 existe só para o planeta continuar
    funcionando sem ser reescrito; o julgamento rico vai inteiro no `extra`.
    Na dúvida o texto entra como 'relato' — regra do Fitipe: descartar exige
    justificativa, e o arquivo perde as bordas se a máquina descartar sozinha.
    """
    e = _carregar()
    t = e['tk'](texto[:2000], truncation=True, max_length=192, return_tensors='pt')
    with torch.no_grad():
        s = e['modelo'](t['input_ids'], t['attention_mask'])
    p = torch.sigmoid(s['portao'])[0]
    portao = [PORTAO[i] for i in range(len(PORTAO)) if p[i] > 0.5]

    if 'descartavel' in portao:            nat = 'ruido'
    elif 'fala_do_sonhar' in portao:       nat = 'meta'
    elif 'literal' in portao:              nat = 'relato'
    elif 'figurado' in portao:             nat = 'idiomatico'
    else:                                  nat = 'relato'      # indeciso fica

    literal = 'literal' in portao
    tem_c = int(torch.softmax(s['conteudo'], 1)[0].argmax()) if literal else None
    extra = dict(portao=portao, tem_conteudo=tem_c,
                 carga=(CARGA[int(torch.softmax(s['carga'], 1)[0].argmax())]
                        if (literal and tem_c == 1) else None),
                 p_literal=float(p[0]), p_figurado=float(p[1]),
                 margem=float((p - 0.5).abs().min()))
    return nat, int(literal), extra
