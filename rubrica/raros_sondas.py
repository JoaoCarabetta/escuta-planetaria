#!/usr/bin/env python3
"""Candidatos a valores RAROS de afeto/atribuição — via 1 (sonda) + via 2 (palavras).

Por quê: o sorteio uniforme dos 15 mil de afeto (Sonnet) confirma o que é
comum e quase nada do que é raro — em 7.300 literais vieram 39 alívios, 10
mortos, 2 terapias. Anotar mais às cegas custa caro para pouca informação
nova sobre esses valores. Aqui repetimos o método que funcionou para a
bandeira (`risco_sonda_v351.py` + `risco_palavras.py`): uma sonda linear no
embedding bge-m3 por classe rara, e listas de palavras medidas nos rótulos;
a interseção das duas é o que mais vale mandar ao anotador.

Rótulos (só leitura, só os campos comuns a todos os lotes):
  A  afeto15k/a_*_anotado.jsonl — Sonnet, sorteio UNIFORME entre literais
     (exceto a fatia `via: indeciso`, menor margem do portão: entra no
     treino, NÃO entra na calibração/medida, porque não é a população).
  F  v35/final_v35.jsonl — Opus, bolsas PESCADAS (enriquecidas). Entra no
     treino (traz positivos), nunca na medida: inflaria a precisão.
  P  v35/prova_*_anotado.jsonl — Opus, a PROVA: fica fora do treino e só
     serve de segunda medida. Esses ids nunca vão para anotação.
Carga/despertar/atribuição só valem sob portão literal: a sonda treina e é
medida só entre os anotados como literais.

Validação: predição FORA-DA-DOBRA (5 dobras em A∪F); a força C da
regularização é a de melhor AP fora-da-dobra nos sorteados de A (leve
otimismo: escolher C e medir no mesmo conjunto; a prova P é a medida limpa,
mas tem poucos positivos). As métricas — AP, precisão nos topos 50/200 —
são nos sorteados de A: é a proporção real do arquivo.

Calibração: a sonda treina em A∪F, que tem mais positivos que o arquivo;
a probabilidade crua superestima. Um logístico de 3 parâmetros, ajustado nos
sorteados de A (TODOS, incluindo os que o Sonnet chamou de não literais —
no arquivo aberto eles também estão lá), lê [logit(sonda fora-da-dobra),
bate palavra?] e devolve p_cal — a chance de o anotador confirmar a classe.
A média de p_cal nos candidatos é a precisão ESPERADA; a soma, quantos
exemplos novos esperar.

Classes com < MIN_POS positivos no treino não têm sonda (sobreajusta): o
escore é a similaridade de cosseno média com os 3 positivos conhecidos mais
próximos (vizinho mais próximo), medida por deixar-um-fora; e só entram
candidatos que batem palavra, ordenados por essa similaridade.

Universo pontuado: canônicos, p_literal ≥ 0,5, NÃO anotados em lote nenhum,
fora dos lotes de afeto15k ainda por anotar, fora da prova e da revisão
cega, e fora de tudo que o cuidado esconde (bandeira em qualquer
conferência — mesma lógica de `risco_rotulos.carregar` + `lotes_afeto15k`).

  python3 raros_sondas.py  →  <scratch>/raros/universo_ids.txt
                              <scratch>/raros/p_sonda.npy  (U × classes, cru)
                              <scratch>/raros/p_cal.npy    (U × classes)
                              <scratch>/raros/palavras.jsonl (id → termos por classe)
                              <scratch>/raros/validacao.json, termos.tsv
Lê o banco só para leitura; não grava nada no banco nem na página.
"""
import glob
import warnings
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedKFold

# numpy 2 + Accelerate (macOS) solta avisos espúrios de overflow no matmul do sklearn
warnings.filterwarnings('ignore', category=RuntimeWarning)

sys.path.insert(0, str(Path(__file__).parent))
import risco_rotulos as R
from risco_palavras import normalizar

AQUI = Path(__file__).parent
LOTES = AQUI / 'lotes'
SCRATCH = Path('/private/tmp/claude-501/-Users-fitipe-Desktop-arte-c-joao-tta/'
               'e9da8b04-cc60-40d3-99e1-9659aa0a463e/scratchpad/raros')
SEMENTE = 2809
CS = (0.25, 1, 4, 16)
MIN_POS = 15          # abaixo disso: sem sonda, só palavras + vizinho mais próximo
K_VIZ = 3
CAMPOS = ('portao', 'carga', 'conteudo', 'despertar', 'figura', 'atribuicao_palavra',
          'atribuicao_origem', 'atribuicao_postura', 'atribuicao_quem', 'marcas', 'confianca')

