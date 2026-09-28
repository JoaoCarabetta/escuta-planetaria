#!/usr/bin/env python3
"""Arquipélago Onírico — gera o mar de ilhas a partir do planeta V2.

Um jogo: cada ilha é um aglomerado de relatos de sonho, e duas ilhas ficam
perto no mar quando os aglomerados delas ficam perto no planeta. Quem joga
conta um sonho; a página acha, pelas palavras, os aglomerados onde ele ecoa e
faz nascer ali a ilha dessa pessoa, com um barco na praia.

Lê só o que já está publicado em planeta-v2/dados/ (pontos.bin, textos*.json,
cuidado.json) — não precisa do banco. Rode de novo sempre que o planeta for
regerado ou o cuidado.json mudar (a página já relê o cuidado.json do planeta
enquanto ele for o mesmo de que as ilhas saíram; regerar tira os textos
também dos arquivos daqui):

    python3 arquipelago/gerar.py

Decisões (medidas na geração de 28/09, 444.591 relatos):
  - AGLOMERADOS: k-means com 240 centros sobre as posições 3D do planeta, que
    vêm SÓ do embedding (a bola do UMAP, ver planeta-v2/projetar.py). Ficam
    de fora a propaganda (camada 3) e todo índice do cuidado.json. O k-means
    não deixa ninguém sem ilha e dá ilhas de tamanhos diferentes (de 54 a
    9.595 relatos): a densidade do planeta é que decide.
  - PROXIMIDADE: o mar é plano e a bola tem três eixos; alguma vizinhança se
    perde na passagem. A régua: das 6 ilhas mais próximas de cada uma NA
    BOLA, quantas continuam entre as 6 mais próximas NO MAR. O PCA dos
    centróides preserva 36%, o MDS (SMACOF) 38-39%; o t-SNE dos centróides,
    69% (acaso: 2,5%). Fica o t-SNE, iniciado pelo PCA. As 6 vizinhas
    verdadeiras de cada ilha vão no mundo.json como `viz`: a página as
    desenha como correntes marítimas, e é por elas que o barco anda mais
    rápido — o mar mostra onde a planificação mentiu.
  - NOMES: as duas palavras mais características de cada aglomerado
    (frequentes nele e raras no resto do arquivo). Aglomerados de fórmula
    ("meu sonho", "que pesadelo" — centenas de pessoas escrevendo só isso)
    não têm palavra característica; o nome é a própria fórmula, entre aspas.
  - O SONHO DE QUEM JOGA não passa por embedding (o bge-m3 não roda no
    navegador): casa-se pelas raízes das palavras. Para cada raiz, as ilhas
    onde ela é característica, com peso idf × log(quanto ela é mais comum ali
    do que no arquivo, por palavra distinta escrita — ver `elevacao`). O
    índice leva as próprias regras de fatiar, para que a página corte o texto
    exatamente como este script cortou.
  - AMOSTRA: cada ilha leva de 6 a 28 sonhos (mais para as maiores), metade
    os mais centrais do aglomerado e metade ao acaso, sem repetir texto,
    preferindo relatos de 25 a 1.100 caracteres. Os textos já são públicos
    na página do planeta; aqui vão só essas amostras.

Saída (arquipelago/dados/):
  mundo.json      as ilhas: posição no mar, raio, nome, palavras, tempero
                  (quanto é sonho dormindo, desejo, pesadelo), motivos que
                  mobíliam a ilha, vizinhas verdadeiras
  palavras.json   o índice raiz → ilhas, com as regras de fatiar
  ilhas/<n>.json  a amostra de sonhos de cada ilha (baixada ao chegar perto)
"""
import json
import math
import re
import struct
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
PLANETA = AQUI.parent / 'planeta-v2' / 'dados'
SAIDA = AQUI / 'dados'

K = 240                 # quantas ilhas
SEMENTE = 2015
PERPLEXIDADE = 20       # do t-SNE: medido 5 → 62%, 10 → 66%, 20 → 69%
VIZINHAS = 6            # a régua e as correntes

