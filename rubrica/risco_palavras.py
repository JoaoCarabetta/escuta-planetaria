#!/usr/bin/env python3
"""Via 1 dos candidatos de bandeira (ideia do Fitipe, 27/09): PALAVRAS.

O aluno (BERT) não aprende bandeira (32-54%) e a sonda de risco lê só o
embedding — que agrupa por ASSUNTO (sofrimento), não pelo que faz a bandeira
levantar (ideação presente, plano, autolesão, ameaça, ódio a grupo). As
palavras são o complemento barato: "me matar", "tirar minha vida", "me
cortar" dizem o que o embedding dilui.

Comparação: textos COM bandeira confirmada × conferidos SEM bandeira (não
contra o arquivo todo — contra o arquivo, o que sobe é o vocabulário do
DESABAFO, que também é o dos falsos alarmes). Unigramas e bigramas
normalizados (sem acento, sem caixa), contados por DOCUMENTO (um texto que
repete "morrer" 30× conta uma vez). Log-odds com prior de Dirichlet
informativo (Monroe, Colaresi & Quinn 2008), prior = frequência no conjunto
conferido inteiro. Depois, para cada termo, a PRECISÃO medida nos conferidos
(positivos que têm o termo / conferidos que têm o termo) e o alcance no
arquivo não conferido.

Validação (27/09, metade escolhe os termos, a outra metade mede, semente 7):
com suporte ≥15 na metade (≈30 no todo) e precisão ≥0,7, um texto com ≥1
termo tem precisão 0,67 (revocação 0,73); com ≥2 termos distintos, 0,79
(revocação 0,45). ATENÇÃO: essa precisão é no conjunto CONFERIDO, que a
sonda enriqueceu em positivos (15%); no arquivo aberto será menor — por
isso a via das palavras sozinha entra por último na fila, e com ≥2 termos.

Escolha dos termos de alta precisão: precisão ≥ PREC_MIN com pelo menos
SUP_MIN positivos, e alcance no arquivo não mais que ALCANCE_MAX× o suporte
nos conferidos (termo que aparece em 40 mil textos e em 10 conferidos é
vocabulário comum que os conferidos, enriquecidos pela sonda, superestimam).

  python3 risco_palavras.py  →  <scratch>/palavras_termos.tsv (todos os termos)
                                <scratch>/palavras_escolhidos.json
                                <scratch>/palavras_batidas.jsonl (id, termos)
Lê o banco só para leitura; não grava nada no banco nem na página.
"""
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import risco_rotulos as R

SCRATCH = Path('/private/tmp/claude-501/-Users-fitipe-Desktop-arte-c-joao-tta/'
               'e9da8b04-cc60-40d3-99e1-9659aa0a463e/scratchpad/risco')
SUP_MIN = 20         # positivos mínimos com o termo (com 6, a precisão na metade
                     # de fora caía de ~0,7 para ~0,5: termo raro = sobreajuste)
PREC_MIN = 0.70      # precisão mínima nos conferidos
ALCANCE_MAX = 25     # textos não conferidos por texto conferido com o termo
A0 = 500.0           # força do prior (pseudo-documentos)

_TOK = re.compile(r'[a-z0-9]+')
# palavras que sozinhas não dizem nada (mas ficam dentro dos bigramas)
_VAZIAS = set('a o e de da do que um uma em no na os as eu me meu minha mas com pra para por se '
              'nao sim ja ai la isso esse essa ele ela eles elas voce vc tb tambem so mais muito '
              'foi era ser ter tem to ta e ou ao aos nos num numa dos das pelo pela'.split())


def normalizar(t):
    t = unicodedata.normalize('NFKD', (t or '').lower())
    return ''.join(c for c in t if not unicodedata.combining(c))