# classe → (campo, valor); 'tem_atribuicao' é qualquer atribuição
CLASSES = {
    'alivio': ('despertar', 'alivio'),
    'acordou_bem': ('despertar', 'acordou_bem'),
    'desorientado': ('despertar', 'desorientado'),
    'acordou_neutro': ('despertar', 'acordou_neutro'),
    'decepcao': ('despertar', 'decepcao'),
    'mista': ('carga', 'mista'),
    'estranha': ('carga', 'estranha'),
    'tem_atribuicao': (None, None),
    'o_entidade_religiosa': ('atribuicao_origem', 'entidade_religiosa'),
    'o_morto': ('atribuicao_origem', 'morto'),
    'o_espirito_proprio': ('atribuicao_origem', 'espirito_proprio'),
    'o_outra': ('atribuicao_origem', 'outra'),
    'q_familia': ('atribuicao_quem', 'familia'),
    'q_religioso': ('atribuicao_quem', 'religioso'),
    'q_doutrina_literatura': ('atribuicao_quem', 'doutrina_literatura'),
    'q_oraculo': ('atribuicao_quem', 'oraculo'),
    'q_heranca': ('atribuicao_quem', 'heranca'),
    'q_terapia': ('atribuicao_quem', 'terapia'),
    'se_cumpriu': ('marcas', 'se_cumpriu'),
}
NOMES = list(CLASSES)