# o mar em "passos" (1 passo = 1 px com zoom 1 na página)
RAIO_MEDIANO = 260      # a ilha de tamanho mediano
RAIO_MIN, RAIO_MAX = 80, 560
DIST_VIZINHA = 1250     # distância mediana de uma ilha à mais próxima (centro a centro)
FOLGA = 260             # água mínima entre duas costas

TEXTO_MIN, TEXTO_MAX = 25, 1100

# ——— fatiar: as mesmas regras vão para palavras.json e a página as repete ———

_ACENTO = re.compile('[\u0300-\u036f]')


def normalizar(s):
    return _ACENTO.sub('', unicodedata.normalize('NFD', s.lower()))


# palavras que não localizam nada, e as de sonho em si (todo relato as tem)
PARADAS = sorted(set(normalizar(w) for w in """
a à ao aos aquela aquelas aquele aqueles aquilo as até com como da das de dela delas dele deles depois do dos
e é ela elas ele eles em entre era eram éramos essa essas esse esses esta está estamos estão estas estava
estavam estávamos este esteja estejam estes esteve estive estivemos estiver estivera estiveram estiverem
estivesse estivessem estou eu foi fomos for fora foram forem fosse fossem fui há haja hajam havia hei houve
isso isto já lhe lhes mais mas me mesmo mesma mesmos meu meus minha minhas muito muita muitos muitas na não
nas nem no nos nós nossa nossas nosso nossos num numa o os ou para pela pelas pelo pelos por qual quais
quando que quem são se seja sejam sem ser será seria seriam seu seus só somos sou sua suas também te tem têm
temos tenha tenham tenho terá teria teu teus teve tinha tinham tive tivemos tiver tivesse tu tua tuas um
uma umas uns você vocês vos pra pro pras pros tá tô to vc vcs q pq porque porquê tbm tb né ne aí ai então
entao tipo coisa coisas gente ainda agora aqui ali lá la onde sempre nunca antes hoje ontem dia dias noite
vez vezes outro outra outros outras todo toda todos todas tudo nada algo alguém ninguém cada bem mal pouco
pouca poucos tão tanto tanta assim sim bom boa vai vou vamos ia iam fazer faz fiz feito fez ficar fica
ficou fiquei estar ter dar deu dei disse dizer diz falar falou falei sei saber sabe acho achei acha quero
queria quer pode posso podia poder conseguir consigo consegui ver vi viu vendo olhar apenas desde sobre sob
contra durante sendo sido tendo pois porém logo cara mano etc dessa desse deste desta disso nisso naquele
naquela dessas desses neste nesta nesse nessa mim comigo contigo talvez enquanto após real realmente
simplesmente acontece aconteceu
sonho sonhos sonhei sonhar sonhando sonhava sonhou sonhe sonha sonham sonhamos sonhador sonhadora sonhado
pesadelo pesadelos dream dreams dreamt dreamed dreaming nightmare nightmares
the and of to in that it is was for with on as at be this have has had not but are you he she they them
his her my me we our your im ive its so just like then there when out up all one about what would could
should dont didnt were been being do did does from by an or if no yes can will get got some any more very
really know think into over again also only even still because how who which while where why am
http https www com html jpg png gif amp reddit imgur bsky twitter
""".split()))
_PARADAS = set(PARADAS)
RISO = r'^(?:k+|(?:ha)+h?|(?:he)+h?|(?:hu)+|rs+|a+h+|u+|a+|e+)$'
_RISO = re.compile(RISO)
# raiz leve: tira no máximo UM sufixo, e só se sobrarem 4 letras — junta
# plural, gênero e parte da conjugação ("dentes"/"dente", "correndo"/"correr")
SUFIXOS = sorted("""amentos imentos amento imento mente acoes icoes avamos iamos ando endo indo aram eram iram
avam ados adas idos idas acao icao aria eria iria ado ada ido ida ava oes aes ais eis ois es as os ar er ir
ei ou eu iu ia am em a o e s""".split(), key=lambda s: (-len(s), s))
_PALAVRA = re.compile('[a-z\u00e0-\u00f6\u00f8-\u00ff]+')
# endereço, @perfil e #hashtag saem antes de fatiar: viravam "youtu", "amzn",
# "unnaxoficial" — e batizavam ilhas
LIMPAR = (r'https?://[^\s]+|www\.[^\s]+|[@#][A-Za-z0-9_.\u00c0-\u00ff]+'
          r'|[A-Za-z0-9.-]+\.(?:com|be|br|net|org|ly|gl|co|me|tv|app|to|social)(?:/[^\s]*)?')
