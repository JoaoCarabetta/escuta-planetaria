# O primeiro humano no topo da cadeia — 70 julgamentos do Fitipe

23/09/2026, entre 22h38 e 00h20. O Fitipe julgou 70 relatos **às cegas**: as 46
dúvidas que eu e os cinco agentes registramos, misturadas com 24 casos em que
nenhum de nós hesitou. Ele não sabia quais eram quais. Guardados em
`anotacoes_v3` sob o anotador `fitipe`, com os eixos que ele inventou no
caminho preservados na coluna `extra`.

## A medida que importava: a minha confiança vale alguma coisa?

| eu disse | n | concordamos | discordamos de fato |
|---|---|---|---|
| confiança **alta** | 18 | **17 (94%)** | 0 |
| confiança **média** | 6 | **6 (100%)** | 0 |
| **dúvida** | 46 | 24 (52%) | 5 |

O único caso de `alta` em que não batemos não é discordância: eu marquei
`devaneio + figurado`, ele só `figurado`, no relato sobre "o pesadelo do
telemarketing". Nenhum cartão em que eu estava confiante recebeu dele uma
leitura oposta.

E nas dúvidas concordamos em metade. **É esse o formato que se quer**: onde eu
disse que sabia, eu sabia; onde disse que não sabia, era dúvida de verdade, não
falsa modéstia. Se a concordância nas dúvidas fosse igual à das certezas, a
minha marcação de confiança não estaria dizendo nada.

## O padrão que eu guardei durante a medição

Enquanto ele marcava, eu vi um padrão e **não contei**, para não contaminar os
cartões restantes. Era este:

**Ele usou `fala sobre sonhar` 20 vezes; eu, 3.** E nos 20 dele, eu havia posto
`literal` em 8 e `figurado` em 5 — ou seja, ele marca meta **por cima** do
resto, como uma propriedade a mais do texto, enquanto eu o usava como destino
exclusivo, para textos que só comentam o sonhar sem contar nenhum.

A leitura dele é a certa, e o esquema da v3 já concordava com ele: `meta` é
uma coluna própria, não um valor do portão. Quem errou foi a minha página, que
pôs os dois na mesma linha e fez parecerem alternativas. **Na v3.1, meta sai do
portão e vira marca.**

## A tendência que separa nós dois

**Ele nunca usou `não é sobre sonho`. Eu usei 5 vezes.** Em nenhum dos 70 ele
achou que o texto devia ser jogado fora — encontrou sempre alguma coisa: uma
letra de música que carrega o figurado já formado, um anúncio que não dá para
saber se usa a palavra em sentido literal, uma piada cuja imagem se perdeu.

Isso é consequente para os 171 mil. Se a minha tendência a descartar for
mesmo maior que a dele, o classificador vai herdar a minha, e o arquivo perde
justamente as bordas — que numa tese sobre o imaginário são o material, não o
resto. **Regra para a v3.1: descartar exige justificativa escrita.**

## Os dois eixos que ele inventou são os mais usados do instrumento

| eixo | usado em | distribuição |
|---|---|---|
| **a quem o texto fala** | 51/70 | responde a algo 32 · solto 30 · dirigido 5 |
| **o jeito de contar** | 48/70 | lamento 20 · aflito 13 · leve 12 · grave 9 · seco 9 · irônico 5 |
| carga (só literais) | 25/70 | não dito 10 · aflitiva 6 · prazerosa 5 · mista 3 |
| memória | 4/70 | não lembra 3 · nem sabe se sonhou 1 |
| despertar | 5/70 | decepção 3 · alívio 2 · acordou mal 1 |
| bandeira | 0/70 | — |

Dois números pedem atenção.

**`responde a algo` em 32 de 70.** Quase metade dos textos é peça de uma
conversa cujo resto não foi coletado. A amostra é enviesada para o difícil, e
texto difícil tende a ser fragmento — mas mesmo descontando isso, é um número
que muda o que se pode afirmar sobre o arquivo. Some-se a isto o buraco
descoberto na mesma noite: **nenhum dos 135.479 relatos do Bluesky tem imagem
registrada**, porque o coletor nunca leu o campo `embed` e nem o guardou no
payload cru.

**`lamento` é o tom mais frequente (20), à frente de `leve` (12).** Os cinco
agentes mediram o oposto nos seus lotes — tom leve dominando com folga. Ou a
amostra de dúvidas puxa para o lamento, ou nós dois ouvimos o corpus de
maneiras diferentes. Vale medir de novo na amostra-prova sorteada.

A bandeira que ele pediu não foi usada nenhuma vez. Fica — o caso vai aparecer.

## O que entra na v3.1 por decisão dele

1. `meta` sai do portão e vira marca combinável.
2. Descartar exige justificativa escrita.
3. Memória do sonho separa **esqueceu um pedaço** de **não lembra nada** de
   **não sabe se sonhou**.
4. Eixo **o despertar**: alívio · decepção · acordou mal. Distinto da carga.
5. Eixo **a quem o texto fala**, com `responde a algo` marcando explicitamente
   o contexto que a coleta perdeu.
6. `irônico` não exige riso. `aflito` cobre o ansioso. `leve` não exige graça.
7. Portão ganha `poema, letra, ficção`, `notícia` e `propaganda`.
8. **Ironia não se infere da implausibilidade do desejo** — só com sinal no
   texto. Levantado por mim e ainda não respondido por ele; a regra fica
   proposta, não fechada.
9. Ficam para a v3.1 sem terem entrado na página, porque o instrumento foi
   congelado no cartão 54: tom `confidência` e **estado do desejo** (pendente ·
   realizado · perdido), este pedido também pelo agente 4.

## Um furo da régua que ele achou de olho

Os cartões 10 e 62 são o mesmo texto em duas contas diferentes, com dois dias de
intervalo, diferindo em **uma letra** ("sozinho"/"sozinha") e um ponto final.
Similaridade 0,9965. A régua marcou `eco_forte` em vez de duplicata, porque a
regra de repost entre contas exige hash de texto idêntico. Conserto proposto:
aceitar similaridade ≥0,995 com o piso de 200 caracteres que já existe — o piso
continua protegendo o achado de duas pessoas sonhando parecido e escrevendo
curto.
