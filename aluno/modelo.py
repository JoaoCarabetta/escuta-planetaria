#!/usr/bin/env python3
"""O aluno: BERTimbau com várias cabeças, uma leitura por texto.

Uma passagem pelo texto alimenta todas as cabeças ao mesmo tempo — é por isso
que uma cabeça a mais é quase de graça, e por isso que cortar campo economiza
anotação e não inferência.

  portão    8 saídas independentes (um texto pode ser literal E figurado)
  tom       9 saídas independentes (o anotador marcou mais de uma)
  carga     6 classes exclusivas, só sob literal
  sonhador  3 classes exclusivas, só sob literal
  meta      binária
  bandeira  binária
"""
import torch
import torch.nn as nn
from transformers import AutoModel

from dados import PORTAO, CARGA, TOM, SONHADOR, BINARIOS

BASE = 'neuralmind/bert-base-portuguese-cased'


class Aluno(nn.Module):
    def __init__(self, base=BASE, dropout=0.15):
        super().__init__()
        self.tronco = AutoModel.from_pretrained(base)
        h = self.tronco.config.hidden_size
        self.solta = nn.Dropout(dropout)
        self.portao = nn.Linear(h, len(PORTAO))
        self.tom = nn.Linear(h, len(TOM))
        self.carga = nn.Linear(h, len(CARGA))
        self.sonhador = nn.Linear(h, len(SONHADOR))
        self.bin = nn.Linear(h, len(BINARIOS))

    def forward(self, ids, mascara):
        # média mascarada dos tokens: num corpus de textos muito curtos ela
        # aproveita melhor que o [CLS] sozinho
        saida = self.tronco(input_ids=ids, attention_mask=mascara).last_hidden_state
        m = mascara.unsqueeze(-1).float()
        pool = self.solta((saida * m).sum(1) / m.sum(1).clamp(min=1e-9))
        return dict(portao=self.portao(pool), tom=self.tom(pool),
                    carga=self.carga(pool), sonhador=self.sonhador(pool),
                    bin=self.bin(pool))


def perda(saidas, alvos, pesos=None):
    """Soma das perdas de cada cabeça. Campos não cobertos entram como -100 e
    o ignore_index os descarta — sem isso, o modelo aprenderia que figurado
    tem carga."""
    p = pesos or {}
    bce = nn.BCEWithLogitsLoss()
    ce = nn.CrossEntropyLoss(ignore_index=-100)
    total, partes = 0.0, {}
    for nome, fn, chave in (('portao', bce, 'portao'), ('tom', bce, 'tom'),
                            ('bin', bce, 'bin')):
        l = fn(saidas[chave], alvos[chave].float())
        partes[nome] = l.detach().item(); total = total + p.get(nome, 1.0) * l
    for nome in ('carga', 'sonhador'):
        a = alvos[nome]
        if (a >= 0).any():
            l = ce(saidas[nome], a)
            partes[nome] = l.detach().item(); total = total + p.get(nome, 1.0) * l
        else:
            partes[nome] = 0.0
    return total, partes
