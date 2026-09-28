#!/usr/bin/env python3
"""O aluno v3.5: BERTimbau, leitura em janelas, oito cabeças.

JANELAS em vez de truncar. 25% do material de treino passa de 1.600 caracteres
e 10% de 3.100; o aluno antigo cortava em 192 tokens (~800 caracteres) e não via
o resto. O que o `testar_janelas.py` ensinou (com bge-m3, não com o BERT) é que
a MÉDIA de muitas janelas puxa o vetor para o centro: o texto longo vira "texto
genérico". Por isso aqui a agregação não é média: é atenção aprendida sobre as
janelas (um escore por janela, softmax dentro do texto). A janela onde está o
"sonhei" pode dominar sozinha; num texto de uma janela só, é identidade.

  janela: 256 tokens (254 + [CLS]/[SEP]), passo 200 (sobreposição de 54)
  treino: até 4 janelas por texto; inferência: até 12
  prioridade: a primeira janela sempre; depois as que contêm "sonh"/"pesadel";
  depois as demais, espaçadas. A ordem original é mantida.

Cabeças:
  portao     8 sigmoides (combinável)
  carga      5 sigmoides (estranha combina com valência) — só literal
  conteudo   2 classes exclusivas — só literal
  despertar  6 sigmoides; tudo zero = não fala do acordar — só literal
  figura     4 sigmoides — só figurado
  tem_atrib  1 sigmoide — só literal/fala_do_sonhar
  origem     7 sigmoides — só onde há atribuição
  bandeira   1 sigmoide — todo texto
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel

from dados_v35 import CARGA, CONTEUDO, DESPERTAR, FIGURA, ORIGEM, PORTAO

BASE = 'neuralmind/bert-base-portuguese-cased'
JANELA = 254
PASSO = 200
K_TREINO = 4
K_INFER = 12
M = -100

SAIDAS = dict(portao=len(PORTAO), carga=len(CARGA), conteudo=len(CONTEUDO),
              despertar=len(DESPERTAR), figura=len(FIGURA), tem_atrib=1,
              origem=len(ORIGEM), bandeira=1)
MULTI = ['portao', 'carga', 'despertar', 'figura', 'origem']
BIN = ['tem_atrib', 'bandeira']


def janelas_de(ids_tok, tk, k):
    """ids sem tokens especiais → lista de janelas (listas de ids), no máximo k."""
    if len(ids_tok) <= JANELA:
        return [ids_tok]
    jans = []
    for ini in range(0, len(ids_tok), PASSO):
        jans.append(ids_tok[ini:ini + JANELA])
        if ini + JANELA >= len(ids_tok):
            break
    if len(jans) <= k:
        return jans
    chave = [i for i, j in enumerate(jans) if i > 0 and any(
        p in tk.decode(j).lower() for p in ('sonh', 'pesadel'))]
    outras = [i for i in range(1, len(jans)) if i not in chave]

    def espalha(lista, n):
        if n <= 0 or not lista:
            return []
        if len(lista) <= n:
            return lista
        return [lista[round(t * (len(lista) - 1) / max(n - 1, 1))] for t in range(n)]
    esc = [0] + espalha(chave, k - 1)
    esc += espalha(outras, k - len(esc))
    return [jans[i] for i in sorted(set(esc))]


class AlunoV35(nn.Module):
    def __init__(self, base=BASE, dropout=0.15):
        super().__init__()
        self.tronco = AutoModel.from_pretrained(base)
        h = self.tronco.config.hidden_size
        self.escore = nn.Linear(h, 1)
        self.solta = nn.Dropout(dropout)
        self.cab = nn.ModuleDict({k: nn.Linear(h, n) for k, n in SAIDAS.items()})

    def forward(self, ids, mascara, dono, n_textos):
        """ids/mascara: [W, T] todas as janelas do lote; dono: [W] índice do
        texto de cada janela."""
        s = self.tronco(input_ids=ids, attention_mask=mascara).last_hidden_state
        m = mascara.unsqueeze(-1).float()
        jan = (s * m).sum(1) / m.sum(1).clamp(min=1e-9)          # [W, h]
        e = self.escore(jan).squeeze(-1)                           # [W]
        # softmax por texto
        # softmax é invariante a deslocamento: basta o máximo global (o escore
        # é limitado; scatter_reduce/amax não é confiável no MPS)
        w = torch.exp((e - e.max()).clamp(min=-60))
        soma = torch.zeros(n_textos, device=e.device).index_add(0, dono, w)
        w = w / soma[dono]
        txt = torch.zeros(n_textos, jan.shape[1], device=e.device).index_add(
            0, dono, jan * w.unsqueeze(-1))
        txt = self.solta(txt)
        return {k: c(txt) for k, c in self.cab.items()}


def perda(saidas, alvos, pesos_pos, peso_amostra=None, pesos_cab=None):
    """Máscara célula a célula (-100). pesos_pos: {cabeça: tensor [n]} para
    BCE; para conteudo, pesos de classe da CE. peso_amostra: [B] (a v3 pesa
    menos)."""
    pc = pesos_cab or {}
    total, partes = 0.0, {}
    B = saidas['portao'].shape[0]
    wa = peso_amostra if peso_amostra is not None else torch.ones(B, device=saidas['portao'].device)
    for k in MULTI + BIN:
        y = alvos[k].float()
        if y.dim() == 1:
            y = y.unsqueeze(-1)
        x = saidas[k]
        valido = (y != M).float()
        if valido.sum() == 0:
            partes[k] = 0.0
            continue
        l = F.binary_cross_entropy_with_logits(x, y.clamp(min=0), reduction='none',
                                               pos_weight=pesos_pos[k])
        l = l * valido * wa.unsqueeze(-1)
        l = l.sum() / (valido * wa.unsqueeze(-1)).sum().clamp(min=1e-9)
        partes[k] = float(l.detach())
        total = total + pc.get(k, 1.0) * l
    y = alvos['conteudo']
    if (y != M).any():
        l = F.cross_entropy(saidas['conteudo'], y, weight=pesos_pos['conteudo'],
                            ignore_index=M)
        partes['conteudo'] = float(l.detach())
        total = total + pc.get('conteudo', 1.0) * l
    else:
        partes['conteudo'] = 0.0
    return total, partes