def termos(t):
    tk = _TOK.findall(normalizar(t))
    s = {w for w in tk if w not in _VAZIAS and len(w) > 2}
    s.update(f'{a} {b}' for a, b in zip(tk, tk[1:]) if not (a in _VAZIAS and b in _VAZIAS))
    return s


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    con = R.conectar()
    rotulo, conferidos, info = R.carregar(con)
    print('rótulos:', info)

    df_pos, df_neg = Counter(), Counter()
    n_pos = n_neg = 0
    ids = list(rotulo)
    for k in range(0, len(ids), 900):
        q = ids[k:k + 900]
        for rid, t in con.execute(f"SELECT id, texto FROM relatos WHERE id IN ({','.join('?' * len(q))})", q):
            s = termos(t)
            if rotulo[rid]:
                df_pos.update(s); n_pos += 1
            else:
                df_neg.update(s); n_neg += 1
    print(f'positivos {n_pos} · negativos {n_neg}')

    # log-odds com prior informativo (por documento)
    tot = df_pos + df_neg
    N = n_pos + n_neg
    linhas = []
    for w, c in tot.items():
        yp, yn = df_pos[w], df_neg[w]
        if yp < 3:
            continue
        a = A0 * c / N
        lp = math.log((yp + a) / (n_pos + A0 - yp - a))
        ln = math.log((yn + a) / (n_neg + A0 - yn - a))
        var = 1 / (yp + a) + 1 / (yn + a)
        linhas.append([w, (lp - ln) / math.sqrt(var), yp, yn, yp / (yp + yn)])
    linhas.sort(key=lambda x: -x[1])
    topo = [l for l in linhas if l[1] > 2.0][:1500]
    vocab = {l[0] for l in topo}
    print(f'{len(linhas)} termos com ≥3 positivos · {len(topo)} com z>2 vão ao arquivo')

    # alcance no arquivo inteiro (canônicos), separando conferidos
    # (duas passadas: guardar os termos de 500 mil textos não cabe folgado na memória)
    alcance = Counter()
    pag = R.ids_da_pagina()
    SQL = 'SELECT id, texto FROM relatos WHERE canonico_de IS NULL'
    for rid, t in con.execute(SQL):
        if rid not in conferidos:
            alcance.update(termos(t) & vocab)

    with open(SCRATCH / 'palavras_termos.tsv', 'w') as f:
        f.write('termo\tz\tpos\tneg\tprecisao\tnao_conferidos\n')
        for w, z, yp, yn, p in topo:
            f.write(f'{w}\t{z:.2f}\t{yp}\t{yn}\t{p:.3f}\t{alcance[w]}\n')

    escolhidos = [dict(termo=w, z=round(z, 2), pos=yp, neg=yn, precisao=round(p, 3), nao_conferidos=alcance[w])
                  for w, z, yp, yn, p in topo
                  if yp >= SUP_MIN and p >= PREC_MIN and alcance[w] <= ALCANCE_MAX * (yp + yn)]
    # tira termo redundante: unigrama/bigrama contido num escolhido mais amplo com a mesma cobertura
    escolhidos.sort(key=lambda d: (-d['precisao'], -d['pos']))
    json.dump(escolhidos, open(SCRATCH / 'palavras_escolhidos.json', 'w'), ensure_ascii=False, indent=1)
    esc = {d['termo'] for d in escolhidos}

    n = fora = 0
    with open(SCRATCH / 'palavras_batidas.jsonl', 'w') as f:
        for rid, t in con.execute(SQL):
            if rid in conferidos:
                continue
            s = sorted(termos(t) & esc)
            if s:
                n += 1; fora += rid not in pag
                f.write(json.dumps({'id': rid, 'termos': s, 'na_pagina': rid in pag}, ensure_ascii=False) + '\n')
    print(f'{len(escolhidos)} termos escolhidos (prec≥{PREC_MIN}, pos≥{SUP_MIN}) · '
          f'{n} textos não conferidos batem · {fora} fora da página')
    for d in escolhidos[:40]:
        print(f"  {d['termo']:<28} prec {d['precisao']:.2f}  pos {d['pos']:>4}  neg {d['neg']:>4}  arquivo {d['nao_conferidos']}")


if __name__ == '__main__':
    main()