_LIMPAR = re.compile(LIMPAR)


def raiz(w):
    for s in SUFIXOS:
        if w.endswith(s) and len(w) - len(s) >= 4:
            return w[:-len(s)]
    return w


def fatiar(texto):
    """→ [(raiz, forma)] das palavras que contam, forma com acento"""
    saida = []
    for forma in _PALAVRA.findall(_LIMPAR.sub(' ', texto).lower()):
        n = normalizar(forma)
        if len(n) < 3 or n in _PARADAS or _RISO.match(n):
            continue
        saida.append((raiz(n), forma))
    return saida


# palavrão não batiza ilha, nem dentro de fórmula («meu sonho pqp» → a seguinte)
PALAVRAO = set(normalizar(w) for w in """
pqp porra caralho carai krl crl foda fdp puta merda cu buceta piroca pica pau rola vsf vsfd desgraça
""".split())
# para nome e etiqueta de ilha: gíria, xingamento, palavra de todo relato
# (acordei, tava, vida, pior…) — casam o sonho de quem joga, mas não batizam
NAO_BATIZA = PALAVRAO | set(normalizar(w) for w in """
mds mdsss dnv vsf vsfd slk slc amg amgs vey vei veyr cntg pqp porra merda caralho foda fdp krl crl puta cu
buceta piroca pica pau rola mamar chupar gozar gozei punheta siririca foder fodendo suruba orgia nudes
onlyfans cacete desgraça tava tavam tavamos acordei acordar acordo acordou lembro lembrar lembrava
estranho estranha bizarro esquisito esquisita horrível ruim simm simmm siim sla oq oque mt mto msm dps hj
tmb pfv pfvr vdd gnt ngm cmg ctg tlg blz ss nss aff afff affs user deleted removed tbh lol omg wtf lmao
pior melhor maior menor virou vira sai pare parar voltar volta vinha juro nível puts putz literalmente
ironicamente parece algum alguma sinal igual final menos imagina vida sinto sentir anos dormi dormir
durmo aleatório aleatória realizar feliz bons deve verdadeiro novo nova tempo pessoas passar querer
linda lindo legal top simples engraçado aiii miga migo nmrl mlk twt tml pin feat live post foto vídeo
video open track intl watch dera existe existir apareceu vivendo viver vive acredito acabei tirei
comecei devia vejo falo mandar siga follow olha caraca bagulho bglh negócio impossível trend date hora
mina jeito par namoral kakakakaka meudeus comia comendo jogando vamo hashtag nat adm duas meio
pensando tentar espero infelizmente atrás encontrar demorei acontecesse favor funciona ultimamente virando
voltasse imagem ótimo tirar rolar apoio
""".split())

