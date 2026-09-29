#!/usr/bin/env python3
"""[V3] Fita de Möbius (Fitipe, 28/09 noite) — uma fita para cada arranjo.

A fita: X(u, v) = ((R + v·cos(u/2))·cos u, (R + v·cos(u/2))·sin u, v·sin(u/2)).
Com u em [0, 4π) e um afastamento d ao longo da normal N, o ponto
P = X + d·N percorre a PELE da fita engrossada: X(u+2π, v) = X(u, −v) e a
normal se inverte, então a segunda volta (u de 2π a 4π) é a outra face. As
duas faces são uma superfície só — é a Möbius.

  todos    : literal numa face (u de 0 a 2π), figurado na outra (u de 2π a
             4π), incerto na alma da fita (d = 0). Onde a face literal
             termina começa a figurada: é o lugar da passagem.
  classe   : a classe ocupa a pele inteira (u de 0 a 4π), uma volta contínua.

Dentro de cada face, (u, v) vem de um UMAP 2D da própria classe (mesmos
embeddings, cosseno), girado pelo eixo maior e passado a posto em cada eixo
para encher a faixa. Os 680 literal+figurado: no "todos", face literal.
Camadas (meta, idiomático, propaganda) ficam fora da fita.

Saída: dados/mobius_{todos,literal,figurado,incerto}.bin, int16 xyz/32767,
só os membros, na ordem da página (todos = relatos com NAT 0). Intermediários
(mapas 2D) em dados/umap2d_*.npy — reaproveitados se existirem.
Refazer a cada gerar.py (junto com projetar_classes.py e cargas_literal.py).
"""
import sqlite3
import time

import numpy as np

from projetar_classes import DADOS, DB, ids_da_pagina, ler_pontos, membros, regua

R, W, D = 0.58, 0.32, 0.045       # raio da fita, meia largura, meia espessura
# Fitipe (28/09 noite): bordas menos delineadas, com focos "vazando" como no
# globo. Três ruídos: (1) cada eixo mistura posto (enche a faixa) e a própria
# coordenada do UMAP (guarda os aglomerados); (2) jitter na largura e na
# espessura desfia as bordas; (3) dispersão aleatória nas bordas e nos
# aglomerados densos (ver POEIRA_BORDA, NUVEM_FOCO abaixo).
MISTURA, FIAPO = 0.5, 0.004
# O desfiado vem de campos SUAVES em (u, v) — somas de senos de frequência
# baixa, contínuas na volta (u/2 inteiro) — e não de ruído ponto a ponto:
# vizinhos recebem quase o mesmo deslocamento. O ruído independente (1ª
# tentativa) custou ~10 pontos de régua (46→36% no incerto).
ONDA_BORDA, ONDA_LARG, ONDA_ESP = 0.12, 0.02, 0.4
# 3ª versão (Fitipe: "parecem espinhos"): os focos eram empurrados todos pela
# normal — cada aglomerado virava uma coluna. Agora a dispersão é ALEATÓRIA em
# 3D (gaussiana isotrópica), com desvio que cresce na borda (a beira vira
# poeira) e nos aglomerados densos (viram nuvem, não espinho).
POEIRA_BORDA, NUVEM_FOCO = 0.045, 0.05


def campo(u, v, semente):
    """Campo suave em [-1, 1] sobre a fita (periódico em u com período 4π)."""
    g = np.random.default_rng(semente)
    tot = np.zeros_like(u)
    for _ in range(6):
        k = g.integers(1, 9) / 2               # meia-frequência: fecha na volta de 4π
        q = g.uniform(0.5, 4.0)
        tot += np.sin(k * u + g.uniform(0, TAU)) * np.cos(q * v / W + g.uniform(0, TAU))
    return tot / 6 * 2.2
TAU = 2 * np.pi