# ---------------------------------------------------------------- palavras
# Regex sobre o texto normalizado (minúsculo, sem acento). Listas AMPLAS de
# propósito: a precisão de cada termo é medida nos rótulos e o termo que não
# presta sai sozinho (ver PREC_TERMO em escolher_termos).
_S = r'(so |apenas )?(um |uma )?'
PALAVRAS = {
    'alivio': [r'que alivio', r'aliviad', r'\balivio', rf'ainda bem que (era|foi) {_S}sonho',
               rf'gracas a deus (que )?(era|foi) {_S}sonho', r'\bufa+\b', rf'(que bom|felizmente) que (era|foi) {_S}sonho',
               r'(ainda bem|gracas a deus|que bom) que (eu )?acordei', r'era so um (sonho|pesadelo)',
               r'(respirei|suspirei) (fundo|aliviad)', r'nao passou de um (sonho|pesadelo)'],
    'acordou_bem': [r'acordei (tao |muito |super |mt |mto |mo |todo |toda )?(feliz|rindo|sorrindo|leve|bem\b|em paz|de bom humor|renovad|animad|radiante|contente|alegre|tranquil|descansad|revigorad|apaixonad|emocionad|com saudade boa)',
                    r'acordar (tao )?(feliz|sorrindo|rindo|leve|em paz)', r'acordei com (um )?sorriso', r'acordei (com o )?coracao (quentinho|leve|aquecido|quente)',
                    r'coracao quentinho', r'(me )?deixou (o dia|meu dia) (mais )?(feliz|leve|melhor)', r'ganhei (o|meu) dia',
                    r'acordei (de )?bom humor', r'acordei (me sentindo|sentindo) (bem|leve|feliz|em paz|amad)'],
    'desorientado': [r'acordei (meio |todo |toda |super |muito )?confus', r'sem saber onde (eu )?(estava|tava|to|estou)',
                     r'demorei (pra|para|a|um tempo pra) (entender|perceber|cair a ficha|me situar|acreditar)',
                     r'nao sabia se (era|foi|tinha sido) (real|sonho|verdade)', r'nao sei se (foi|era) (sonho|real)',
                     r'(achei|pensei|jurava) que (era|tinha sido|fosse|tivesse sido) (real|verdade)', r'confus[oa] se (era|foi)',
                     r'custei a (acreditar|entender|perceber)', r'sera que (foi|era) (real|sonho)', r'(desorientad|atordoad|zonz)',
                     r'(realidade|real) ou (sonho|nao)', r'fiquei (um tempo|uns minutos|alguns minutos|um tempao) (sem saber|tentando|pensando se)',
                     r'nao sei o que e (real|realidade)', r'sem saber o que (e|era) (real|realidade|sonho)'],
    'acordou_neutro': [r'\b(ai|entao|e|dai|ate que|quando) (eu )?acordei\b', r'acordei (no meio|antes|na hora|bem na hora|logo)',
                       r'\be acordei\b', r'(me )?acordaram', r'despertador', r'acordei com (o|a|um|uma) (barulho|som|alarme|despertador|gato|cachorro|mae|luz)'],
    'decepcao': [r'queria (voltar|continuar) (a dormir|pro sonho|para o sonho|no sonho|dormindo|sonhando|nele)', r'nao queria (ter )?acorda',
                 rf'pena que (era|foi) {_S}sonho', r'acordei (tao |muito |mt |bem )?(triste|chatead|frustrad|decepcionad|bolad|arrasad|na bad)',
                 rf'(infelizmente|que pena|pena que) (era|foi|nao passou de) {_S}sonho', r'por ?que (eu )?(fui )?acord', r'odeio (ter que )?acordar',
                 r'(voltar|volta) a dormir (pra|para)', r'queria que (fosse|tivesse sido) (real|verdade)', r'(que|q) (pena|triste|tristeza|decepcao)',
                 r'queria (tanto )?que (nao )?(acabasse|terminasse|fosse verdade|continuasse)', r'(me )?(acordou|acordaram|acordou) (bem )?(na melhor|justo)',
                 r'na melhor parte', r'era bom demais pra ser verdade', r'acordar (foi|e) (triste|horrivel|decepcionante)', r'\bso (no|em) sonho\b'],
    'mista': [r'(misto|mistura|misturad)', r'ao mesmo tempo', r'(bom e ruim|ruim e bom|lindo e (triste|assustador)|feliz e triste|triste e feliz|alegre e triste|agridoce|bittersweet)',
              r'nao sei se (foi|era|e) (bom|ruim|pesadelo)', r'(pesadelo|sonho) (bom|lindo) (e|mas) (triste|ruim|assustador)',
              r'sentimentos? (confus|misturad|contradit)', r'(lindo|bom|feliz),? mas (triste|doeu|doloroso|assustador)', r'(triste|assustador),? mas (lindo|bom|feliz)'],
    'estranha': [r'sonh[oe]s? (muito |mt |mto |super |tao |mais |meio |bem |mo )?(estranh|bizarr|doid|louc|maluc|esquisit|surreal|sem sentido|aleatori|nonsense|insano|psicodelic|pirad|random)',
                 r'que (sonho )?(estranho|bizarro|doido|loucura|esquisito|surreal|aleatorio)', r'sonhei (umas|cada) (coisa|parada)', r'sem pe nem cabeca',
                 r'\bwtf\b', r'(estranh|bizarr|esquisit)', r'cada sonho', r'\bnada a ver\b'],
    'tem_atribuicao': [r'significad', r'o que (sera que |sera )?(isso |esse sonho )?(significa|quer dizer)', r'\bsignifica\b', r'sera (que )?(e |foi )?(um )?(sinal|aviso|recado)',
                       r'\bsinal\b', r'\baviso\b', r'premoni', r'subconsciente|inconsciente', r'\bmensagem', r'(deus|universo|o senhor) (me )?(mostrou|mandou|avisou|falou|quer|revelou)',
                       r'livramento', r'interpret', r'quer (me )?dizer', r'\bfreud', r'(cerebro|mente) (ta|esta|quer|tentando|me)', r'pressagio|pressentimento',
                       r'\brecado\b', r'alguem sabe (o que|interpretar|o significado)', r'(foi|e|era) (um )?(sinal|aviso|livramento|revelacao)', r'\bespiritual'],
    'o_entidade_religiosa': [r'\borixa', r'pomba ?gira', r'\bexu\b', r'\bcaboclo', r'pret[oa]s? velh[oa]', r'\bmentor', r'\bguias? espiritu', r'(meu|minha|meus|minhas) guias?\b',
                             r'\banjo', r'nossa senhora', r'iemanja|oxum|ogum|oxala|xango|iansa|oxossi|omolu|obaluae|nana buruque', r'\bentidade', r'\bsant[oa]\b',
                             r'deus (me )?(mostrou|revelou|falou|deu|mandou|avisou|disse|queria|quer|fala)', r'(o senhor|jesus|espirito santo) (me )?(mostrou|revelou|falou|disse|avisou)',
                             r'\bjesus\b', r'\brevela', r'maria (padilha|mulambo)', r'ze pilintra', r'\bere\b|\beres\b', r'\bencosto', r'demonio|\bdiabo|\bcapeta|satana',
                             r'\bespirito santo', r'\bumband|candomble|\bterreiro'],
    'o_morto': [r'falecid|faleceu|\bfalecer', r'(que|q) (ja )?morreu', r'que ja se foi|partiu dessa|in memoriam|descanse em paz|que deus (a|o) tenha',
                r'(veio|vem|vinha|voltou) me (visitar|ver|dar (um )?recado|avisar|abracar|dizer)', r'\bme visitou\b', r'\bvisita (dele|dela|do meu|da minha|em sonho|no sonho|espiritual)',
                r'(minha|meu) (avo|vo|vovo|vozinha|mae|pai|painho|mainha|tia|tio|irma|irmao|bisavo|madrinha|padrinho|sogra|sogro|filho|filha|marido|esposa|amiga|amigo|primo|prima)( \w+){0,2} (que )?(ja )?(faleceu|falecid|morreu|se foi|partiu)',
                r'do outro lado|do ceu|la de cima|plano espiritual', r'(morreu|faleceu) (ha|faz) \w+ (anos|meses|dias|semanas)', r'\bveio se despedir|\bse despedir de mim'],
    'o_espirito_proprio': [r'projec(ao|oes) astra', r'viage(m|ns) astra', r'desdobramento', r'(sai|saio|saindo|sair|saiu) do (meu )?corpo', r'fora do (meu )?corpo', r'vidas? passadas?',
                           r'(minha|a) alma (saiu|viaja|viajou|sai|vai)', r'emancipacao da alma', r'mediun', r'(tenho|tive|tem|temos) (o |esse |um )?dom', r'sonhos? premonit',
                           r'intuica', r'sexto sentido', r'clarivid|\bvidente', r'perispirito', r'(meu )?espirito (saiu|viaja|viajou|sai)', r'sonho (acontece|se realiza)',
                           r'(eu )?(sempre )?sonho (com as coisas|antes de acontecer)', r'\bsensitiv'],
    'o_outra': [r'\bkarma|\bcarma', r'\balien|extraterr', r'feitic|macumba|mandinga|trabalho feito|fizeram (um )?trabalho|olho gordo', r'universo paralelo|realidade paralela|multiverso|\bmatrix\b|simulacao',
                r'energia (ruim|negativa|pesada)', r'\bdo alem\b', r'maldic|amaldico|\bpraga\b', r'\bbruxa|\bbruxaria', r'\bfantasma|assombra', r'\bfada\b'],
    'q_familia': [r'(minha|meu) (mae|pai|avo|vo|vovo|tia|tio|irma|irmao|prima|primo|madrinha|familia|sogra|mainha|painho|bisavo)( \w+){0,2} (disse|falou|fala|diz|dizia|falava|explicou|interpretou|acha|achou|jura|sempre diz|sempre fala|sempre dizia) (que|q)\b',
                  r'(minha|meu) (mae|pai|avo|vo|tia|familia) .{0,50}(significa|significado|sinal|aviso|interpret)', r'(segundo|de acordo com) (minha|meu) (mae|avo|vo|tia|familia|pai)',
                  r'minha (mae|vo|avo) (sempre )?(dizia|diz|fala|falava) que sonhar'],
    'q_religioso': [r'(pastor|pastora|padre|mae de santo|pai de santo|obreira|profeta|profetisa|benzedeira|dirigente|medium|guia do terreiro) (disse|falou|revelou|interpretou|confirmou|explicou|me disse|falou que|viu)',
                    r'(contei|falei|perguntei) (pro|pra|para o|para a|com o|com a|ao|a) (meu |minha )?(pastor|pastora|padre|mae de santo|pai de santo|zelador|zeladora)', r'\bpastor', r'\bpadre\b', r'(mae|pai) de santo', r'\bmae pequena|\bpai pequeno', r'babalorix|ialorix|yalorix', r'\bobreir', r'\bprofeta|\bprofetiz|\bprofecia',
                    r'\bbenzedeir', r'\bcentro espirita', r'\bterreiro', r'\b(na|da) igreja|\bno culto', r'\bmedium\b', r'\bcambon', r'lider (da igreja|espiritual)', r'\bxama', r'\bdirigente'],
    'q_doutrina_literatura': [r'(segundo|de acordo com|pra|para|como diz|como dizia) (o )?(freud|jung|kardec|a biblia|o espiritismo|a psicanalise|a umbanda|o candomble)',
                              r'freud explica', r'kardec', r'espiritism|\bespirita\b', r'livro dos (espiritos|sonhos|mediuns)', r'\bfreud', r'\bjung', r'(dicionario|significado) dos sonhos',
                              r'\bbiblia|\bbiblic|\bversiculo|\bgenesis|jose do egito', r'\b(li|lendo|leio|lido) (que|em|num|no|sobre|um|uma)\b',
                              r'segundo (a|o) (psicanalise|ciencia|pesquisa|estudo|biblia|espiritismo|umbanda|candomble|tradicao)', r'\bestudos?\b|\bpesquisa|cientist', r'neurocien',
                              r'chico xavier|andre luiz|\bemmanuel\b', r'psicanalise'],
    'q_oraculo': [r'(taro|tarot|cartas|buzios|baralho|oraculo) (confirmou|confirmaram|disse|disseram|falou|falaram|mostrou|mostraram|deu|saiu)',
                  r'(tiragem|jogo de buzios|jogar buzios|abrir (o|um) jogo)', r'\btarot?\b|\btarolog', r'\bbuzios', r'cartoman', r'baralho cigano|\bcigana\b', r'(tirei|tirou|jogar|joguei|jogou|tiragem) (as |de |uma )?cartas?', r'astrolog|mapa astral|\bsigno\b|retrogrado',
                  r'numerolog', r'jogo do bicho|\bno bicho\b|palpite', r'\bi ching|\brunas\b|\boraculo'],
    'q_heranca': [r'(bisavo|tataravo|avo|\bvo\b|familia|mae|tia).{0,80}(\bdom\b|benzedeir|curandeir|mediun|vidente|premonit|parteira|rezadeir)', r'herdei|herdad|heranca',
                  r'(vem|veio|coisa|e) de familia', r'na minha familia (todo mundo|todos|as mulheres|sempre|tem)', r'(puxei|puxou) (da|a|de) minha (vo|avo|mae|bisavo)',
                  r'(eu e minha|minha) (vo|avo|mae) (tambem )?(temos|tinha|tem|tinhamos|tivemos|ja tivemos)'],
    'q_terapia': [r'(levei|levar|levo|contei|contar|falei|falar|trazer|trouxe) (isso |esse sonho |o sonho |esse |ele )?(pra|para|na|a|pro|com|no) (minha |meu |a |o )?(terapia|terapeuta|psicologa|psicologo|analista|psicanalista|psi|analise|sessao)\b',
                  r'(minha|meu) (terapeuta|psicologa|psicologo|analista|psicanalista|psi|psiquiatra) (disse|falou|acha|achou|interpretou|explicou|perguntou|diz|fala|sugeriu)',
                  r'(pauta|assunto|material) (pra|para) (a |minha )?(terapia|sessao|analise)', r'psicolog', r'\banalista\b', r'terapeut', r'\bterapia', r'psicanal', r'psiquiatr', r'\bminha psi\b', r'\bsessao\b'],
    'se_cumpriu': [r'aconteceu de verdade', r'se realiz', r'no dia seguinte', r'realmente aconteceu', r'no outro dia', r'(dias|semanas|meses|horas) depois',
                   r'(se|me) (concretizou|cumpriu)', r'virou (realidade|verdade)', r'(aconteceu|acontecer) (de verdade|igualzinho|exatamente|igual|mesmo)',
                   r'nao deu outra', r'dito e feito', r'(tudo|sempre) que (eu )?sonho (acontece|se realiza)', r'premonit', r'fiquei sabendo que', r'recebi a noticia',
                   r'nao e que', r'na mesma (noite|semana)|no mesmo dia', r'(aconteceu|acontece) (tudo )?(igual|igualzinho|como no sonho)', r'sonhei e aconteceu',
                   r'(ligou|mandou mensagem|apareceu) (hoje|no dia|de manha)'],
}
_RX = {c: [re.compile(t) for t in ts] for c, ts in PALAVRAS.items()}
_RX_UNIAO = {c: re.compile('|'.join(f'(?:{t})' for t in ts)) for c, ts in PALAVRAS.items()}


