# O que o aluno aprendeu — e o que não aprendeu

*24/09/2026, madrugada. BERTimbau base, 1.303 exemplos de treino, seleção pela
quarta época. Cada número vem com a linha de base e o teto de concordância ao
lado, como o `desenho-do-treino.md` exige desde antes do treino existir.*

## A vitória: o portão funciona, e está no teto

Na **amostra-prova** — 300 relatos sorteados que o modelo nunca viu:

| | acerto | chute constante | teto humano |
|---|---|---|---|
| **portão** | **91,3%** | 64,0% | 93% |

**Ele está a 1,7 ponto do teto de concordância entre leitores cuidadosos.** Não
há muito mais a extrair deste material: o que resta de erro é, em boa parte, o
mesmo erro em que três anotadores humanos discordam entre si.

Por classe, e é aqui que a honestidade importa:

| classe | n | revocação |
|---|---|---|
| literal | 197 | **97%** |
| figurado | 97 | **92%** |
| fala_do_sonhar | 6 | 0% |
| obra | 2 | 0% |
| propaganda | 3 | 33% |
| descartável | 2 | 0% |
| devaneio | 0 | — |

As duas classes que carregam o arquivo foram aprendidas. **As raras não foram, e
isso estava previsto**: com 6 exemplos de `obra` no treino, não há o que
aprender. Elas continuam existindo na camada aberta e continuam sendo achadas
por busca — o classificador é que não as reconhece.

## O meio-termo: a carga aprendeu a ausência, não o afeto

| | acerto | chute constante | teto |
|---|---|---|---|
| carga | 76,6% | 60,4% | 92% |

Há aprendizado real acima do chute, mas o detalhe desmente a média:

| valor | n | acerto |
|---|---|---|
| sem_afeto_dito | 119 | **90%** |
| sem_conteudo | 34 | **91%** |
| aflitiva | 23 | 48% |
| prazerosa | 16 | 12% |
| mista / neutra | 5 | 0% |

**Ele aprendeu a reconhecer quando o texto NÃO diz, e mal aprendeu a reconhecer
o que ele diz quando diz.** É exatamente o defeito que seis anotadores
diagnosticaram antes do treino: falta o quarto quadrante da carga, e os casos
de afeto dito ficaram divididos entre `aflitiva` e `sem_conteudo` conforme o
anotador. O modelo herdou a indecisão.

**Isso não se conserta com mais dados.** Conserta-se partindo o eixo em dois —
conteúdo e afeto — como está na v3.3.

## O fracasso, dito sem rodeio: o tom não funciona

| | acerto | chute constante | teto |
|---|---|---|---|
| **tom** | **20,0%** | **43,0%** | 75% |

**O modelo é pior que responder sempre a combinação mais comum.** Fora `leve`
(41% de revocação) e `seco` (9%), ele não acerta nenhum valor: ironia, lamento,
confidência, indignação, aflição e gravidade ficaram todas em zero.

A causa estava diagnosticada antes de eu treinar e eu treinei assim mesmo,
porque era o que havia: o tom concorda em 75% entre humanos, a rubrica define
`leve` e não define `seco`, cada anotador declarou um limiar próprio, e os
emojis — que decidem o tom sozinhos em vários textos — não estão na rubrica.
**O modelo aprendeu a incerteza que lhe demos.**

**A cabeça do tom não deve ser usada.** Nem no planeta, nem na tese, nem para
pré-rotular. Ela volta quando a v3.3 definir `seco`, mapear os emojis e separar
o celebratório.

## Os 70 do Fitipe: o número dos casos difíceis

| | acerto | chute constante |
|---|---|---|
| portão | 68,6% | 35,7% |

Muito abaixo dos 91,3% da amostra-prova, e **era esperado**: 46 dos 70 são
justamente as dúvidas que eu e os cinco anotadores registramos. É o desempenho
do modelo no pior material que existe, não no material médio.

Ainda assim, quase o dobro do chute. E as duas classes principais seguem em pé:
literal 89% de revocação, figurado 93%.

## O que continua sem teste

**O confundidor da propaganda.** Eu havia registrado que 86% dos exemplos de
propaganda no treino contêm link ou preço, contra 3% do resto, e prometido medir
a falha. **Não deu para medir: a amostra-prova não tem um único texto com link
ou preço em 300 sorteios.** Isso é informação sobre o arquivo — link é raro —
mas deixa o confundidor por testar. Precisa de um conjunto próprio, sorteado
entre os textos com link.

## O veredito prático

**Usar:** o portão, nos dois valores que importam. É o que permite dizer quanto
do arquivo é sonho dormido e quanto é figura de linguagem, com 97% e 92% de
revocação e o erro restante no mesmo lugar onde humanos discordam.

**Usar com ressalva escrita:** a carga, só na distinção dito × não dito.

**Não usar:** o tom, e as classes raras do portão.
