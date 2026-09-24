# O desenho do treino — decidido ANTES de treinar

*Fitipe + Claude, 2026-09-24. Escrito antes de qualquer treino porque decidir a
prova depois de ver o resultado é a forma mais fácil e mais comum de se enganar.*

## Dois conjuntos de teste, e nenhum deles entra no treino

**A amostra-prova: 300 relatos sorteados uniformemente** dos 135.512 elegíveis,
semente 2015, gravados em `amostra_prova`. Anotados com a v3.2 pelos mesmos
anotadores e com o mesmo cuidado do material de treino.

Ela responde a pergunta que as bolsas por palavra não podem responder: **as
proporções reais do arquivo**. As bolsas foram montadas de propósito para conter
categoria rara — medir nelas mede a pesca, não o arquivo. Saiu representativa no
que dá para conferir de antemão: 34,7% dela tem "sonhei que" contra 33,5% do
arquivo inteiro.

**Os 70 do Fitipe**, julgados às cegas. Este é o único conjunto com um humano no
topo da cadeia, e é o teto contra o qual tudo se mede. Também nunca entra no
treino.

## O treino

~2.000 anotações vindas das bolsas por pista de superfície. As bolsas continuam
sendo o jeito certo de **treinar**: sorteando ao acaso, uma categoria rara teria
dois exemplos e o modelo nunca a aprenderia.

A regra é a de sempre, e vale repetir porque é onde quase todo mundo escorrega:
**treinar no estratificado, medir no sorteado.**

Ficam de fora do treino, obrigatoriamente: os 300 da amostra-prova, os 70 do
Fitipe, e qualquer relato que apareça em `grupos_copia` com tipo `copy_paste` ou
`obra` — porque 24 cópias do mesmo texto no treino ensinam o modelo a decorar
aquele texto, não a ler.

## O que se mede, e contra o quê

1. **Contra a amostra-prova** — o desempenho honesto nos 174 mil, e as
   proporções reais de cada classe.
2. **Contra os 70 do Fitipe** — a distância até o humano.
3. **Contra os anotadores Claude entre si** — o teto de concordância possível.
   Um classificador não pode ser mais consistente que os julgamentos que o
   treinaram; se dois anotadores discordam em 15% de um campo, exigir 95% do
   modelo naquele campo é exigir que ele adivinhe.

## Depois do treino, antes de soltar nos 174 mil

O modelo rotula a amostra-prova e os 70. Onde ele divergir do humano ou dos
anotadores, os casos voltam para leitura — não para justificar o modelo, mas
para descobrir qual dos dois lados estava errado. Já aconteceu duas vezes nesta
noite de o instrumento estar errado e o julgamento certo.

Só então ele roda no arquivo inteiro, e os relatos em que ficar menos confiante
voltam para anotação cara. É aí que cada ficha gasta vai para onde o modelo
erra, em vez de para onde ele já acerta.

## Nenhuma acurácia se lê sem a linha de base

Aviso que veio de um anotador da amostra-prova, e que muda como os números vão
ser lidos: na fatia dele, `sem_afeto_dito` foi 18 de 28 literais. **Um
classificador que responda `sem_afeto_dito` a tudo acerta 64% do eixo `carga`**
sem ter aprendido nada.

Então, para cada campo, o relatório tem de trazer três números lado a lado:

1. o acerto do modelo;
2. o acerto da **classe majoritária** naquele campo, na amostra-prova;
3. a concordância entre os anotadores Claude no mesmo campo.

O primeiro número só quer dizer algo entre o segundo e o terceiro. Abaixo do
segundo, o modelo é pior que um chute constante. Acima do terceiro, ele não está
acertando: está reproduzindo o ruído de quem o treinou.

E há um efeito parente na direção oposta: **classe rara não se mede por
acurácia.** Numa fatia sorteada de 38, `ironico` apareceu zero vezes. Se ele for
raro assim no arquivo, o modelo pode nunca marcar `ironico` e ainda assim exibir
99% de acerto no campo. Para esses casos o que vale é a revocação por classe,
contada em cima das bolsas — não a acurácia na amostra-prova.