def termos_batidos(texto_norm):
    """{classe: [índices dos termos que batem]} — união primeiro, termo a termo só se bater."""
    out = {}
    for c, rx in _RX_UNIAO.items():
        if rx.search(texto_norm):
            ks = [k for k, r in enumerate(_RX[c]) if r.search(texto_norm)]
            if ks:
                out[c] = ks
    return out


# ---------------------------------------------------------------- rótulos
def _jsonl(caminho):
    for l in open(caminho):
        if l.strip():
            yield json.loads(l)


def classes_de(x):
    """Conjunto de classes raras presentes numa anotação (só vale se literal)."""
    if 'literal' not in (x.get('portao') or []):
        return None
    s = set()
    for c, (campo, valor) in CLASSES.items():
        if campo is None:
            if x.get('atribuicao_palavra') or x.get('atribuicao_origem') or x.get('atribuicao_quem'):
                s.add(c)
        elif valor in (x.get(campo) or []):
            s.add(c)
    return s


def carregar_rotulos():
    """id → dict(fonte 'A'|'F'|'P', sorteio bool, literal bool, classes set)."""
    via = {}
    for f in glob.glob(str(LOTES / 'afeto15k' / 'a_*.jsonl')):
        if f.endswith('_anotado.jsonl'):
            continue
        for x in _jsonl(f):
            via[x['id']] = x.get('via')
    rot = {}
    for f in sorted(glob.glob(str(LOTES / 'afeto15k' / 'a_*_anotado.jsonl'))):
        for x in _jsonl(f):
            x = {k: x.get(k) for k in ('id',) + CAMPOS}
            cl = classes_de(x)
            rot[x['id']] = dict(fonte='A', sorteio=via.get(x['id']) == 'sorteio', literal=cl is not None, classes=cl or set())
    for x in _jsonl(LOTES / 'v35' / 'final_v35.jsonl'):
        cl = classes_de(x)
        rot.setdefault(x['id'], dict(fonte='F', sorteio=False, literal=cl is not None, classes=cl or set()))
    for f in sorted(glob.glob(str(LOTES / 'v35' / 'prova_*_anotado.jsonl'))):
        for x in _jsonl(f):
            cl = classes_de(x)
            rot[x['id']] = dict(fonte='P', sorteio=False, literal=cl is not None, classes=cl or set())
    return rot