def ler_emb(con, ids):
    X = np.empty((len(ids), 1024), dtype='float32')
    for a in range(0, len(ids), 900):
        lote = ids[a:a + 900]
        got = dict(con.execute(f"SELECT id, embedding FROM relatos WHERE id IN ({','.join('?' * len(lote))})", lote))
        for j, rid in enumerate(lote):
            X[a + j] = np.frombuffer(got[rid], dtype='float32')
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    assert np.isfinite(X).all()
    return X


def mapa2d(con, ids, nome):
    arq = DADOS / f'umap2d_{nome}.npy'
    if arq.exists():
        Y = np.load(arq)
        if len(Y) == len(ids):
            print(f'{nome}: mapa 2D reaproveitado', flush=True)
            return Y, None
    X = ler_emb(con, ids)
    from umap import UMAP
    t0 = time.time()
    Y = UMAP(n_neighbors=15, min_dist=0.0, metric='cosine', n_components=2, n_epochs=200,
             init='pca', random_state=2015, verbose=False).fit_transform(X)
    print(f'{nome}: UMAP 2D {len(ids)} pontos em {(time.time() - t0) / 60:.1f} min', flush=True)
    np.save(arq, Y.astype('float32'))
    return Y, X


def faixa(Y):
    """Mapa 2D → (ru, rv, densidade): eixo maior ao longo da fita; cada eixo é
    meio posto (enche) e meio coordenada suavizada (guarda os aglomerados)."""
    Y = Y - np.median(Y, 0)
    _, _, Vt = np.linalg.svd(Y, full_matrices=False)
    Z = Y @ Vt.T
    n = len(Z)
    eixos = []
    for k in (0, 1):
        posto = (np.argsort(np.argsort(Z[:, k])) + 0.5) / n
        z = Z[:, k] / (1.4826 * np.median(np.abs(Z[:, k])) + 1e-9)
        suave = 0.5 + 0.5 * np.tanh(z / 2.2)
        eixos.append(MISTURA * posto + (1 - MISTURA) * suave)
    from sklearn.neighbors import NearestNeighbors
    dist, _ = NearestNeighbors(n_neighbors=9).fit(Y).kneighbors(Y)
    dens = 1 / (dist[:, 1:].mean(1) + 1e-9)
    drank = (np.argsort(np.argsort(dens)) + 0.5) / n
    return eixos[0], eixos[1], drank


def pele(u, v, d):
    """X(u, v) + d·N(u, v), u em [0, 4π)."""
    c, s, c2, s2 = np.cos(u), np.sin(u), np.cos(u / 2), np.sin(u / 2)
    rr = R + v * c2
    X = np.stack([rr * c, rr * s, v * s2], 1)
    Xu = np.stack([-v * s2 / 2 * c - rr * s, -v * s2 / 2 * s + rr * c, v * c2 / 2], 1)
    Xv = np.stack([c2 * c, c2 * s, s2], 1)
    N = np.cross(Xu, Xv)
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    return X + d[:, None] * N


def espessura(drank, d, rng, u, v, sinal=1.0):
    """Afastamento da face: d levemente ondulado por um campo suave."""
    return sinal * d + D * ONDA_ESP * campo(u, v, 7) + rng.normal(0, FIAPO, len(drank))


def espalhar(P, v, drank, rng):
    """Dispersão aleatória em 3D: poeira na borda, nuvem nos aglomerados densos."""
    borda = np.clip(np.abs(v) / W, 0, 1.3) ** 4
    foco = np.clip((drank - 0.9) / 0.1, 0, 1) ** 2
    sig = POEIRA_BORDA * borda + NUVEM_FOCO * foco
    return P + rng.normal(0, 1, P.shape) * sig[:, None]


def largura(u, rv, rng):
    """v na faixa, com borda ondulada (a meia largura respira ao longo de u)."""
    v = (2 * rv - 1) * W
    v = v * (1 + ONDA_BORDA * campo(u, 0 * u, 3)) + ONDA_LARG * campo(u, v, 5)
    return v + rng.normal(0, FIAPO, len(v))