# motivos que mobíliam a ilha: um aglomerado onde essas palavras são mais
# comuns que no arquivo ganha casas, lagoas, lápides… A página usa as mesmas
# listas para mobiliar a ilha de quem joga com as palavras do sonho dela.
MOTIVOS = {
    'casa': 'casa casas apartamento predio quarto sala cozinha banheiro janela parede telhado vizinho '
            'vizinha morar mansao condominio',
    'familia': 'mae pai avo vovo vovó irma irmao tia tio prima primo familia filho filha bebe crianca',
    'agua': 'agua mar praia onda ondas rio piscina chuva lago oceano afogando afogar nadar nadando '
            'barco navio enchente cachoeira tsunami',
    'floresta': 'floresta arvore arvores mato jardim flor flores planta plantas folhas natureza selva '
                'bosque fazenda sitio',
    'altura': 'montanha morro altura alto cair caindo caiu queda precipicio penhasco abismo escada '
              'escadas pular pulando topo',
    'fogo': 'fogo incendio queimar queimando chamas fumaca explosao vulcao queimado',
    'morte': 'morte morto morta mortos morrer morrendo morreu cemiterio caixao velorio enterro funeral '
             'tumulo defunto falecido falecida fantasma espirito',
    'bichos': 'cobra cobras aranha aranhas barata baratas rato ratos inseto insetos bicho bichos lagarto '
              'jacare tubarao minhoca abelha formiga formigas escorpiao',
    'animais': 'cachorro cachorros cachorra gato gatos gata gatinho cavalo cavalos passaro passaros '
               'animal animais vaca leao tigre urso coelho galinha peixe peixes',
    'escola': 'escola prova provas professor professora aula aulas faculdade colegio vestibular enem '
              'estudar estudando turma universidade formatura',
    'sagrado': 'igreja deus jesus anjo anjos demonio diabo satanas capeta oracao rezar orar santo santa '
               'macumba orixa biblia inferno milagre pastor padre',
    'estrada': 'carro carros estrada onibus trem metro viagem viajar rua avenida moto bicicleta uber '
               'motorista dirigir dirigindo acidente aeroporto',
    'voo': 'voar voando voei voava ceu aviao avioes nuvem nuvens estrela estrelas lua planeta espaco '
           'astronauta foguete flutuando flutuar asas',
    'corpo': 'dente dentes boca sangue corpo cabelo olho olhos unha unhas pele barriga gravida gravidez '
             'parto cirurgia hospital medico',
    'frio': 'neve frio gelo inverno congelando congelado',
    'ouro': 'dinheiro rico rica riqueza emprego trabalho salario empresa carreira sucesso loteria '
            'ganhar premio',
    'amor': 'amor beijo beijar beijando namorado namorada namorar crush casamento casar noivo noiva '
            'marido esposa paixao apaixonado apaixonada abraco',
    'perigo': 'perseguicao perseguindo perseguido correr correndo fugir fugindo policia tiro tiros arma '
              'armas guerra bandido assalto sequestro matar matando assassino faca briga ataque zumbi '
              'zumbis monstro monstros',
    'estranheza': 'espelho espelhos elevador labirinto portal corredor infinito relogio porta portas '
                  'escuro escuridao sombra sombras',
    'musica': 'musica show cantar cantando banda cantor cantora festival album danca dancar palco',
    'telas': 'celular internet instagram whatsapp tiktok youtube jogo jogos videogame computador tela',
    'comida': 'comida comer comendo bolo chocolate pizza doce doces fome restaurante lanche fruta frutas',
}
MOTIVO_RAIZES = {m: sorted(set(raiz(normalizar(w)) for w in ws.split())) for m, ws in MOTIVOS.items()}


# ——— leitura do planeta ———

def ler_planeta():
    buf = (PLANETA / 'pontos.bin').read_bytes()
    n = struct.unpack_from('<I', buf, 0)[0]
    tipo = np.dtype([('pos', '<f4', 3), ('camada', 'u1'), ('fonte', 'u1'), ('com', 'u1'),
                     ('ano', '<u2'), ('mes', 'u1'), ('bits', '<u2'), ('pl', 'u1'), ('pf', 'u1')])
    assert tipo.itemsize == 22
    reg = np.frombuffer(buf, dtype=tipo, count=n, offset=4)
    meta = json.load(open(PLANETA / 'meta.json'))
    assert meta['n'] == n, 'meta.json e pontos.bin são de gerações diferentes'
    textos = [None] * n
    for b in range(meta['arquivos_texto']):
        bl = json.load(open(PLANETA / f'textos{b}.json'))
        textos[bl['i0']:bl['i0'] + len(bl['textos'])] = bl['textos']
    assert all(t is not None for t in textos)
    cuidado = set(json.load(open(PLANETA / 'cuidado.json')))
    return reg, textos, cuidado, len(buf)


# ——— k-means ———