def ids_jsonl(padrao):
    s = set()
    for f in glob.glob(str(LOTES / padrao), recursive=True):
        for l in open(f):
            try:
                s.add(json.loads(l)['id'])
            except Exception:
                pass
    return s


def excluidos(con):
    """Tudo que não pode virar candidato: já anotado, por anotar (afeto15k),
    prova, revisão cega, e tudo que o cuidado esconde ou deveria esconder."""
    fora = {r[0] for r in con.execute('SELECT relato_id FROM anotacoes_v3')}
    fora |= {r[0] for r in con.execute('SELECT relato_id FROM amostra_prova')}
    fora |= {r[0] for r in con.execute('SELECT relato_id FROM predicoes_v35 WHERE bandeira = 1')}
    fora |= (ids_jsonl('v3*/**/*.jsonl') | ids_jsonl('afeto15k/*.jsonl') | ids_jsonl('revisao_cega_fitipe.jsonl')
             | ids_jsonl('revisao_cega_GABARITO_nao_abrir.jsonl') | ids_jsonl('cuidado_manual.jsonl') | ids_jsonl('sabado_26-09.jsonl')
             | ids_jsonl('raros/*_anotado.jsonl'))    # os r_*.jsonl desta rodada NÃO: regerar tem de dar o mesmo
    # bandeira: positivo em qualquer conferência, ou ambíguo, ou escondido na página
    rotulo, conferidos, _ = R.carregar(con)
    fora |= {r for r, v in rotulo.items() if v == 1}
    fora |= {r for r in conferidos if r not in rotulo}
    return fora