def gravar_uvd(nome, u, v, d):
    """Coordenadas NA FITA (a página calcula xyz e faz o rio correr em u):
    u em uint16 sobre [0, 4π), v/W e d/D_ESC em int16."""
    # a beira vaza: a largura passa de W (até ~3W na cauda); o arquivo guarda v/(2W)
    v = np.clip(v, -2 * W * 0.9999, 2 * W * 0.9999)
    d = np.clip(d, -D_ESC * 0.9999, D_ESC * 0.9999)
    q = np.empty((len(u), 3), dtype='<u2')
    q[:, 0] = np.round((np.mod(u, 2 * TAU) / (2 * TAU)) * 65535).astype('<u2')
    q[:, 1] = (np.round(v / (2 * W) * 32767).astype('<i2')).view('<u2')
    q[:, 2] = (np.round(d / D_ESC * 32767).astype('<i2')).view('<u2')
    q.tofile(DADOS / f'mobius_{nome}.bin')
    print(f'dados/mobius_{nome}.bin ({len(u)} pontos, {q.nbytes / 1e6:.1f} MB, u v d)', flush=True)


def gravar(nome, P):
    n = np.linalg.norm(P, axis=1).max()
    if n > 0.999:
        P = P * (0.999 / n)                   # os focos não furam a bola da página
    assert np.isfinite(P).all() and np.abs(P).max() <= 1.0
    q = np.round(P * 32767).astype('<i2')
    q.tofile(DADOS / f'mobius_{nome}.bin')
    print(f'dados/mobius_{nome}.bin ({len(P)} pontos, {q.nbytes / 1e6:.1f} MB)', flush=True)


# 4ª versão (Fitipe: "ficou só difuso; no globo havia caminhos entre
# aglomerados, fios longos e finos"): a fita deixa de vir do UMAP 2D com posto
# (que achata os aglomerados) e passa a ser a BOLA de cada classe (dados/
# classe_*.bin, a mesma do arranjo globo) deformada em fita. Um eixo da bola
# vira o comprimento (por posto: as fatias da bola têm tamanhos diferentes);
# cada fatia redonda vira a seção da fita (largura × espessura), dividindo
# pelo raio da fatia. É contínuo: aglomerados, fios e pontes vêm junto. Sem
# poeira nem nuvem aleatórias.
ESP = 0.05                        # meia espessura de cada camada
# 5ª versão (Fitipe: "fenda no meio da torção"): com FACE > ESP sobrava um vão
# entre as camadas, visível onde a fita fica de perfil. Agora encostam no meio.
FACE = 0.8 * ESP                  # 8ª: as camadas se interpenetram um pouco no meio
D_ESC = 0.2                       # escala da espessura no arquivo (|d| < 0,2)
# 7ª versão (Fitipe: "vácuo na torção com o rio parado"): era a EMENDA — ali
# se encontram as pontas (polos) de bolas diferentes e as bordas não casam.
# Cada face passa um pouco da emenda (SOBRA radianos de cada lado): as pontas
# se sobrepõem e as populações se entremeiam, sem corte.
SOBRA = 0.0   # 10ª: a sobreposição dobrava a densidade na emenda (brilho em raios); a dispersão das pontas basta


def bola_da_classe(nat, bits, c):
    q = np.fromfile(DADOS / f'classe_{c}.bin', dtype='<i2').reshape(-1, 3) / 32767
    assert len(q) == membros(nat, bits, c).sum(), f'classe_{c}.bin fora de sincronia com a página'
    return q