## O que fica registrado como limitação, desde já

O treino não cobre igualmente as classes raras. `hipnagogico`,
`paralisia_do_sono`, `nao_sabe_se_sonhou` e vários valores de `presencas`
aparecem uma ou duas vezes em quinhentos. **Isso não se resolve com volume**,
porque elas são raras no arquivo também. Elas vivem na camada aberta: ficam
buscáveis, contáveis e citáveis, e o classificador não finge que as aprendeu.

## Confundidores conhecidos, medidos antes do treino

Escritos aqui porque um confundidor que se descobre depois vira desculpa.

**`propaganda` está colada a "link".** 86% dos 29 exemplos de propaganda no
treino contêm um link ou um preço, contra 3% do resto do material. O modelo vai
aprender "tem link, então é anúncio" — e isso é *parcialmente verdadeiro no
mundo*, o que torna o confundidor pior, não melhor: ele acerta o suficiente para
não chamar atenção.

Um anotador levantou a suspeita sobre `noticia`, mas a medição mostrou que ali
são 25% de 8 exemplos. O confundidor real é o outro.

**Não vou consertar isto reanotando.** `propaganda` é 1% do arquivo na amostra-
prova; com 29 exemplos, a cabeça vai ser fraca de qualquer forma. O que vou
fazer é **medir a falha em vez de esconder**: no teste, passar pela cabeça de
propaganda os textos da amostra-prova que **contêm link e não são anúncio**, e
relatar quantos ela marca errado. Se ela disparar neles, o número vai no
relatório, não numa nota de pé de página.

**Ruído de rótulo na `carga`, admitido.** Quatro anotadores relataram o mesmo
buraco: falta o espelho de `sem_afeto_dito` — o texto que diz **como foi** e não
**o que foi** ("tive um pesadelo horrível hj"). Sem esse valor, cada anotador
resolveu de um jeito: uns marcaram `aflitiva`, outros `sem_conteudo`. É
construção frequente, e portanto **a cabeça da carga tem ruído de rótulo na
fronteira mais movimentada dela**. Isso limita o teto dela por baixo dos 92% que
a auditoria mediu, e o conserto é a v3.3, não mais dados.

**`modo` não vira cabeça.** Zero ou dois usos forçados por lote, em todos os
lotes, em todos os anotadores. Fica na camada aberta, buscável. Treinar uma
cabeça com dois exemplos produz uma cabeça que responde sempre "não" e exibe
99% de acerto.

## Mudança de critério de seleção, declarada — 24/09, durante o primeiro treino

A primeira corrida guardava o melhor modelo pela **perda total de validação**, que
é a soma de todas as cabeças. Nas épocas 3 e 4 a perda total subiu e ficou plana
enquanto **o acerto do portão subiu de 0,799 para 0,882**. A causa é aritmética:
a perda total é dominada pelas cabeças com muitas classes e poucos exemplos, e o
portão — o campo de que o projeto inteiro depende — pesa pouco nela. Do jeito
que estava, eu terminaria guardando um modelo pior justamente no que importa.

**O critério passa a ser o acerto exato do portão na validação**, com a perda
total registrada ao lado para não esconder o que ela mostra.

Duas coisas que parecem a mesma e não são, e é por isso que esta nota existe:

Escolher a época pela **validação** é legítimo. É para isso que ela serve, e ela
sai do próprio material de treino. Os conjuntos de prova — os 300 sorteados e os
70 do Fitipe — continuam sem participar de decisão nenhuma, nem de treino, nem
de seleção.

O que **não** seria legítimo é olhar o resultado na amostra-prova e então
escolher o critério. Isso é decidir a prova depois de ver a nota, e é
exatamente o que o critério escrito antes existe para impedir. Esta mudança foi
feita olhando só a validação, com o modelo ainda sem ter visto a prova uma única
vez.
