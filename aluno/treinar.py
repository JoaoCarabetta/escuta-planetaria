#!/usr/bin/env python3
"""Treina o aluno, com a máquina do Fitipe em mente.

Ele pediu: sobrecarregar o mínimo, não fechar o Chrome, e oito horas de folga.
Então o padrão aqui é o gentil, não o rápido — lote pequeno, poucas linhas de
execução, e um freio que pausa sozinho se a memória do sistema apertar. Com
umas duas mil amostras, o gentil termina em minutos de qualquer jeito: não há
troca a fazer entre cuidado e tempo nesta escala.

  medir:    python3 treinar.py medir              (quanto custa cada passo)
  treinar:  python3 treinar.py --epocas=6 --lote=8 --aparelho=cpu
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer

from dados import BINARIOS, CARGA, PORTAO, SONHADOR, TOM, conjuntos
from modelo import BASE, Aluno, perda

AQUI = Path(__file__).parent
MAX_LEN = 192          # 99% dos relatos cabem; o corpus é de textos curtos
FOLGA_MIN = 12         # % de memória livre abaixo da qual o treino respira


def memoria_livre():
    """Porcentagem livre segundo o próprio macOS, não a nossa conta."""
    try:
        s = subprocess.run(['memory_pressure'], capture_output=True, text=True,
                           timeout=10).stdout
        for l in s.splitlines():
            if 'free percentage' in l:
                return int(l.split(':')[1].strip().rstrip('%'))
    except Exception:
        pass
    return 100


class Levas(Dataset):
    def __init__(self, linhas, tk):
        self.l, self.tk = linhas, tk

    def __len__(self):
        return len(self.l)

    def __getitem__(self, i):
        r = self.l[i]
        e = self.tk(r['texto'], truncation=True, max_length=MAX_LEN,
                    padding='max_length', return_tensors='pt')
        return dict(
            ids=e['input_ids'][0], mascara=e['attention_mask'][0],
            portao=torch.tensor(r['portao']), tom=torch.tensor(r['tom']),
            carga=torch.tensor(r['carga']), sonhador=torch.tensor(r['sonhador']),
            bin=torch.tensor([r[k] for k in BINARIOS]))


def mover(b, ap):
    return {k: v.to(ap) for k, v in b.items()}


def avaliar(modelo, carregador, ap):
    modelo.eval()
    soma, n = 0.0, 0
    acertos = {k: [0, 0] for k in ('portao', 'carga', 'sonhador')}
    with torch.no_grad():
        for b in carregador:
            b = mover(b, ap)
            s = modelo(b['ids'], b['mascara'])
            l, _ = perda(s, b)
            soma += float(l); n += 1
            pred = (torch.sigmoid(s['portao']) > 0.5).int()
            acertos['portao'][0] += int((pred == b['portao']).all(1).sum())
            acertos['portao'][1] += len(pred)
            for campo in ('carga', 'sonhador'):
                m = b[campo] >= 0
                if m.any():
                    acertos[campo][0] += int((s[campo][m].argmax(1) == b[campo][m]).sum())
                    acertos[campo][1] += int(m.sum())
    modelo.train()
    return soma / max(n, 1), {k: (v[0] / v[1] if v[1] else None) for k, v in acertos.items()}


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    medir = 'medir' in sys.argv
    ap = arg.get('--aparelho', 'cpu')
    lote = int(arg.get('--lote', 8))
    epocas = int(arg.get('--epocas', 6))
    linhas_exec = int(arg.get('--linhas', 4))
    torch.set_num_threads(linhas_exec)
    torch.manual_seed(2015)

    tr, val, pv, hm = conjuntos()
    print(f'treino {len(tr)} · validação {len(val)} · prova {len(pv)} · humano {len(hm)}',
          flush=True)
    tk = AutoTokenizer.from_pretrained(BASE)
    modelo = Aluno().to(ap)
    dtr = DataLoader(Levas(tr, tk), batch_size=lote, shuffle=True)
    dval = DataLoader(Levas(val, tk), batch_size=lote)

    if medir:
        otim = torch.optim.AdamW(modelo.parameters(), lr=2e-5)
        t0, k = time.time(), 0
        for b in dtr:
            b = mover(b, ap)
            l, _ = perda(modelo(b['ids'], b['mascara']), b)
            l.backward(); otim.step(); otim.zero_grad(); k += 1
            if k == 5: break
        dt = (time.time() - t0) / k
        passos = epocas * (len(tr) // lote + 1)
        print(f'{ap} · lote {lote} · {linhas_exec} linhas · {dt:.2f} s/passo · '
              f'{passos} passos = {passos*dt/60:.0f} min · memória livre {memoria_livre()}%')
        return

    otim = torch.optim.AdamW(modelo.parameters(), lr=2e-5, weight_decay=0.01)
    total = epocas * (len(dtr))
    agenda = torch.optim.lr_scheduler.OneCycleLR(otim, max_lr=3e-5, total_steps=total,
                                                 pct_start=0.1)
    melhor, historico = -1.0, []
    for ep in range(1, epocas + 1):
        t0, soma, n = time.time(), 0.0, 0
        for b in dtr:
            if memoria_livre() < FOLGA_MIN:
                print('  memória apertada: pausando 20 s', flush=True)
                time.sleep(20)
            b = mover(b, ap)
            l, _ = perda(modelo(b['ids'], b['mascara']), b)
            l.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            otim.step(); agenda.step(); otim.zero_grad()
            soma += float(l); n += 1
        pv_, ac = avaliar(modelo, dval, ap)
        linha = dict(epoca=ep, treino=soma / n, validacao=pv_,
                     portao=ac['portao'], carga=ac['carga'], sonhador=ac['sonhador'],
                     minutos=(time.time() - t0) / 60, livre=memoria_livre())
        historico.append(linha)
        print(f"época {ep}: treino {linha['treino']:.4f} · validação {pv_:.4f} · "
              f"portão exato {ac['portao']:.3f} · {linha['minutos']:.1f} min · "
              f"livre {linha['livre']}%", flush=True)
        # seleção pelo ACERTO DO PORTÃO, não pela perda total: a perda total é
        # dominada pelas cabeças com muitas classes e poucos exemplos, e o
        # portão pesa pouco nela. Ver `rubrica/desenho-do-treino.md`.
        if ac['portao'] > melhor:
            melhor = ac['portao']
            torch.save(modelo.state_dict(), AQUI / 'aluno.pt')
            print('  ↳ melhor até agora, guardado', flush=True)
        (AQUI / 'historico.json').write_text(json.dumps(historico, indent=1))
    print(f'fim · melhor portão na validação {melhor:.3f} · pesos em aluno.pt', flush=True)


if __name__ == '__main__':
    main()
