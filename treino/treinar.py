#!/usr/bin/env python3
"""Treina o Laya multilíngue nos julgamentos do qwen (professor → aluno).

Depois do treino, calibra a temperatura na validação e avalia nos 120 do
gabarito humano — a mesma régua usada em todos os modelos até aqui.

Uso: python3 treinar.py [--epocas 3] [--lote 8] [--lr 2e-5] [--so-avaliar]
Pausar: touch PAUSAR_TREINO (salva o estado e sai)
"""
import json
import math
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import torch
import torch.nn.functional as F

import laya
from laya.common import build_sequence, collate_items, render_options
from laya.agent import QTYPES

AQUI = Path(__file__).parent
DADOS = AQUI / 'dados'
PESOS = AQUI / 'laya-sonhario'
BANDEIRA = AQUI / 'PAUSAR_TREINO'
MODELO_BASE = str(AQUI.parent / 'modelos' / 'laya-multilingual')

arg = lambda n, d: type(d)(next((a.split('=')[1] for a in sys.argv if a.startswith(f'--{n}=')), d))
EPOCAS, LOTE, LR = arg('epocas', 3), arg('lote', 8), arg('lr', 2e-5)
random.seed(2015)
torch.manual_seed(2015)


def ler(nome):
    return [json.loads(l) for l in open(DADOS / f'{nome}.jsonl')]


def indice_resposta(opcoes, resposta):
    """Mapeia nosso rótulo ao índice da opção interna do Laya.

    noul  → opções são 'false: ...' / 'true: ...'
    choice→ opções são 'chave: descrição'
    """
    if resposta in ('sim', 'nao'):
        alvo = 'true' if resposta == 'sim' else 'false'
        for i, o in enumerate(opcoes):
            if o.split(':')[0].strip().lower() == alvo:
                return i
        return None
    for i, o in enumerate(opcoes):
        if o.split(':')[0].strip() == resposta:
            return i
    return None


def preparar_lote(ag, itens, perguntas):
    """Monta o batch no mesmo formato que o predict usa, com o alvo."""
    brutos, alvos = [], []
    for it in itens:
        q = ag._to_internal(perguntas[it['pergunta']])
        opcoes = render_options(q)
        seq, markers = build_sequence(ag.tok, {'texto': it['texto']}, q,
                                      ag.cfg.get('max_len', 512),
                                      ag.cfg.get('head_max_len', 192))
        if len(markers) != len(opcoes):
            continue
        alvo = indice_resposta(opcoes, it['resposta'])
        if alvo is None:
            continue
        brutos.append({'ids': seq, 'markers': markers, 'qtype': QTYPES[q['t']]})
        alvos.append(alvo)
    if not brutos:
        return None, None
    b = collate_items([brutos], ag.tok.pad_token_id)
    return b, torch.tensor(alvos)


def rodar_modelo(ag, b):
    return ag.model(b['input_ids'].to(ag.device), b['attention_mask'].to(ag.device),
                    b['marker_pos'].to(ag.device), b['marker_mask'].to(ag.device),
                    b['qtype'].to(ag.device))


def avaliar(ag, itens, perguntas, temp=None, rotulo=''):
    """Acurácia por pergunta + coleta de probabilidades para calibração."""
    ag.model.eval()
    certos = defaultdict(lambda: [0, 0])
    coleta = []
    with torch.no_grad():
        for i in range(0, len(itens), 16):
            fatia = itens[i:i + 16]
            b, alvos = preparar_lote(ag, fatia, perguntas)
            if b is None:
                continue
            logits, _ = rodar_modelo(ag, b)
            logits = logits.float().cpu()
            for j, it in enumerate(fatia[:len(alvos)]):
                q = ag._to_internal(perguntas[it['pergunta']])
                k = len(render_options(q))
                z = logits[j, :k]
                if temp:
                    z = z / temp.get(k, 1.0)
                p = F.softmax(z, dim=-1)
                pred = int(p.argmax())
                ok = pred == int(alvos[j])
                grupo = 'natureza' if it['pergunta'] == 'natureza' else (
                    'qualidades' if it['pergunta'].startswith('q_') else it['pergunta'])
                certos[grupo][0] += ok
                certos[grupo][1] += 1
                coleta.append((k, float(p.max()), ok))
    if rotulo:
        print(f'  [{rotulo}]', ' · '.join(
            f'{g} {100*c[0]/c[1]:.1f}%' for g, c in sorted(certos.items())))
    return certos, coleta


def calibrar(coleta):
    """Ajusta uma temperatura por número de opções (o que o README pede)."""
    temps = {}
    por_k = defaultdict(list)
    for k, p, ok in coleta:
        por_k[k].append((p, ok))
    for k, vals in por_k.items():
        melhor, melhor_ece = 1.0, 9e9
        for t in [0.5 + 0.1 * i for i in range(30)]:
            caixas = defaultdict(lambda: [0, 0])
            for p, ok in vals:
                # reescala a confiança pela temperatura (aproximação monotônica)
                pt = p ** (1 / t)
                pt = pt / (pt + (1 - p) ** (1 / t))
                caixas[min(9, int(pt * 10))][0] += ok
                caixas[min(9, int(pt * 10))][1] += 1
            ece = sum(abs(c[0] / c[1] - (b + .5) / 10) * c[1] for b, c in caixas.items()) / len(vals)
            if ece < melhor_ece:
                melhor, melhor_ece = t, ece
        temps[k] = melhor
        print(f'  {k} opções: temperatura {melhor:.2f} (ECE {melhor_ece:.3f})')
    return temps