def embeddings(con, ids):
    X = np.zeros((len(ids), 1024), np.float32)
    pos = {r: k for k, r in enumerate(ids)}
    for k in range(0, len(ids), 900):
        q = ids[k:k + 900]
        for rid, b in con.execute(f"SELECT id, embedding FROM relatos WHERE id IN ({','.join('?' * len(q))})", q):
            if b:
                X[pos[rid]] = np.frombuffer(b, '<f4')
    n = np.linalg.norm(X, axis=1, keepdims=True)
    return X / np.maximum(n, 1e-9)


# ---------------------------------------------------------------- medidas
def prec_topo(y, s, k):
    o = np.argsort(-s)[:k]
    return round(float(y[o].mean()), 3) if len(o) else None


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def sonda_cv(X, y, grupos_medida):
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    """OOF em 5 dobras para cada C; devolve (C, oof, ap por C)."""
    cv = StratifiedKFold(5, shuffle=True, random_state=SEMENTE)
    melhor = None
    aps = {}
    for C in CS:
        oof = np.zeros(len(y))
        for a, b in cv.split(X, y):
            m = LogisticRegression(C=C, max_iter=3000).fit(X[a], y[a])
            oof[b] = m.predict_proba(X[b])[:, 1]
        aps[C] = average_precision_score(y[grupos_medida], oof[grupos_medida])
        if melhor is None or aps[C] > aps[melhor[0]]:
            melhor = (C, oof)
    return melhor[0], melhor[1], aps


