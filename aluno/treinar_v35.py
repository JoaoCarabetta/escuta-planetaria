#!/usr/bin/env python3
"""Treina o aluno v3.5. Não mexe em aluno.pt.

  python3 treinar_v35.py medir [--v3]
  python3 treinar_v35.py --epocas=8 --lote=8 --aparelho=mps [--v3] --saida=aluno_v35_A.pt

Seleção de época (declarada antes de ver qualquer prova): média, na validação,
de portão micro-F1, carga micro-F1, conteúdo acerto, despertar micro-F1, figura
micro-F1, tem_atribuição F1 e origem micro-F1. A bandeira fica FORA do critério
porque a regra dela vai mudar. Paciência de 3 épocas.
"""
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer

from dados_v35 import conjuntos
from modelo_v35 import (BASE, BIN, K_INFER, K_TREINO, M, MULTI, SAIDAS, AlunoV35,
                        janelas_de, perda)

AQUI = Path(__file__).parent
FOLGA_MIN = 12
PESO_V3 = 0.5


def memoria_livre():
    try:
        s = subprocess.run(['memory_pressure'], capture_output=True, text=True, timeout=10).stdout
        for l in s.splitlines():
            if 'free percentage' in l:
                return int(l.split(':')[1].strip().rstrip('%'))
    except Exception:
        pass
    return 100


class Textos(Dataset):
    def __init__(self, linhas, tk, k):
        self.l, self.tk, self.k = linhas, tk, k
        self.jan = []
        for r in linhas:
            ids = tk(r['texto'], add_special_tokens=False)['input_ids']
            self.jan.append(janelas_de(ids, tk, k))

    def __len__(self):
        return len(self.l)

    def __getitem__(self, i):
        return i


def coletor(ds):
    tk = ds.tk
    cls, sep, pad = tk.cls_token_id, tk.sep_token_id, tk.pad_token_id

    def f(idx):
        jans, dono = [], []
        for n, i in enumerate(idx):
            for j in ds.jan[i]:
                jans.append([cls] + j + [sep]); dono.append(n)
        T = max(len(j) for j in jans)
        ids = torch.full((len(jans), T), pad, dtype=torch.long)
        mas = torch.zeros((len(jans), T), dtype=torch.long)
        for w, j in enumerate(jans):
            ids[w, :len(j)] = torch.tensor(j); mas[w, :len(j)] = 1
        L = [ds.l[i] for i in idx]
        b = dict(ids=ids, mascara=mas, dono=torch.tensor(dono), n=len(idx))
        for k in SAIDAS:
            if all(k in r for r in L):          # a revisão cega não tem rótulos v3.5
                b[k] = torch.tensor([r[k] for r in L])
        b['peso'] = torch.tensor([PESO_V3 if r.get('origem_rot') == 'v3' else 1.0 for r in L])
        b['idx'] = torch.tensor(idx)
        return b
    return f


def mover(b, ap):
    return {k: (v.to(ap) if torch.is_tensor(v) else v) for k, v in b.items()}


def pesos_positivos(tr, ap):
    """sqrt(neg/pos), entre 1 e 10: empurra os raros sem transformar o limiar
    0,5 em 'sim para tudo'."""
    pp = {}
    for k in MULTI + BIN:
        cols = [r[k] if isinstance(r[k], list) else [r[k]] for r in tr]
        n = len(cols[0])
        w = []
        for c in range(n):
            pos = sum(1 for x in cols if x[c] == 1)
            neg = sum(1 for x in cols if x[c] == 0)
            w.append(min(10.0, max(1.0, math.sqrt(neg / max(pos, 1)))))
        pp[k] = torch.tensor(w, device=ap)
    c = [sum(1 for r in tr if r['conteudo'] == v) for v in (0, 1)]
    tot = sum(c)
    pp['conteudo'] = torch.tensor([min(10.0, math.sqrt(tot / (2 * max(x, 1)))) for x in c],
                                  device=ap)
    return pp


def prever(modelo, ds, ap, lote=8):
    """Probabilidades por cabeça, na ordem do ds."""
    modelo.eval()
    dl = DataLoader(ds, batch_size=lote, collate_fn=coletor(ds))
    out = {k: [] for k in SAIDAS}
    with torch.no_grad():
        for b in dl:
            b = mover(b, ap)
            s = modelo(b['ids'], b['mascara'], b['dono'], b['n'])
            for k in SAIDAS:
                p = torch.softmax(s[k], -1) if k == 'conteudo' else torch.sigmoid(s[k])
                out[k] += p.cpu().tolist()
    modelo.train()
    return out


def f1_micro(alvo, prob, lim=0.5):
    vp = fp = fn = 0
    for a, p in zip(alvo, prob):
        a = a if isinstance(a, list) else [a]
        for x, q in zip(a, p):
            if x == M:
                continue
            y = q > lim
            vp += x == 1 and y; fp += x == 0 and y; fn += x == 1 and not y
    return 2 * vp / max(2 * vp + fp + fn, 1)