def secao(B):
    """Bola → (ru ao longo, v e t na seção em [-1, 1]).
    11ª versão: sem dividir pelo raio da fatia. Perto dos polos quase todo
    ponto está na casca da bola, e a divisão levava a casca para a beira da
    seção — pontas ocas, que na emenda viravam um leque de raios. Largura e
    espessura vêm da ORDEM local em cada trecho (enche_largura): seção cheia
    em toda a volta, inclusive nas pontas."""
    x, y, z = B[:, 0], B[:, 1], B[:, 2]
    n = len(B)
    ru = (np.argsort(np.argsort(x)) + 0.5) / n
    return ru, enche_largura(ru, y), enche_largura(ru, z, ENCHE_T), np.linalg.norm(B, axis=1)


# 9ª versão (Fitipe: "por que continua com uma faixa de vácuo?"). Medido no
# mapa (volta × largura): eram VAZIOS DO DADO — numa fatia da bola os relatos
# não ocupam todas as direções (os vãos entre aglomerados). No globo ficam
# escondidos atrás de outras camadas; na fita fina ficam expostos, e como a
# fatia muda devagar ao longo da fita, o vão vira uma faixa oblíqua.
# Em cada trecho da fita a largura é redistribuída pela ORDEM dos pontos
# daquele trecho (CDF local, interpolada entre trechos vizinhos para não
# criar cortes), misturada com a posição original (ENCHE) para os fios
# continuarem aparecendo.
ENCHE = 0.5          # 14ª: era 0,7 — a redistribuição uniformiza e apaga o contraste
ENCHE_T = 0.75       # espessura (era 1,0)

# 10ª versão (Fitipe: "tire os raios da emenda; as bordas voltaram a ficar
# demarcadas"). (1) As pontas de cada bola (o fim de x) são os relatos mais
# soltos; na emenda viravam raios atravessando a largura. Nas pontas, u ganha
# uma dispersão que cresce até a ponta: viram poeira misturada à outra face.
# (2) Borda: a largura ondula devagar (campo suave) e os pontos da beira
# VAZAM para fora na própria largura, com cauda longa (exponencial) — sem o
# empurrão pela normal que fez espinhos na 2ª e sem a poeira em tudo que
# deixou difuso na 3ª. A espessura também desfia na sua beira.
PONTA, DISP_PONTA = 0.06, 0.35       # fração da volta tratada como ponta; desvio máx. em u
ONDA, POEIRA = 0.10, 0.004       # 14ª: quase sem poeira (Fitipe: "ainda um pouco difuso")
R_FIO, FIO = 0.88, 0.9            # a partir de que raio da bola o relato é "fio"; quanto o fio se estica


def pontas(ru, rng):
    """Desvio em u nas pontas (0 no meio), para desfazer os raios da emenda."""
    k = np.clip(np.maximum(PONTA - ru, ru - (1 - PONTA)) / PONTA, 0, 1) ** 2
    return rng.normal(0, 1, len(ru)) * DISP_PONTA * k


def borda(u, v, t, rb, rng):
    """13ª versão (Fitipe: "como no geóide: caminhos entre aglomerados que
    saem para fora às vezes, entram para dentro em outras; os anéis se
    conectando por esses fios e vazando um no outro"). O vazamento vem do
    PRÓPRIO DADO: na bola, os fios que vazam são os relatos mais externos
    (raio perto de 1). Aqui eles se afastam do miolo da seção na direção que
    já têm nela — quem aponta para a beira da largura vaza para fora da fita,
    quem aponta para fora da face sai da superfície, quem aponta para o miolo
    atravessa para a outra camada (é por aí que os anéis conversam). Vizinhos
    de um fio apontam para o mesmo lado: saem caminhos, não espinhos nem
    poeira. Um fiapo de poeira isotrópica só suaviza. Devolve (u, v em
    unidades, t esticado, acréscimo de espessura)."""
    k = np.clip((rb - R_FIO) / (1 - R_FIO), 0, 1) ** 2
    esticar = 1 + FIO * k
    vv = v * esticar * (1 + ONDA * campo(u, 0 * u, 3))
    tt = t * esticar
    sig = POEIRA * np.clip(np.abs(v), 0, 1.3) ** 4
    g = rng.normal(0, 1, (len(v), 3)) * sig[:, None]
    return u + g[:, 0] / R, vv * W + g[:, 1], tt, g[:, 2]


