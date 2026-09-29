#!/usr/bin/env python3
"""Mede o aluno v3.5 na amostra-prova (gabarito v3.5) e na revisão cega.

Nenhum número sozinho: cada cabeça traz o acerto do modelo ao lado do chute
constante (a combinação mais comum NA PROVA), e cada classe traz n, precisão,
revocação, F1 e o F1 do chute "sempre sim" (2p/(1+p)), que é a linha de base
honesta para F1 de classe.

Cabeças condicionais (carga, conteúdo, despertar, figura, atribuição) são
medidas onde o GABARITO abre a cabeça (literal etc.), não onde o modelo abriu:
mede a cabeça, não o portão de novo.

O aluno antigo (aluno.pt, v3.2, truncado em 192 tokens) roda na mesma prova com
o mesmo gabarito v3.5 — só no portão, que é a única cabeça comparável.

  python3 avaliar_v36.py [--pesos=aluno_v36.pt,...] [--aparelho=mps]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import torch
from transformers import AutoTokenizer

from dados_v35 import (CARGA, CONTEUDO, DESPERTAR, FIGURA, ORIGEM, PORTAO, cega,
                       conectar, prova_v35)
from modelo_v35 import BASE, K_INFER, M, AlunoV35
from treinar_v35 import Textos, prever

AQUI = Path(__file__).parent
L = 0.5


def pct(x):
    return '—' if x is None else f'{100*x:.1f}%'


def por_classe(alvos, preds, nomes):
    """alvos/preds: listas de listas 0/1 (M ignorado)."""
    out = []
    n_tot = len(alvos)
    for c, nome in enumerate(nomes):
        par = [(a[c], p[c]) for a, p in zip(alvos, preds) if a[c] != M]
        vp = sum(1 for a, p in par if a == 1 and p)
        fp = sum(1 for a, p in par if a == 0 and p)
        fn = sum(1 for a, p in par if a == 1 and not p)
        n = vp + fn
        prev = n / max(len(par), 1)
        out.append(dict(classe=nome, n=n, marcados=vp + fp,
                        prec=vp / (vp + fp) if vp + fp else None,
                        rev=vp / n if n else None,
                        f1=2 * vp / (2 * vp + fp + fn) if (2 * vp + fp + fn) else None,
                        f1_sempre_sim=2 * prev / (1 + prev) if n else None))
    return out


def exato(alvos, preds):
    ok = [a == p for a, p in zip(alvos, preds)]
    base = Counter(tuple(a) for a in alvos).most_common(1)[0]
    return sum(ok) / len(ok), base[1] / len(alvos), base[0]


def tabela(titulo, alvos, preds, nomes, linhas_saida):
    ac, b, comb = exato(alvos, preds)
    rot = '+'.join(n for n, x in zip(nomes, comb) if x) or '(nada)'
    linhas_saida.append(f'\n### {titulo}  (n={len(alvos)})\n')
    linhas_saida.append(f'acerto exato {pct(ac)} · chute constante {pct(b)} (`{rot}`)\n')
    linhas_saida.append('| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |')
    linhas_saida.append('|---|---|---|---|---|---|---|')
    res = por_classe(alvos, preds, nomes)
    for r in res:
        linhas_saida.append(f"| {r['classe']} | {r['n']} | {r['marcados']} | {pct(r['prec'])} | "
                            f"{pct(r['rev'])} | {pct(r['f1'])} | {pct(r['f1_sempre_sim'])} |")
    return dict(exato=ac, base=b, classes=res)


def avaliar_modelo(nome_pesos, pv, cg, tk, ap, saida):
    modelo = AlunoV35().to(ap)
    modelo.load_state_dict(torch.load(AQUI / nome_pesos, map_location=ap))
    P = prever(modelo, Textos(pv, tk, K_INFER), ap)
    C = prever(modelo, Textos(cg, tk, K_INFER), ap)
    res = {}
    saida.append(f'\n## {nome_pesos} — AMOSTRA-PROVA ({len(pv)} relatos, gabarito v3.5)\n')

    # portão: linhas com ambiguo ficam fora do exato (candidatas mascaradas)
    idx = [i for i, r in enumerate(pv) if M not in r['portao']]
    amb = len(pv) - len(idx)
    a = [pv[i]['portao'] for i in idx]
    p = [[int(q > L) for q in P['portao'][i]] for i in idx]
    res['portao'] = tabela(f'PORTÃO (fora {amb} ambíguos)', a, p, PORTAO, saida)
    res['portao_pred'] = {pv[i]['id']: p[k] for k, i in enumerate(idx)}

    # literal × não-literal, e por tamanho
    lit = PORTAO.index('literal')
    longos = [k for k, i in enumerate(idx) if len(pv[i]['texto']) > 1000]
    if longos:
        ok = sum(a[k] == p[k] for k in longos)
        saida.append(f'\nportão exato nos {len(longos)} textos >1.000 caracteres: {pct(ok/len(longos))}')

    def cond(cab, nomes, abre):
        ii = [i for i, r in enumerate(pv) if abre(r) and M not in r[cab]]
        if not ii:
            return None
        return tabela(cab.upper() + ' (onde o gabarito abre a cabeça)',
                      [pv[i][cab] for i in ii],
                      [[int(q > L) for q in P[cab][i]] for i in ii], nomes, saida)

    res['carga'] = cond('carga', CARGA, lambda r: True)
    res['despertar'] = cond('despertar', DESPERTAR, lambda r: True)
    res['figura'] = cond('figura', FIGURA, lambda r: True)
    res['origem'] = cond('origem', ORIGEM, lambda r: True)

    ii = [i for i, r in enumerate(pv) if r['conteudo'] != M]
    a = [[int(pv[i]['conteudo'] == c) for c in range(2)] for i in ii]
    p = [[int(max(range(2), key=lambda c: P['conteudo'][i][c]) == c) for c in range(2)] for i in ii]
    res['conteudo'] = tabela('CONTEÚDO (onde o gabarito é literal com conteúdo)', a, p, CONTEUDO, saida)

    for cab in ('tem_atrib', 'bandeira'):
        ii = [i for i, r in enumerate(pv) if r[cab] != M]
        a = [[pv[i][cab]] for i in ii]
        p = [[int(P[cab][i][0] > L)] for i in ii]
        res[cab] = tabela(cab.upper(), a, p, [cab], saida)
        if cab == 'bandeira':
            marc = [pv[i]['id'] for i in ii if P[cab][i][0] > L]
            saida.append(f'\nids marcados com bandeira: {marc}')

    # propaganda × link
    ip = PORTAO.index('propaganda')
    link = [k for k, i in enumerate(idx) if re.search(r'https?://|www\.|R\$', pv[i]['texto'])
            and not pv[i]['portao'][ip]]
    erra = sum(res['portao_pred'][pv[idx[k]]['id']][ip] for k in link)
    saida.append(f'\nconfundidor da propaganda: {len(link)} textos da prova com link/preço e sem '
                 f'propaganda no gabarito; marcados propaganda: {erra}')

    # revisão cega
    saida.append(f'\n## {nome_pesos} — REVISÃO CEGA DO FITIPE ({len(cg)} relatos)\n')
    ifg = PORTAO.index('figurado')
    res['cega'] = cega_medir(cg, [int(q[lit] > L) for q in C['portao']],
                             [int(q[ifg] > L) for q in C['portao']], saida)
    return res


def cega_medir(cg, plit, pfig, saida):
    a = [[r['literal'], r['figurado']] for r in cg]
    p = [[x, y] for x, y in zip(plit, pfig)]
    ac = sum(r[0] == q[0] for r, q in zip(a, p)) / len(a)
    base = max(sum(r[0] for r in a), len(a) - sum(r[0] for r in a)) / len(a)
    saida.append(f'literal × não-literal: acerto {pct(ac)} · chute constante {pct(base)}\n')
    saida.append('| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |')
    saida.append('|---|---|---|---|---|---|---|')
    res = por_classe(a, p, ['literal', 'figurado'])
    for r in res:
        saida.append(f"| {r['classe']} | {r['n']} | {r['marcados']} | {pct(r['prec'])} | "
                     f"{pct(r['rev'])} | {pct(r['f1'])} | {pct(r['f1_sempre_sim'])} |")
    return dict(acerto_literal=ac, base=base, classes=res)


def aluno_antigo(pv, cg, ap, saida):
    """aluno.pt (v3.2) no mesmo gabarito v3.5. Só portão."""
    sys.path.insert(0, str(AQUI))
    from modelo import Aluno
    from treinar import MAX_LEN
    tk = AutoTokenizer.from_pretrained(BASE)
    m = Aluno().to(ap)
    m.load_state_dict(torch.load(AQUI / 'aluno.pt', map_location=ap))
    m.eval()

    def rodar(linhas):
        out = []
        with torch.no_grad():
            for i in range(0, len(linhas), 16):
                e = tk([r['texto'] for r in linhas[i:i + 16]], truncation=True, max_length=MAX_LEN,
                       padding=True, return_tensors='pt')
                s = m(e['input_ids'].to(ap), e['attention_mask'].to(ap))
                out += (torch.sigmoid(s['portao']) > L).int().tolist()
        # a ordem do portão antigo é outra (devaneio antes de fala_do_sonhar)
        from dados import PORTAO as P_ANT
        return [[q[P_ANT.index(k)] for k in PORTAO] for q in out]
    P = rodar(pv)
    C = rodar(cg)
    saida.append('\n## ALUNO ANTIGO (aluno.pt, v3.2) — mesma prova, gabarito v3.5\n')
    idx = [i for i, r in enumerate(pv) if M not in r['portao']]
    a = [pv[i]['portao'] for i in idx]
    p = [P[i] for i in idx]
    res = dict(portao=tabela('PORTÃO', a, p, PORTAO, saida))
    longos = [k for k, i in enumerate(idx) if len(pv[i]['texto']) > 1000]
    if longos:
        saida.append(f'\nportão exato nos {len(longos)} textos >1.000 caracteres: '
                     f'{pct(sum(a[k] == p[k] for k in longos)/len(longos))}')
    saida.append('\n## ALUNO ANTIGO — REVISÃO CEGA\n')
    res['cega'] = cega_medir(cg, [q[0] for q in C], [q[1] for q in C], saida)
    return res


def longos_val(pesos, ap, saida):
    """A prova não tem texto >1.000 caracteres (0 de 300). O ganho das janelas
    só se mede na VALIDAÇÃO (10% do final_v35, nunca treino de nenhum dos dois
    alunos — o antigo treinou em anotacoes_v3, disjunta). Portão, só nas
    células literal/figurado (o antigo tinha outra definição para o resto)."""
    from dados_v35 import conjuntos
    from modelo import Aluno
    from treinar import MAX_LEN
    _, val = conjuntos(False, verbose=False)
    tk = AutoTokenizer.from_pretrained(BASE)
    grupos = dict(curtos=[r for r in val if len(r['texto']) <= 1000],
                  longos=[r for r in val if len(r['texto']) > 1000])
    saida.append('\n## Textos longos — validação (literal e figurado, acerto por célula)\n')
    saida.append('| modelo | curtos (n) | longos (n) |')
    saida.append('|---|---|---|')

    def acerto(linhas, pred):
        ok = n = 0
        for r, p in zip(linhas, pred):
            for c in (0, 1):
                if r['portao'][c] != M:
                    ok += r['portao'][c] == p[c]; n += 1
        return ok / max(n, 1)
    for nome in pesos:
        m = AlunoV35().to(ap)
        m.load_state_dict(torch.load(AQUI / nome, map_location=ap))
        cel = []
        for g, L_ in grupos.items():
            P = prever(m, Textos(L_, tk, K_INFER), ap)
            cel.append(f"{pct(acerto(L_, [[int(q > L) for q in x] for x in P['portao']]))} ({len(L_)})")
        saida.append(f'| {nome} | ' + ' | '.join(cel) + ' |')
    m = Aluno().to(ap)
    m.load_state_dict(torch.load(AQUI / 'aluno.pt', map_location=ap)); m.eval()
    cel = []
    for g, L_ in grupos.items():
        out = []
        with torch.no_grad():
            for i in range(0, len(L_), 16):
                e = tk([r['texto'] for r in L_[i:i + 16]], truncation=True, max_length=MAX_LEN,
                       padding=True, return_tensors='pt')
                s = m(e['input_ids'].to(ap), e['attention_mask'].to(ap))
                out += (torch.sigmoid(s['portao']) > L).int().tolist()
        cel.append(f'{pct(acerto(L_, out))} ({len(L_)})')
    saida.append('| aluno.pt (v3.2, 192 tokens) | ' + ' | '.join(cel) + ' |')


def deriva_v32(con, pv, saida):
    """Quanto o gabarito v3.5 da prova difere do v3.2 dos mesmos 300 (literal e
    figurado). Não é teto: é o tamanho da mudança de régua."""
    v32 = {}
    for rid, l, f in con.execute("""SELECT relato_id, tem_literal, tem_figurado FROM anotacoes_v3
            WHERE anotador LIKE 'claude:v32:%' AND relato_id IN (SELECT relato_id FROM amostra_prova)"""):
        v32[rid] = (int(bool(l)), int(bool(f)))
    par = [(r['portao'][0], r['portao'][1], v32[r['id']]) for r in pv
           if r['id'] in v32 and M not in r['portao'][:2]]
    if par:
        cl = sum(a == b[0] for a, _, b in par) / len(par)
        cf = sum(a == b[1] for _, a, b in par) / len(par)
        saida.append(f'\n## Deriva da régua: gabarito v3.5 × anotação v3.2 dos mesmos relatos (n={len(par)})\n'
                     f'literal coincide em {pct(cl)} · figurado coincide em {pct(cf)}')


def main():
    arg = {a.split('=')[0]: a.split('=')[-1] for a in sys.argv[1:] if '=' in a}
    ap = arg.get('--aparelho', 'mps')
    pesos = arg.get('--pesos', 'aluno_v36.pt').split(',')
    con = conectar()
    pv, n1 = prova_v35(con)
    cg = cega(con)
    tk = AutoTokenizer.from_pretrained(BASE)
    saida = [f'# Avaliação v3.6 — prova {len(pv)} (prova_1: {n1} linhas) · cega {len(cg)}']
    tudo = {}
    for p in pesos:
        tudo[p] = avaliar_modelo(p, pv, cg, tk, ap, saida)
    if '--sem-antigo' not in sys.argv:
        tudo['aluno.pt'] = aluno_antigo(pv, cg, ap, saida)
    deriva_v32(con, pv, saida)
    if '--sem-antigo' not in sys.argv:
        longos_val(pesos, ap, saida)
    txt = '\n'.join(saida)
    print(txt)
    (AQUI / 'avaliacao_v36.md').write_text(txt)
    for v in tudo.values():
        v.pop('portao_pred', None)
    (AQUI / 'avaliacao_v36.json').write_text(json.dumps(tudo, indent=1, default=str))


if __name__ == '__main__':
    main()