def medidas_val(linhas, prob):
    m = {}
    for k in MULTI + BIN:
        m[k] = f1_micro([r[k] for r in linhas], prob[k])
    ok = [(r['conteudo'], p) for r, p in zip(linhas, prob['conteudo']) if r['conteudo'] != M]
    m['conteudo'] = sum(a == max(range(2), key=lambda i: p[i]) for a, p in ok) / max(len(ok), 1)
    ex = [r for r in zip(linhas, prob['portao']) if M not in r[0]['portao']]
    m['portao_exato'] = sum(r['portao'] == [int(q > .5) for q in p] for r, p in ex) / max(len(ex), 1)
    crit = ['portao', 'carga', 'conteudo', 'despertar', 'figura', 'tem_atrib', 'origem']
    m['criterio'] = sum(m[k] for k in crit) / len(crit)
    return m


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    ap = arg.get('--aparelho', 'mps')
    lote = int(arg.get('--lote', 8))
    epocas = int(arg.get('--epocas', 8))
    paciencia = int(arg.get('--paciencia', 3))
    saida = AQUI / arg.get('--saida', 'aluno_v35.pt')
    usar_v3 = '--v3' in sys.argv
    torch.manual_seed(2015)
    torch.set_num_threads(4)

    tr, val = conjuntos(usar_v3)
    tk = AutoTokenizer.from_pretrained(BASE)
    t0 = time.time()
    dtr_ds, dval_ds = Textos(tr, tk, K_TREINO), Textos(val, tk, K_INFER)
    nj = [len(j) for j in dtr_ds.jan]
    print(f'janelas: treino {sum(nj)} para {len(nj)} textos ({sum(n > 1 for n in nj)} com >1) · '
          f'tokenização {time.time()-t0:.0f}s', flush=True)
    modelo = AlunoV35().to(ap)
    pp = pesos_positivos(tr, ap)
    print('pesos positivos:', {k: [round(x, 1) for x in v.tolist()] for k, v in pp.items()}, flush=True)
    dtr = DataLoader(dtr_ds, batch_size=lote, shuffle=True, collate_fn=coletor(dtr_ds))

    if 'medir' in sys.argv:
        otim = torch.optim.AdamW(modelo.parameters(), lr=2e-5)
        t0, k = time.time(), 0
        for b in dtr:
            b = mover(b, ap)
            l, _ = perda(modelo(b['ids'], b['mascara'], b['dono'], b['n']), b, pp, b['peso'])
            l.backward(); otim.step(); otim.zero_grad(); k += 1
            if k == 20:
                break
        dt = (time.time() - t0) / k
        print(f'{ap} · lote {lote} · {dt:.2f} s/passo · {len(dtr)} passos/época = '
              f'{len(dtr)*dt/60:.1f} min/época · livre {memoria_livre()}%', flush=True)
        return

    otim = torch.optim.AdamW(modelo.parameters(), lr=2e-5, weight_decay=0.01)
    agenda = torch.optim.lr_scheduler.OneCycleLR(otim, max_lr=3e-5, total_steps=epocas * len(dtr),
                                                 pct_start=0.1)
    melhor, sem_melhora, hist = -1.0, 0, []
    for ep in range(1, epocas + 1):
        t0, soma, n = time.time(), 0.0, 0
        for b in dtr:
            if n % 50 == 0 and ap == 'mps':
                # janelas de tamanho variável fragmentam o cache do MPS; a
                # corrida B morreu por falta de memória na época 4 sem isto
                torch.mps.empty_cache()
            if n % 50 == 0 and memoria_livre() < FOLGA_MIN:
                print('  memória apertada: pausando 20 s', flush=True)
                time.sleep(20)
            b = mover(b, ap)
            l, _ = perda(modelo(b['ids'], b['mascara'], b['dono'], b['n']), b, pp, b['peso'])
            l.backward()
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            otim.step(); agenda.step(); otim.zero_grad()
            soma += float(l); n += 1
            if n % 200 == 0:
                print(f'  passo {n}/{len(dtr)} · perda {soma/n:.4f}', flush=True)
        m = medidas_val(val, prever(modelo, dval_ds, ap))
        linha = dict(epoca=ep, treino=soma / n, minutos=(time.time() - t0) / 60, **m)
        hist.append(linha)
        print(f"época {ep}: treino {linha['treino']:.4f} · critério {m['criterio']:.3f} · "
              f"portão exato {m['portao_exato']:.3f} · " +
              ' · '.join(f'{k} {m[k]:.2f}' for k in ('portao', 'carga', 'conteudo', 'despertar',
                                                      'figura', 'tem_atrib', 'origem', 'bandeira')) +
              f" · {linha['minutos']:.1f} min", flush=True)
        if m['criterio'] > melhor:
            melhor, sem_melhora = m['criterio'], 0
            torch.save(modelo.state_dict(), saida)
            print(f'  ↳ melhor até agora, guardado em {saida.name}', flush=True)
        else:
            sem_melhora += 1
        (AQUI / (saida.stem + '_historico.json')).write_text(json.dumps(hist, indent=1))
        if sem_melhora >= paciencia:
            print('  paciência esgotada', flush=True)
            break
    print(f'fim · melhor critério na validação {melhor:.3f} · {saida.name}', flush=True)


if __name__ == '__main__':
    main()