def enche_largura(ru, v, enche=None):
    enche = ENCHE if enche is None else enche
    n = len(v)
    nb = max(8, min(120, n // 400))
    bordas = np.quantile(ru, np.linspace(0, 1, nb + 1))
    centros = (bordas[:-1] + bordas[1:]) / 2
    ordenados = [np.sort(v[(ru >= bordas[b]) & (ru <= bordas[b + 1])]) for b in range(nb)]
    q = np.empty((nb, n))
    for b, o in enumerate(ordenados):
        q[b] = np.searchsorted(o, v) / max(1, len(o))           # CDF do trecho b, em todos
    pos = np.clip(np.interp(ru, centros, np.arange(nb)), 0, nb - 1)
    b0 = np.floor(pos).astype(int); b1 = np.minimum(b0 + 1, nb - 1); w = pos - b0
    cdf = (1 - w) * q[b0, np.arange(n)] + w * q[b1, np.arange(n)]
    return enche * (2 * cdf - 1) + (1 - enche) * np.clip(v, -1, 1)


def main():
    pos, nat, bits = ler_pontos()
    ids = ids_da_pagina(pos)
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=600)
    con.execute('PRAGMA busy_timeout=600000')
    rng = np.random.default_rng(2015)
    ruido = np.random.default_rng(28)
    secoes = {}
    for c in ['incerto', 'literal', 'figurado']:
        idx = np.nonzero(membros(nat, bits, c))[0]
        ru, v, t, rb = secao(bola_da_classe(nat, bits, c))
        secoes[c] = (idx, ru, v, t, rb)
        # a fita da classe: a pele inteira (u de 0 a 4π), uma camada contínua
        u = -SOBRA + ru * (2 * TAU + 2 * SOBRA) + pontas(ru, ruido)
        u, vw, tt, dd = borda(u, v, t, rb, ruido)
        d = FACE + tt * ESP + dd
        P = pele(u, vw, d)
        gravar_uvd(c, u, vw, d)
        X = ler_emb(con, [ids[i] for i in idx])
        print(f'  régua {c}: fita {regua(X, P, rng):.0%}', flush=True)

    # todos: literal na face de 0 a 2π, figurado na de 2π a 4π, incerto na alma
    rel = np.nonzero(nat == 0)[0]
    lugar = {int(i): k for k, i in enumerate(rel)}
    U, V, Dd = np.zeros(len(rel)), np.zeros(len(rel)), np.zeros(len(rel))
    feito = np.zeros(len(rel), bool)
    for c, (u0, d, esp) in [('literal', (0.0, FACE, ESP)), ('figurado', (TAU, FACE, ESP)),
                            ('incerto', (0.0, 0.0, ESP * 0.4))]:
        idx, ru, v, t, rb = secoes[c]
        k = np.array([lugar[int(i)] for i in idx])
        livre = ~feito[k]                        # os 680 ficam na face literal
        kk = k[livre]
        uu = u0 - SOBRA + ru[livre] * (TAU + 2 * SOBRA) + pontas(ru[livre], ruido)
        uu, vw, tt, dd = borda(uu, v[livre], t[livre], rb[livre], ruido)
        U[kk], V[kk], Dd[kk] = uu, vw, d + tt * esp + dd
        feito[kk] = True
    assert feito.all(), f'{(~feito).sum()} relatos sem lugar na fita'
    gravar_uvd('todos', U, V, Dd)
    import json
    json.dump({'R': R, 'W': 2 * W, 'D_ESC': D_ESC}, open(DADOS / 'mobius_meta.json', 'w'))  # W = escala de v no arquivo


if __name__ == '__main__':
    main()
