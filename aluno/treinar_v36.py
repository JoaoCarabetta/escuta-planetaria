#!/usr/bin/env python3
"""Treina o aluno v3.6 — final_v35 + afeto15k + raros_enxuto (ver dados_v36.py).
Não mexe em aluno_v35.pt, dados_v35.py nem treinar_v35.py. Cópia adaptada de
treinar_v35.py: mesmo modelo (modelo_v35.AlunoV35), mesmo laço de treino,
mesmo critério de seleção de época (só a validação do final_v35, 10%, decide;
a bandeira fica fora do critério, igual v3.5). A validação extra do
raros_enxuto (10%, estratificada por lote) é só medida a cada época — não
decide nada, como pedido.

  python3 treinar_v36.py medir [--v3]
  python3 treinar_v36.py --teste=200          # ensaio rápido, 1 época, ponta a ponta
  python3 treinar_v36.py --epocas=8 --lote=8 --aparelho=mps --saida=aluno_v36.pt
"""
import json
import random
import sys
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from dados_v36 import CABECAS, contar, conjuntos_v36
from modelo_v35 import K_INFER, K_TREINO, SAIDAS, AlunoV35
from treinar_v35 import (Textos, coletor, medidas_val, memoria_livre, mover,
                         pesos_positivos, prever)

AQUI = Path(__file__).parent
FOLGA_MIN = 12


def relatar_contagens(tr, val, val_raros, rel):
    print('\n=== junção v3.6 ===')
    print(json.dumps(rel, indent=1, ensure_ascii=False), flush=True)
    for nome, linhas in (('treino v3.6', tr), ('validação (decide época)', val),
                         ('validação extra raros (só medida)', val_raros)):
        print(f'\n-- {nome} (n={len(linhas)}) --')
        for cab, nomes in CABECAS.items():
            print(' ', cab, dict(contar(linhas, cab, nomes)))
        print('  conteudo', dict(__import__('collections').Counter(r['conteudo'] for r in linhas)))
        print('  tem_atrib', dict(__import__('collections').Counter(r['tem_atrib'] for r in linhas)),
              'bandeira', dict(__import__('collections').Counter(r['bandeira'] for r in linhas)))
    sys.stdout.flush()


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    ap = arg.get('--aparelho', 'mps')
    lote = int(arg.get('--lote', 8))
    epocas = int(arg.get('--epocas', 8))
    paciencia = int(arg.get('--paciencia', 3))
    saida = AQUI / arg.get('--saida', 'aluno_v36.pt')
    usar_v3 = '--v3' in sys.argv
    teste = int(arg['--teste']) if '--teste' in arg else None
    torch.manual_seed(2015)
    torch.set_num_threads(4)

    tr, val, val_raros, rel = conjuntos_v36(usar_v3, verbose=True)

    if teste:
        rng = random.Random(2015)
        tr = rng.sample(tr, min(teste, len(tr)))
        val = val[:min(50, len(val))]
        val_raros = val_raros[:min(50, len(val_raros))]
        epocas = 1
        print(f'\n*** MODO TESTE: treino reduzido a {len(tr)} · val {len(val)} · '
              f'val_raros {len(val_raros)} · 1 época ***', flush=True)

    relatar_contagens(tr, val, val_raros, rel)

    tk = __import__('transformers').AutoTokenizer.from_pretrained(
        __import__('modelo_v35').BASE)
    t0 = time.time()
    dtr_ds = Textos(tr, tk, K_TREINO)
    dval_ds = Textos(val, tk, K_INFER)
    dval_raros_ds = Textos(val_raros, tk, K_INFER)
    nj = [len(j) for j in dtr_ds.jan]
    print(f'janelas: treino {sum(nj)} para {len(nj)} textos ({sum(n > 1 for n in nj)} com >1) · '
          f'tokenização {time.time()-t0:.0f}s', flush=True)

    modelo = AlunoV35().to(ap)
    pp = pesos_positivos(tr, ap)
    print('pesos positivos:', {k: [round(x, 1) for x in v.tolist()] for k, v in pp.items()}, flush=True)
    dtr = DataLoader(dtr_ds, batch_size=lote, shuffle=True, collate_fn=coletor(dtr_ds))

    from modelo_v35 import perda

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
        m_raros = medidas_val(val_raros, prever(modelo, dval_raros_ds, ap)) if val_raros else {}
        linha = dict(epoca=ep, treino=soma / n, minutos=(time.time() - t0) / 60, **m,
                    raros_criterio=m_raros.get('criterio'))
        hist.append(linha)
        print(f"época {ep}: treino {linha['treino']:.4f} · critério {m['criterio']:.3f} · "
              f"portão exato {m['portao_exato']:.3f} · " +
              ' · '.join(f'{k} {m[k]:.2f}' for k in ('portao', 'carga', 'conteudo', 'despertar',
                                                      'figura', 'tem_atrib', 'origem', 'bandeira')) +
              f" · {linha['minutos']:.1f} min", flush=True)
        if m_raros:
            print(f"  [extra] raros_enxuto: critério {m_raros['criterio']:.3f} · " +
                  ' · '.join(f'{k} {m_raros[k]:.2f}' for k in ('portao', 'carga', 'conteudo',
                                                                'despertar', 'figura', 'tem_atrib',
                                                                'origem', 'bandeira')), flush=True)
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
