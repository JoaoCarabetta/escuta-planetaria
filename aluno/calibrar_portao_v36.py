#!/usr/bin/env python3
"""Calibra o corte do portão do v3.6 (só validação de 344, semente 2015) e
compara v3.5 × v3.6 cru × v3.6 calibrado na prova (300) e na cega (83).
Só LÊ o banco (mode=ro). Não reinfere: usa p_portao gravado em predicoes_v36.

  python3 calibrar_portao_v36.py     → imprime tudo e grava ../rubrica/medidas/portao_v35_v36_calibrado.md
                                       e limiar_portao_v36.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

from dados_v35 import M, PORTAO, cega, conectar, conjuntos, prova_v35

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
L = 0.5
LIT, FIG = 0, 1


def pct(x):
    return '—' if x is None else f'{100*x:.1f}%'


def carregar(con, ids, tabela):
    out = {}
    ids = list(ids)
    for i in range(0, len(ids), 900):
        p = ids[i:i + 900]
        q = ','.join('?' * len(p))
        for rid, pj, dec in con.execute(f'SELECT relato_id, p_portao, portao FROM {tabela} WHERE relato_id IN ({q})', p):
            out[rid] = (json.loads(pj) if pj else None, json.loads(dec) if dec else [])
    return out


def vetor(dec):
    return [int(n in dec) for n in PORTAO]


def vetor_cal(pp, tl, tf):
    v = [int(pp[n] > L) for n in PORTAO]
    v[LIT] = int(pp['literal'] > tl)
    v[FIG] = int(pp['figurado'] > tf)
    return v


def exato(alvos, preds):
    ac = sum(a == p for a, p in zip(alvos, preds)) / len(alvos)
    base = Counter(tuple(a) for a in alvos).most_common(1)[0]
    return ac, base[1] / len(alvos), base[0]


def por_classe(alvos, preds, nomes):
    out = []
    for c, nome in enumerate(nomes):
        par = [(a[c], p[c]) for a, p in zip(alvos, preds) if a[c] != M]
        vp = sum(1 for a, p in par if a == 1 and p)
        fp = sum(1 for a, p in par if a == 0 and p)
        fn = sum(1 for a, p in par if a == 1 and not p)
        n = vp + fn
        out.append(dict(classe=nome, n=n, marc=vp + fp, prec=vp / (vp + fp) if vp + fp else None,
                        rev=vp / n if n else None,
                        f1=2 * vp / (2 * vp + fp + fn) if (2 * vp + fp + fn) else None))
    return out


def linhas_classe(res):
    o = ['| classe | n | marcados | precisão | revocação | F1 |', '|---|---|---|---|---|---|']
    for r in res:
        o.append(f"| {r['classe']} | {r['n']} | {r['marc']} | {pct(r['prec'])} | {pct(r['rev'])} | {pct(r['f1'])} |")
    return o


def main():
    con = conectar()
    tr, val = conjuntos(False, verbose=False)
    pv, _ = prova_v35(con)
    cg = cega(con)
    S = []

    # ---------- validação 344 ----------
    vv = [r for r in val if M not in r['portao']]
    pr36 = carregar(con, [r['id'] for r in val], 'predicoes_v36')
    faltam = [r['id'] for r in vv if r['id'] not in pr36]
    assert not faltam, faltam
    A = [r['portao'] for r in vv]
    PP = [pr36[r['id']][0] for r in vv]
    n_lit = sum(a[LIT] for a in A)
    taxa_real = n_lit / len(A)
    S.append(f'validação: {len(val)} linhas, {len(vv)} sem ambíguo · literal real {n_lit} ({pct(taxa_real)}) · '
             f'figurado real {sum(a[FIG] for a in A)}')

    grade = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    curva_lit = []
    for t in grade:
        pred = [vetor_cal(p, t, L) for p in PP]
        ac = sum(a == q for a, q in zip(A, pred)) / len(A)
        marc = sum(q[LIT] for q in pred)
        acl = sum(a[LIT] == q[LIT] for a, q in zip(A, pred)) / len(A)
        curva_lit.append((t, ac, acl, marc, marc / len(A)))
    # limiar fino para escolher (passo 0,01)
    fino = []
    for k in range(20, 100):
        t = k / 100
        pred = [vetor_cal(p, t, L) for p in PP]
        ac = sum(a == q for a, q in zip(A, pred)) / len(A)
        marc = sum(q[LIT] for q in pred)
        fino.append((t, ac, marc))
    melhor = max(a for _, a, _ in fino)
    empatados = [t for t, a, _ in fino if abs(a - melhor) < 1e-12]
    # plateau: mediana dos limiares empatados (menos sensível a ruído de um caso)
    t_ac = empatados[len(empatados) // 2]
    t_ac_min, t_ac_max = min(empatados), max(empatados)
    # limiar que iguala a taxa marcada à real
    t_taxa = min(fino, key=lambda x: (abs(x[2] - n_lit), abs(x[0] - 0.5)))[0]
    marc_taxa = [m for t, _, m in fino if t == t_taxa][0]
    ac_taxa = [a for t, a, _ in fino if t == t_taxa][0]
    S.append(f'limiar máx. acerto exato (literal): {t_ac} (platô {t_ac_min}-{t_ac_max}) acerto {pct(melhor)}')
    S.append(f'limiar taxa marcada = real: {t_taxa} marca {marc_taxa}/{len(A)} acerto {pct(ac_taxa)}')

    # figurado
    curva_fig = []
    for tf in grade:
        pred = [vetor_cal(p, t_ac, tf) for p in PP]
        ac = sum(a == q for a, q in zip(A, pred)) / len(A)
        curva_fig.append((tf, ac, sum(q[FIG] for q in pred)))
    fino_f = []
    for k in range(20, 96):
        tf = k / 100
        pred = [vetor_cal(p, t_ac, tf) for p in PP]
        fino_f.append((tf, sum(a == q for a, q in zip(A, pred)) / len(A)))
    melhor_f = max(a for _, a in fino_f)
    emp_f = [t for t, a in fino_f if abs(a - melhor_f) < 1e-12]
    ac_f05 = [a for t, a in fino_f if t == 0.5][0]
    S.append(f'figurado: melhor {pct(melhor_f)} em {emp_f[0]}-{emp_f[-1]} · em 0,50: {pct(ac_f05)}')
    # só troca o limiar do figurado se ganhar >= 5 casos (1,5 pt) sobre 0,5; menos é ruído em n=342
    n_ganho_f = round((melhor_f - ac_f05) * len(A))
    t_fig = L if n_ganho_f < 5 else emp_f[len(emp_f) // 2]
    S.append(f'ganho do figurado sobre 0,5: {n_ganho_f} casos → t_fig = {t_fig}')

    # cru na validação
    cru = [vetor(pr36[r['id']][1]) for r in vv]
    ac_cru = sum(a == q for a, q in zip(A, cru)) / len(A)
    m_cru = sum(q[LIT] for q in cru)
    pred_c = [vetor_cal(p, t_ac, t_fig) for p in PP]
    ac_c = sum(a == q for a, q in zip(A, pred_c)) / len(A)
    pr35 = carregar(con, [r['id'] for r in val], 'predicoes_v35')
    v35v = [vetor(pr35[r['id']][1]) for r in vv if r['id'] in pr35]
    S.append(f'validação: v3.6 cru {pct(ac_cru)} (literal marcado {m_cru}) · calibrado {pct(ac_c)}')

    # ---------- prova 300 ----------
    pvv = [r for r in pv if M not in r['portao']]
    P36 = carregar(con, [r['id'] for r in pvv], 'predicoes_v36')
    P35 = carregar(con, [r['id'] for r in pvv], 'predicoes_v35')
    Ap = [r['portao'] for r in pvv]
    pred_p = dict(
        v35=[vetor(P35[r['id']][1]) for r in pvv],
        v36cru=[vetor(P36[r['id']][1]) for r in pvv],
        v36cal=[vetor_cal(P36[r['id']][0], t_ac, t_fig) for r in pvv],
        v36taxa=[vetor_cal(P36[r['id']][0], t_taxa, L) for r in pvv])
    curva_prova = []
    for t in (0.5, 0.55, 0.6, 0.66, 0.7, 0.75, 0.8, 0.85):
        pr = [vetor_cal(P36[r['id']][0], t, L) for r in pvv]
        curva_prova.append((t, sum(a == q for a, q in zip(Ap, pr)) / len(Ap), sum(q[LIT] for q in pr)))
    # ---------- cega ----------
    P36c = carregar(con, [r['id'] for r in cg], 'predicoes_v36')
    P35c = carregar(con, [r['id'] for r in cg], 'predicoes_v35')
    Ac = [[r['literal'], r['figurado']] for r in cg]
    pred_c2 = dict(
        v35=[[int('literal' in P35c[r['id']][1]), int('figurado' in P35c[r['id']][1])] for r in cg],
        v36cru=[[int('literal' in P36c[r['id']][1]), int('figurado' in P36c[r['id']][1])] for r in cg],
        v36cal=[[int(P36c[r['id']][0]['literal'] > t_ac), int(P36c[r['id']][0]['figurado'] > t_fig)] for r in cg],
        v36taxa=[[int(P36c[r['id']][0]['literal'] > t_taxa), int(P36c[r['id']][0]['figurado'] > L)] for r in cg])

    # ---------- arquivo inteiro ----------
    tot = {}
    for nome, tab in (('v35', 'predicoes_v35'), ('v36cru', 'predicoes_v36')):
        n, l, f = con.execute(f"""SELECT count(*), sum(portao LIKE '%"literal"%'), sum(portao LIKE '%"figurado"%')
                                  FROM {tab}""").fetchone()
        tot[nome] = (n, l, f)
    # calibrado: p_literal > t (json extract não necessário: colunas p_literal)
    n, l, f = con.execute('SELECT count(*), sum(p_literal > ?), sum(p_figurado > ?) FROM predicoes_v36', (t_ac, t_fig)).fetchone()
    tot['v36cal'] = (n, l, f)
    n, l, f = con.execute('SELECT count(*), sum(p_literal > ?), sum(p_figurado > ?) FROM predicoes_v36', (t_taxa, L)).fetchone()
    tot['v36taxa'] = (n, l, f)
    # conjunto comum (ids em ambos) para comparação justa
    comum = con.execute("""SELECT count(*), sum(a.portao LIKE '%"literal"%'), sum(b.portao LIKE '%"literal"%'),
                                  sum(b.p_literal > ?), sum(b.p_literal > ?)
                           FROM predicoes_v35 a JOIN predicoes_v36 b USING (relato_id)""", (t_ac, t_taxa)).fetchone()
    # canônicos apenas (sem herdados)
    canon = con.execute("""SELECT count(*), sum(b.portao LIKE '%"literal"%'), sum(b.p_literal > ?)
                           FROM predicoes_v36 b WHERE b.herdado_de IS NULL""", (t_ac,)).fetchone()

    return dict(curva_prova=curva_prova, S=S, grade=curva_lit, curva_fig=curva_fig, t_ac=t_ac, t_ac_pl=(t_ac_min, t_ac_max), melhor=melhor,
                t_taxa=t_taxa, marc_taxa=marc_taxa, ac_taxa=ac_taxa, t_fig=t_fig, melhor_f=melhor_f, ac_f05=ac_f05,
                emp_f=(emp_f[0], emp_f[-1]), n_val=len(A), n_lit=n_lit, taxa_real=taxa_real, ac_cru=ac_cru, m_cru=m_cru,
                ac_c=ac_c, val35=(sum(a == q for a, q in zip([r['portao'] for r in vv if r['id'] in pr35], v35v)) / max(len(v35v), 1),
                                  sum(q[LIT] for q in v35v), len(v35v)),
                Ap=Ap, pred_p=pred_p, Ac=Ac, pred_c2=pred_c2, tot=tot, comum=comum, canon=canon)


def relatorio(r):
    N = r['n_val']
    o = []
    w = o.append
    w('# Portão v3.5 × v3.6 cru × v3.6 calibrado\n')
    w('*28/09/2026. Gerado por `aluno/calibrar_portao_v36.py` (só lê o banco; não reinfere: usa `p_portao`/`p_literal`/'
      '`p_figurado` gravados em `predicoes_v36`). O limiar é escolhido só na validação de 344 do final_v35 '
      '(semente 2015, 342 sem ambíguo); prova e cega só medem.*\n')
    w('## 1. Calibração (validação, n=%d)\n' % N)
    w(f"Literal real: {r['n_lit']}/{N} ({pct(r['taxa_real'])}) — o treino do v3.6 tem 83,6% de literais. "
      f"O v3.6 cru marca {r['m_cru']} literais aqui (acerto exato do portão {pct(r['ac_cru'])}); "
      f"o v3.5 marca {r['val35'][1]} (acerto {pct(r['val35'][0])}, n={r['val35'][2]}).\n")
    w('Acerto exato = as 8 células do portão idênticas ao gabarito. O limiar do literal varia; as outras sete classes ficam em 0,5 '
      '(figurado em %s).\n' % r['t_fig'])
    w('| limiar p_literal | acerto exato do portão | acerto só do literal | literais marcados | taxa marcada |')
    w('|---|---|---|---|---|')
    for t, ac, acl, m, tx in r['grade']:
        mark = ' **←**' if abs(t - 0.5) < 1e-9 else ''
        w(f'| {t:.2f}{mark} | {pct(ac)} | {pct(acl)} | {m} | {pct(tx)} |')
    w(f"\n(A taxa real é {pct(r['taxa_real'])}; 0,50 é o corte cru.)\n")
    w(f"- **Máximo acerto exato:** {pct(r['melhor'])} num platô de limiares de {r['t_ac_pl'][0]:.2f} a {r['t_ac_pl'][1]:.2f} "
      f"(passo 0,01); escolhido o do meio do platô, **{r['t_ac']:.2f}**.")
    w(f"- **Taxa marcada = taxa real:** limiar **{r['t_taxa']:.2f}** → {r['marc_taxa']} marcados de {N} "
      f"(real {r['n_lit']}), acerto {pct(r['ac_taxa'])}.")
    w(f"- **p_figurado:** melhor {pct(r['melhor_f'])} com limiar {r['emp_f'][0]:.2f}-{r['emp_f'][1]:.2f}; em 0,50 dá {pct(r['ac_f05'])} "
      f"(diferença de {round((r['melhor_f']-r['ac_f05'])*N)} casos de {N}). Ganho dentro do ruído: **p_figurado fica em 0,50**.\n")
    w('| limiar p_figurado (com literal em %.2f) | acerto exato | figurados marcados (real %d) |' % (r['t_ac'], 110))
    w('|---|---|---|')
    for tf, ac, m in r['curva_fig']:
        w(f'| {tf:.2f} | {pct(ac)} | {m} |')
    w('\nCaveat: com n=342 um caso vale 0,29 ponto; o platô de %.2f-%.2f é a evidência, não o pico exato.\n' % r['t_ac_pl'])

    def bloco(titulo, A, P, nomes, cega=False, teto=None):
        ac_r = {}
        w(f'### {titulo}\n')
        w('| portão | acerto exato | chute constante | teto entre anotadores | literais marcados (real) |')
        w('|---|---|---|---|---|')
        for k, rot in (('v35', 'v3.5 (gravado)'), ('v36cru', 'v3.6 cru (gravado)'),
                       ('v36cal', f"v3.6 calibrado (literal>{r['t_ac']:.2f})"),
                       ('v36taxa', f"v3.6 taxa igualada (literal>{r['t_taxa']:.2f})")):
            if cega:
                ac = sum(a[0] == p[0] for a, p in zip(A, P[k])) / len(A)
                base = max(sum(a[0] for a in A), len(A) - sum(a[0] for a in A)) / len(A)
                rt = 'literal×não-literal'
                nl = sum(a[0] for a in A)
            else:
                ac, base, comb = exato(A, P[k])
                nl = sum(a[LIT] for a in A)
            ml = sum(p[0 if cega else LIT] for p in P[k])
            w(f"| {rot} | {pct(ac)} | {pct(base)} | {teto or '—'} | {ml} ({nl}) |")
        w('')
        for k, rot in (('v35', 'v3.5'), ('v36cru', 'v3.6 cru'), ('v36cal', 'v3.6 calibrado')):
            w(f'**{rot}**\n')
            res = por_classe(A, P[k], ['literal', 'figurado'] if cega else PORTAO)
            for l in linhas_classe(res):
                w(l)
            w('')

    w('## 2. Prova (300; %d sem ambíguo)\n' % len(r['Ap']))
    bloco('Prova — 8 classes do portão', r['Ap'], r['pred_p'], PORTAO, teto='93%')
    w('Curva na prova, só informativa (NÃO usada para escolher; literal real 192):\n')
    w('| limiar p_literal | acerto exato | literais marcados |')
    w('|---|---|---|')
    for t, ac, m in r['curva_prova']:
        w(f'| {t:.2f} | {pct(ac)} | {m} |')
    w('')
    w('## 3. Revisão cega (83; literal × não-literal e figurado)\n')
    w('O teto de 93% é do portão de 8 classes na auditoria v3.2; não foi medido para literal×não-literal da cega.\n')
    bloco('Cega', r['Ac'], r['pred_c2'], None, cega=True)

    w('## 4. Taxa de literal no arquivo inteiro (o prior visível na página)\n')
    w('| portão | relatos | literal | taxa | figurado | taxa |')
    w('|---|---|---|---|---|---|')
    for k, rot in (('v35', 'v3.5'), ('v36cru', 'v3.6 cru'), ('v36cal', f"v3.6 calibrado (>{r['t_ac']:.2f})"),
                   ('v36taxa', f"v3.6 taxa igualada (>{r['t_taxa']:.2f})")):
        n, l, f = r['tot'][k]
        w(f'| {rot} | {n} | {l} | {pct(l/n)} | {f} | {pct(f/n)} |')
    n, l35, l36, lc, lt = r['comum']
    w(f"\nNos {n} relatos presentes em ambas as tabelas: v3.5 {pct(l35/n)} · v3.6 cru {pct(l36/n)} · calibrado {pct(lc/n)} · taxa igualada {pct(lt/n)}.")
    n, l36, lc = r['canon']
    w(f"Só canônicos (sem herdados, {n}): v3.6 cru {pct(l36/n)} · calibrado {pct(lc/n)}.")
    w('\nReferência: literal real na prova (sorteio uniforme) ≈ 64%%, na validação %s. A prova e a validação são amostras '
      'de outras populações do arquivo; a taxa do arquivo não tem gabarito.\n' % pct(r['taxa_real']))
    return '\n'.join(o)


if __name__ == '__main__':
    r = main()
    for s in r['S']:
        print(s)
    txt = relatorio(r)
    (RAIZ / 'rubrica' / 'medidas' / 'portao_v35_v36_calibrado.md').write_text(txt + '\n@@REC@@\n')
    (AQUI / 'limiar_portao_v36.json').write_text(json.dumps(
        dict(p_literal=r['t_ac'], p_figurado=r['t_fig'],
             como=f"máx. acerto exato do portão na validação de 344 do final_v35 (342 sem ambíguo, semente 2015): platô "
                  f"{r['t_ac_pl'][0]:.2f}-{r['t_ac_pl'][1]:.2f}, escolhido o meio; p_figurado mantido em 0,50 (ganho < 5 casos). "
                  f"Limiar alternativo que iguala a taxa marcada à real: {r['t_taxa']:.2f}. Demais classes do portão em 0,5. "
                  "Aplicar sobre p_literal/p_figurado de predicoes_v36; não reinferir."),
        indent=1, ensure_ascii=False) + '\n')