def kmeans(X, k, semente, iteracoes=60):
    """Lloyd com início k-means++ numa amostra. Determinístico pela semente."""
    rng = np.random.default_rng(semente)
    amostra = X[rng.choice(len(X), min(len(X), 60000), replace=False)]
    C = [amostra[rng.integers(len(amostra))]]
    d2 = ((amostra - C[0]) ** 2).sum(1)
    for _ in range(1, k):
        c = amostra[rng.choice(len(amostra), p=d2 / d2.sum())]
        C.append(c)
        d2 = np.minimum(d2, ((amostra - c) ** 2).sum(1))
    C = np.array(C)
    rotulo = np.empty(len(X), dtype=np.int32)
    for _ in range(iteracoes):
        for i0 in range(0, len(X), 50000):
            B = X[i0:i0 + 50000]
            d = (B ** 2).sum(1)[:, None] - 2 * B @ C.T + (C ** 2).sum(1)[None]
            rotulo[i0:i0 + 50000] = d.argmin(1)
        conta = np.bincount(rotulo, minlength=k)
        novo = np.stack([np.bincount(rotulo, weights=X[:, j], minlength=k) for j in range(3)], 1)
        vazio = conta == 0
        novo[~vazio] /= conta[~vazio, None]
        novo[vazio] = C[vazio]
        andou = np.sqrt(((novo - C) ** 2).sum(1)).max()
        C = novo
        if andou < 1e-6:
            break
    return C, rotulo


# ——— do espaço dos sonhos para o mar ———