def vizinho(Epos, Q, excluir_self=None):
    """média das K_VIZ maiores similaridades de cada linha de Q com os positivos."""
    S = Q @ Epos.T
    if excluir_self is not None:           # (linha de Q, coluna de Epos) que é o próprio texto
        for i, j in excluir_self:
            S[i, j] = -1
    k = min(K_VIZ, S.shape[1])
    return np.sort(S, axis=1)[:, -k:].mean(1)


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    con = R.conectar()
    rot = carregar_rotulos()
    ids_rot = sorted(rot)
    print(f'rotulados: {len(ids_rot)} · A {sum(v["fonte"] == "A" for v in rot.values())} '
          f'(sorteio {sum(v["sorteio"] for v in rot.values())}) · F {sum(v["fonte"] == "F" for v in rot.values())} '
          f'· P {sum(v["fonte"] == "P" for v in rot.values())}')

    # textos e palavras dos rotulados
    txt = {}
    for k in range(0, len(ids_rot), 900):
        q = ids_rot[k:k + 900]
        txt.update(con.execute(f"SELECT id, texto FROM relatos WHERE id IN ({','.join('?' * len(q))})", q))
    bat_rot = {i: termos_batidos(normalizar(txt.get(i, ''))) for i in ids_rot}
    Xr = embeddings(con, ids_rot)
    tem_emb = np.abs(Xr).sum(1) > 0

    fonte = np.array([rot[i]['fonte'] for i in ids_rot])
    sorteio = np.array([rot[i]['sorteio'] for i in ids_rot])
    literal = np.array([rot[i]['literal'] for i in ids_rot])
    Y = {c: np.array([c in rot[i]['classes'] for i in ids_rot], int) for c in NOMES}
    treino = literal & np.isin(fonte, ['A', 'F']) & tem_emb       # onde a sonda aprende
    medida = treino & sorteio                                        # onde se mede (população real)
    calib = sorteio & tem_emb                                        # A sorteado, literal ou não
    prova = literal & (fonte == 'P') & tem_emb

    # ------------- precisão de cada termo nos rotulados
    linhas_t = []
    for c in NOMES:
        for k, t in enumerate(PALAVRAS[c]):
            h = np.array([k in bat_rot[i].get(c, []) for i in ids_rot])
            hp, ha = h & treino, h & medida
            linhas_t.append(dict(classe=c, k=k, termo=t, bate_AF=int(hp.sum()), pos_AF=int(Y[c][hp].sum()),
                                 prec_AF=round(Y[c][hp].mean(), 3) if hp.any() else None,
                                 bate_A=int(ha.sum()), pos_A=int(Y[c][ha].sum()),
                                 prec_A=round(Y[c][ha].mean(), 3) if ha.any() else None))

    # ------------- universo
    fora = excluidos(con)
    print(f'excluídos (anotados/por anotar/prova/cuidado): {len(fora)}')
    uni = [r for (r,) in con.execute("""SELECT r.id FROM relatos r JOIN predicoes_v35 p ON p.relato_id = r.id
                                        WHERE r.canonico_de IS NULL AND p.p_literal >= 0.5 AND r.embedding IS NOT NULL""")
           if r not in fora and r not in rot]
    print(f'universo: {len(uni)} literais canônicos não anotados')
    Eu = embeddings(con, uni)
    bat_uni = []
    for k in range(0, len(uni), 900):
        q = uni[k:k + 900]
        d = dict(con.execute(f"SELECT id, texto FROM relatos WHERE id IN ({','.join('?' * len(q))})", q))
        bat_uni.extend(termos_batidos(normalizar(d[i])) for i in q)
    # alcance de cada termo no universo
    alc = defaultdict(int)
    for b in bat_uni:
        for c, ks in b.items():
            for k in ks:
                alc[(c, k)] += 1
    for l in linhas_t:
        l['universo'] = alc[(l['classe'], l['k'])]

    # termos aceitos: precisão em A∪F ≥ PREC_TERMO com ≥2 acertos, ou sem medida
    # e alcance pequeno (termo raro demais para medir — só nas classes sem sonda)
    def aceitos(c, sem_sonda):
        base = Y[c][treino].mean()
        out = []
        for l in linhas_t:
            if l['classe'] != c:
                continue
            if l['bate_AF'] >= 3 and l['pos_AF'] >= 2 and l['prec_AF'] >= max(0.15, 4 * base):
                out.append(l['k'])
            # sem medida possível (quase não aparece nos rotulados) e sem erro visto:
            # entra se o alcance no arquivo for pequeno — não pode inundar a fila
            elif l['bate_AF'] < 3 and l['pos_AF'] == l['bate_AF'] and l['universo'] <= (400 if sem_sonda else 200):
                out.append(l['k'])
        return out

    def kw(bat, c, ok):
        return np.array([bool(set(b.get(c, [])) & ok) for b in bat], float)

    val, P_sonda, P_cal = {}, np.zeros((len(uni), len(NOMES)), np.float32), np.zeros((len(uni), len(NOMES)), np.float32)
    termos_ok = {}

    # 1) sondas em paralelo (só os rotulados vão aos processos; o universo fica aqui)
    ok_de, kr_de = {}, {}
    for c in NOMES:
        sem = int(Y[c][treino].sum()) < MIN_POS
        ok_de[c] = set(aceitos(c, sem))
        kr_de[c] = np.array([bool(set(bat_rot[i].get(c, [])) & ok_de[c]) for i in ids_rot], float)
    com_sonda = [c for c in NOMES if Y[c][treino].sum() >= MIN_POS]
    idx = np.where(treino)[0]
    res = Parallel(n_jobs=6)(delayed(sonda_cv)(Xr[idx], Y[c][idx], medida[idx]) for c in com_sonda)

    oof_A = {}
    for c in NOMES:
        j, y, ok, kr = NOMES.index(c), Y[c], ok_de[c], kr_de[c]
        npos = int(y[treino].sum())
        v = dict(positivos_AF=npos, positivos_A_sorteio=int(y[medida].sum()), literais_A_sorteio=int(medida.sum()),
                 positivos_prova=int(y[prova].sum()), base_A=round(float(y[medida].mean()), 4),
                 via='sonda' if c in com_sonda else 'vizinho+palavras', termos_aceitos=[PALAVRAS[c][k] for k in sorted(ok)])
        for nome, g in (('A', medida), ('AF', treino)):
            h = (kr > 0) & g
            v[f'palavras_bate_{nome}'] = int(h.sum())
            v[f'palavras_prec_{nome}'] = round(float(y[h].mean()), 3) if h.any() else None
        ku = kw(bat_uni, c, ok)
        if c in com_sonda:
            C, oof_t, aps = res[com_sonda.index(c)]
            oof = np.full(len(ids_rot), np.nan)
            oof[idx] = oof_t
            m = LogisticRegression(C=C, max_iter=3000).fit(Xr[idx], y[idx])
            resto = np.where(~treino & tem_emb)[0]          # não literais e prova: o modelo nunca os viu
            oof[resto] = m.predict_proba(Xr[resto])[:, 1]
            s_m = oof[medida]
            v.update(C=C, ap_cv={str(k): round(a, 3) for k, a in aps.items()},
                     ap_A=round(average_precision_score(y[medida], s_m), 3),
                     p50_A=prec_topo(y[medida], s_m, 50), p200_A=prec_topo(y[medida], s_m, 200))
            if y[prova].sum():
                v['ap_prova'] = round(average_precision_score(y[prova], oof[prova]), 3)
            cal = LogisticRegression(C=100, max_iter=2000).fit(np.c_[logit(oof[calib]), kr[calib]], y[calib])
            v['calibrador'] = [round(float(z), 3) for z in list(cal.coef_[0]) + [cal.intercept_[0]]]
            pcm = cal.predict_proba(np.c_[logit(s_m), kr[medida]])[:, 1]
            v.update(ap_comb_A=round(average_precision_score(y[medida], pcm), 3),
                     p50_comb_A=prec_topo(y[medida], pcm, 50), p200_comb_A=prec_topo(y[medida], pcm, 200))
            oof_A[c] = np.c_[y[medida], pcm]                 # para conferir a calibração no topo
            pu = m.predict_proba(Eu)[:, 1]
            pc = cal.predict_proba(np.c_[logit(pu), ku])[:, 1]
        else:
            # vizinho mais próximo dos positivos de A∪F, medido deixando-um-fora
            ip = np.where(treino & (y == 1))[0]
            col = {jj: n for n, jj in enumerate(ip)}
            s = vizinho(Xr[ip], Xr[idx], excluir_self=[(n, col[jj]) for n, jj in enumerate(idx) if jj in col])
            v.update(ap_vizinho_AF=round(average_precision_score(y[idx], s), 3), p50_vizinho_AF=prec_topo(y[idx], s, 50))
            pu = vizinho(Xr[ip], Eu)
            # sem calibração possível: p_cal = precisão das palavras em A∪F para quem
            # bate (otimista: F é pescado), 0 para quem não bate
            pc = ku * (v['palavras_prec_AF'] or 0.0)
        val[c], P_sonda[:, j], P_cal[:, j], termos_ok[c] = v, pu, pc, sorted(ok)
        print(c, json.dumps({k: v[k] for k in v if k not in ('termos_aceitos', 'ap_cv')}, ensure_ascii=False), flush=True)

    np.savez(SCRATCH / 'oof_A.npz', **oof_A)
    np.save(SCRATCH / 'p_sonda.npy', P_sonda)
    np.save(SCRATCH / 'p_cal.npy', P_cal)
    open(SCRATCH / 'universo_ids.txt', 'w').write('\n'.join(uni))
    with open(SCRATCH / 'palavras.jsonl', 'w') as f:
        for i, b in zip(uni, bat_uni):
            b2 = {c: [PALAVRAS[c][k] for k in ks if k in termos_ok[c]] for c, ks in b.items()}
            b2 = {c: t for c, t in b2.items() if t}
            if b2:
                f.write(json.dumps({'id': i, 'termos': b2}, ensure_ascii=False) + '\n')
    json.dump({'classes': NOMES, 'por_classe': val, 'universo': len(uni)},
              open(SCRATCH / 'validacao.json', 'w'), ensure_ascii=False, indent=1)
    with open(SCRATCH / 'termos.tsv', 'w') as f:
        f.write('classe\ttermo\tbate_AF\tpos_AF\tprec_AF\tbate_A\tpos_A\tprec_A\tuniverso\taceito\n')
        for l in linhas_t:
            f.write(f"{l['classe']}\t{l['termo']}\t{l['bate_AF']}\t{l['pos_AF']}\t{l['prec_AF']}\t{l['bate_A']}\t"
                    f"{l['pos_A']}\t{l['prec_A']}\t{l['universo']}\t{int(l['k'] in termos_ok[l['classe']])}\n")


if __name__ == '__main__':
    main()
