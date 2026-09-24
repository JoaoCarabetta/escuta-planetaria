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