def vizinhas(X, m):
    d = np.sqrt(((X[:, None] - X[None]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    return np.argsort(d, 1, kind='stable')[:, :m]


def regua(V3, Y, m=VIZINHAS):
    """fração das m vizinhas na bola que continuam entre as m mais próximas no mar"""
    V2 = vizinhas(Y, m)
    return float(np.mean([len(set(a) & set(b)) / m for a, b in zip(V3[:, :m], V2)]))


def tsne(X, Y0, perp, iteracoes=2000):
    """t-SNE exato (são só 240 pontos), iniciado pelo PCA: sem acaso."""
    n = len(X)
    d2 = ((X[:, None] - X[None]) ** 2).sum(-1)
    P = np.zeros((n, n))
    alvo = math.log(perp)
    for i in range(n):
        lo, hi = 1e-8, 1e8
        for _ in range(100):
            beta = math.sqrt(lo * hi)
            p = np.exp(-np.maximum(d2[i] - d2[i][d2[i] > 0].min(), 0) * beta)
            p[i] = 0
            p /= p.sum()
            H = -(p[p > 0] * np.log(p[p > 0])).sum()
            if H > alvo:
                lo = beta
            else:
                hi = beta
        P[i] = p
    P = np.maximum((P + P.T) / (2 * n), 1e-12)
    Y = Y0 / Y0.std() * 1e-2
    passo = np.zeros_like(Y)
    for t in range(iteracoes):
        exagero = 12 if t < 250 else 1
        q = 1 / (1 + ((Y[:, None] - Y[None]) ** 2).sum(-1))
        np.fill_diagonal(q, 0)
        Q = np.maximum(q / q.sum(), 1e-12)
        G = 4 * (((exagero * P - Q) * q)[:, :, None] * (Y[:, None] - Y[None])).sum(1)
        passo = (0.5 if t < 250 else 0.8) * passo - 50 * G
        Y = Y + passo
    return Y


def afastar(Y, R, folga, voltas=400):
    """empurra as ilhas até nenhuma costa ficar a menos de `folga` da outra"""
    Y = Y.copy()
    for _ in range(voltas):
        d = Y[:, None] - Y[None]
        dist = np.sqrt((d ** 2).sum(-1))
        np.fill_diagonal(dist, np.inf)
        falta = (R[:, None] + R[None] + folga) - dist
        if falta.max() <= 0.5:
            break
        falta = np.clip(falta, 0, None)
        np.fill_diagonal(falta, 0)
        empurra = (d / np.maximum(dist, 1e-9)[:, :, None] * falta[:, :, None] * 0.5).sum(1)
        Y += empurra
    return Y


# ——— palavras ———
# Relato longo tem mais palavras de tudo. Comparar "quantos relatos do
# aglomerado têm a palavra" com o arquivo inteiro fazia os aglomerados de
# desabafo longo parecerem característicos de TUDO — medido: «umbanda e
# terreiro» saía com 21 dos 22 motivos e ficava em segundo para qualquer sonho
# comprido. A taxa agora é por palavra distinta escrita (a mesma contagem,
# dividida pelo quanto se escreve ali), puxada para a do arquivo quando a
# evidência é pouca: aglomerado pequeno precisa de mais para se destacar.
ENCOLHE = 3000          # pseudo-contagem, em palavras distintas


def elevacao(x, U_c, x_arquivo, U):
    """quantas vezes a raiz (ou o motivo) é mais comum no aglomerado do que no
    arquivo, por palavra distinta escrita"""
    rg = x_arquivo / U
    return ((x + ENCOLHE * rg) / (U_c + ENCOLHE)) / rg


def caracteristicas(df_c, n_c, U_c, df, U, lift_min=2.0, doc_min=5):
    """raízes frequentes no aglomerado e raras no arquivo, da mais à menos"""
    esc = []
    for r, x in df_c.items():
        if x < doc_min or df[r] < 20:
            continue
        lift = elevacao(x, U_c, df[r], U)
        if lift < lift_min:
            continue
        esc.append((x / n_c * math.log(lift), r))
    esc.sort(key=lambda e: (-e[0], e[1]))
    return [r for _, r in esc]


def main():
    SAIDA.mkdir(exist_ok=True)
    (SAIDA / 'ilhas').mkdir(exist_ok=True)
    print('lendo o planeta…', flush=True)
    reg, textos, cuidado, bytes_pontos = ler_planeta()
    n_planeta = len(reg)
    ok = reg['camada'] == 0
    ok[list(cuidado)] = False
    idx = np.nonzero(ok)[0]
    X = reg['pos'][idx].astype('float64')
    bits = reg['bits'][idx]
    anos = reg['ano'][idx]
    N = len(idx)
    print(f'{N} relatos no mar ({n_planeta - N} de fora: propaganda e cuidado)', flush=True)

    print(f'k-means em {K} ilhas…', flush=True)
    C, rotulo = kmeans(X, K, SEMENTE)
    conta = np.bincount(rotulo, minlength=K)
    print(f'  tamanhos: mín {conta.min()} · mediana {int(np.median(conta))} · máx {conta.max()}')

    print('fatiando as palavras…', flush=True)
    df = Counter()
    df_c = [Counter() for _ in range(K)]
    formas = defaultdict(Counter)
    motivo_de = defaultdict(list)
    for m, rs in MOTIVO_RAIZES.items():
        for r in rs:
            motivo_de[r].append(m)
    motivos_c = [Counter() for _ in range(K)]      # relatos com alguma palavra do motivo
    U_c = np.zeros(K)                              # palavras distintas escritas, por ilha
    for j, i in enumerate(idx):
        rs = set()
        for r, f in fatiar(textos[i][:3000]):
            rs.add(r)
            formas[r][f] += 1
        df.update(rs)
        c = rotulo[j]
        df_c[c].update(rs)
        U_c[c] += len(rs)
        motivos_c[c].update({m for r in rs for m in motivo_de.get(r, ())})
    U = U_c.sum()
    # forma de exibição: a grafia mais comum da raiz (com acento)
    forma = {r: min(fc.items(), key=lambda x: (-x[1], x[0]))[0] for r, fc in formas.items()}
    print(f'  {len(df)} raízes')

    # ——— layout ———
    print('estendendo o mar (t-SNE dos centróides)…', flush=True)
    V3 = vizinhas(C, VIZINHAS)
    Cc = C - C.mean(0)
    _, _, Vt = np.linalg.svd(Cc, full_matrices=False)
    Y0 = Cc @ Vt[:2].T
    Y = tsne(C, Y0, PERPLEXIDADE)
    raio = np.clip(RAIO_MEDIANO * (conta / np.median(conta)) ** 0.42, RAIO_MIN, RAIO_MAX)
    dmin = np.sqrt(((Y[:, None] - Y[None]) ** 2).sum(-1))
    np.fill_diagonal(dmin, np.inf)
    Y *= DIST_VIZINHA / np.median(dmin.min(1))
    Y = afastar(Y, raio, FOLGA)
    Y -= Y.min(0) - (RAIO_MAX + 1500)          # margem de mar aberto em volta
    medidas = {
        'vizinhas': VIZINHAS,
        'preservadas_tsne': round(regua(V3, Y), 3),
        'preservadas_pca': round(regua(V3, Y0), 3),
        'acaso': round(VIZINHAS / (K - 1), 3),
    }
    print(f"  régua: {100 * medidas['preservadas_tsne']:.0f}% das {VIZINHAS} vizinhas preservadas "
          f"(PCA {100 * medidas['preservadas_pca']:.0f}%, acaso {100 * medidas['acaso']:.1f}%)")

    # ——— ilhas: nome, palavras, tempero, motivos ———
    print('batizando…', flush=True)
    ilhas, usados = [], set()
    for c in range(K):
        n_c = int(conta[c])
        membros = np.nonzero(rotulo == c)[0]
        b = bits[membros]
        cands = [r for r in caracteristicas(df_c[c], n_c, U_c[c], df, U)
                 if normalizar(forma[r]) not in NAO_BATIZA
                 and not re.search(r'(.)\1\1', forma[r])]       # "simmmm", "afff"
        palavras = list(dict.fromkeys(forma[r] for r in cands))[:8]
        nome = None
        # aglomerado de fórmula ("meu sonho", "que pesadelo"): o nome é a
        # própria fórmula; se ela já batizou outra ilha, a seguinte mais dita
        curtos = Counter(re.sub(r'\s+', ' ', textos[idx[j]].strip().lower())
                         for j in membros if len(textos[idx[j]].strip()) <= 40)
        formulas = sorted(curtos.items(), key=lambda x: (-x[1], x[0]))
        if formulas and formulas[0][1] >= 0.25 * n_c:
            for f, q in formulas:
                if q < max(3, 0.01 * n_c):
                    break
                if set(re.findall(r'\w+', normalizar(f))) & PALAVRAO:
                    continue
                if f'«{f}»' not in usados:
                    nome = f'«{f}»'
                    break
        if nome is None and len(palavras) >= 2:
            pares = [(a, z) for z in range(1, len(palavras)) for a in range(z)]
            for a, z in pares:
                pa, pz = normalizar(palavras[a]), normalizar(palavras[z])
                if pa[:4] == pz[:4]:            # "dormi e dormir"
                    continue
                if f'{palavras[a]} e {palavras[z]}' not in usados:
                    nome = f'{palavras[a]} e {palavras[z]}'
                    break
        if nome is None:
            base = palavras[0] if palavras else (f'«{formulas[0][0]}»' if formulas else 'ilha')
            nome, k2 = base, 2
            while nome in usados:
                nome = f'{base} {k2}'
                k2 += 1
        usados.add(nome)
        mot = {}
        for m, rs in MOTIVO_RAIZES.items():
            no_arquivo = sum(df[r] for r in rs)
            if motivos_c[c][m] / n_c < 0.03 or not no_arquivo:
                continue
            forca = math.log2(elevacao(sum(df_c[c][r] for r in rs), U_c[c], no_arquivo, U)) / 2
            if forca >= 0.15:
                mot[m] = round(min(forca, 1.0), 2)
        ilhas.append({
            'id': c,
            'x': round(float(Y[c, 0])), 'y': round(float(Y[c, 1])),
            'r': round(float(raio[c])),
            'n': n_c,
            'nome': nome,
            'pal': palavras,
            'lit': round(float(np.mean(b & 1 > 0)), 2),
            'fig': round(float(np.mean(b & 2 > 0)), 2),
            'inc': round(float(np.mean(b & 4 > 0)), 2),
            'pes': round(float(np.mean(b & 256 > 0)), 2),
            'ano': int(np.median(anos[membros])),
            'mot': mot,
            'viz': [int(v) for v in V3[c]],
        })

    # ——— amostras de sonhos ———
    print('escolhendo os sonhos de cada ilha…', flush=True)
    rng = np.random.default_rng(SEMENTE)
    total_amostra = 0
    for c in range(K):
        membros = np.nonzero(rotulo == c)[0]
        quantos = int(np.clip(round(6 + 4 * math.log2(max(conta[c], 1) / 100)), 6, 28))
        d = ((X[membros] - C[c]) ** 2).sum(1)
        ordem_centro = membros[np.argsort(d, kind='stable')]
        ordem_acaso = rng.permutation(membros)

        escolhidos, vistos = [], set()

        def tentar(ordem, ate, estrito):
            for j in ordem:
                if len(escolhidos) >= ate:
                    return
                t = textos[idx[j]].strip()
                if not ((TEXTO_MIN <= len(t) <= TEXTO_MAX) if estrito else len(t) >= 2):
                    continue
                chave = normalizar(re.sub(r'\W+', ' ', t))[:80]
                if chave in vistos:          # o mesmo texto repostado por muitos: uma vez só
                    continue
                vistos.add(chave)
                escolhidos.append(j)

        # primeiro só os de tamanho bom de ler; se faltarem (ilhas de fórmula,
        # "meu sonho"), os curtos e os longos (cortados) completam
        for estrito in (True, False):
            tentar(ordem_centro, quantos // 2, estrito)
            tentar(ordem_acaso, quantos, estrito)
            if len(escolhidos) >= quantos:
                break
        sonhos = []
        for j in escolhidos:
            i = int(idx[j])
            t = textos[i].strip()
            if len(t) > TEXTO_MAX:
                t = t[:TEXTO_MAX].rsplit(' ', 1)[0] + '…'
            bb = int(bits[j])
            sonhos.append({'t': t, 'a': int(anos[j]),
                           'b': (bb & 7) | ((bb >> 5) & 8),     # 1 dormindo · 2 desejo · 4 incerto · 8 pesadelo
                           'p': i})
        ilhas[c]['ns'] = len(sonhos)
        total_amostra += len(sonhos)
        json.dump({'id': c, 'sonhos': sonhos}, open(SAIDA / 'ilhas' / f'{c}.json', 'w'),
                  ensure_ascii=False, separators=(',', ':'))
    print(f'  {total_amostra} sonhos nas amostras')

    # ——— índice raiz → ilhas ———
    print('índice das palavras…', flush=True)
    raizes, dfs, listas = [], [], []
    for r in sorted(df):
        if df[r] < 5 or df[r] > N // 8:
            continue
        idf = math.log(N / df[r])
        pesos = []
        for c in range(K):
            x = df_c[c].get(r, 0)
            if x < 2:
                continue
            lift = elevacao(x, U_c[c], df[r], U)
            if lift < 1.5:
                continue
            pesos.append((idf * math.log(lift), c))
        if not pesos:
            continue
        pesos.sort(key=lambda p: (-p[0], p[1]))
        plano = []
        for w, c in pesos[:20]:
            plano += [c, max(1, round(w * 4))]
        raizes.append(r)
        dfs.append(df[r])
        listas.append(plano)
    json.dump({
        'versao': 1,
        'total': N,
        'paradas': PARADAS,
        'riso': RISO,
        'limpar': LIMPAR,
        'sufixos': SUFIXOS,
        'min_raiz': 4,
        'raizes': raizes,
        'df': dfs,
        'ilhas': listas,        # por raiz: [ilha, peso×4, ilha, peso×4, …]
    }, open(SAIDA / 'palavras.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print(f'  {len(raizes)} raízes no índice')

    largura = int(Y[:, 0].max() + RAIO_MAX + 1500)
    altura = int(Y[:, 1].max() + RAIO_MAX + 1500)
    json.dump({
        'versao': 1,
        'planeta': {'n': n_planeta, 'bytes_pontos': bytes_pontos},
        'total': N,
        'mar': {'largura': largura, 'altura': altura},
        'medidas': medidas,
        'motivos': MOTIVO_RAIZES,
        'ilhas': ilhas,
    }, open(SAIDA / 'mundo.json', 'w'), ensure_ascii=False, separators=(',', ':'))

    mb = lambda p: p.stat().st_size / 1e6
    pasta = SAIDA / 'ilhas'
    print(f"\nmundo.json {mb(SAIDA / 'mundo.json'):.2f}MB · palavras.json "
          f"{mb(SAIDA / 'palavras.json'):.2f}MB · ilhas/ "
          f"{sum(mb(p) for p in pasta.glob('*.json')):.2f}MB em {K} arquivos")
    print(f'mar de {largura}×{altura} passos')


if __name__ == '__main__':
    main()