def main():
    perguntas = json.load(open(DADOS / 'perguntas.json'))
    treino, validacao, teste = ler('treino'), ler('validacao'), ler('teste')
    print(f'treino {len(treino)} · validação {len(validacao)} · teste {len(teste)}')

    origem = str(PESOS) if (PESOS.exists() and '--so-avaliar' in sys.argv) else MODELO_BASE
    ag = laya.load(origem)
    ag.model.to(ag.device)
    print(f'modelo: {origem} · device {ag.device}')

    if '--so-avaliar' not in sys.argv:
        print('\n— antes do treino —')
        avaliar(ag, teste, perguntas, rotulo='gabarito humano')

        # congela o encoder (95% dos pesos): ele já sabe português; quem aprende
        # a nossa tarefa é a cabeça. 20x menos memória — cabe folgado em 24GB.
        if '--tudo' not in sys.argv:
            for p in ag.model.encoder.parameters():
                p.requires_grad = False
        treinaveis = [p for p in ag.model.parameters() if p.requires_grad]
        print(f'parâmetros treináveis: {sum(p.numel() for p in treinaveis)/1e6:.1f}M '
              f'de {sum(p.numel() for p in ag.model.parameters())/1e6:.0f}M')
        otim = torch.optim.AdamW(treinaveis, lr=LR, weight_decay=0.01)
        passos = EPOCAS * math.ceil(len(treino) / LOTE)
        sched = torch.optim.lr_scheduler.OneCycleLR(otim, max_lr=LR, total_steps=passos,
                                                    pct_start=0.1)
        print(f'\n— treinando: {EPOCAS} épocas, lote {LOTE}, {passos} passos —')
        t0, passo = time.time(), 0
        for ep in range(EPOCAS):
            random.shuffle(treino)
            ag.model.train()
            perdas = []
            for i in range(0, len(treino), LOTE):
                if BANDEIRA.exists():
                    ag.model.save_pretrained(PESOS) if hasattr(ag.model, 'save_pretrained') else \
                        torch.save(ag.model.state_dict(), PESOS / 'model.pt')
                    print('⏸ pausado; estado salvo'); return
                b, alvos = preparar_lote(ag, treino[i:i + LOTE], perguntas)
                if b is None:
                    continue
                logits, _ = rodar_modelo(ag, b)
                # máscara: cada pergunta tem seu número de opções
                perda = 0.0
                for j in range(len(alvos)):
                    k = int(b['marker_mask'][0, j].sum()) if b['marker_mask'].dim() == 3 \
                        else int(b['marker_mask'][j].sum())
                    perda = perda + F.cross_entropy(logits[j, :k].unsqueeze(0).float(),
                                                    alvos[j].unsqueeze(0).to(logits.device))
                perda = perda / max(len(alvos), 1)
                perda.backward()
                torch.nn.utils.clip_grad_norm_(treinaveis, 1.0)
                otim.step(); sched.step(); otim.zero_grad()
                perdas.append(float(perda)); passo += 1
                if passo % 100 == 0:
                    dt = time.time() - t0
                    print(f'  passo {passo}/{passos} · perda {sum(perdas[-100:])/len(perdas[-100:]):.3f} '
                          f'· {passo/dt:.1f} passos/s · resta {(passos-passo)/max(passo/dt,1e-6)/60:.0f} min')
            print(f'época {ep+1}: perda média {sum(perdas)/max(len(perdas),1):.3f}')
            avaliar(ag, teste, perguntas, rotulo=f'gabarito após época {ep+1}')
            PESOS.mkdir(exist_ok=True)
            torch.save(ag.model.state_dict(), PESOS / 'model.pt')
            print(f'  pesos da época {ep+1} salvos')

        PESOS.mkdir(exist_ok=True)
        torch.save(ag.model.state_dict(), PESOS / 'model.pt')
        print(f'\npesos salvos em {PESOS}')

    print('\n— calibrando na validação —')
    _, coleta = avaliar(ag, validacao, perguntas, rotulo='validação (sem calibrar)')
    temps = calibrar(coleta)
    json.dump({str(k): v for k, v in temps.items()}, open(PESOS / 'temperaturas.json', 'w')) \
        if PESOS.exists() else None

    print('\n— AVALIAÇÃO FINAL nos 120 do gabarito humano —')
    avaliar(ag, teste, perguntas, temp=temps, rotulo='FINAL')
    print('\nreferência qwen3.5:9b → natureza 95.8% · sonho 93.3% · desejo 84.2% · sofrim 90.8%')


if __name__ == '__main__':
    main()
