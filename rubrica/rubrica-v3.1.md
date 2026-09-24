# Rubrica v3.1 — o portão, quatro marcas e três eixos

*Fitipe + Claude, 2026-09-24. Substitui a v3 depois de 519 anotações minhas e
dos cinco agentes, e dos 70 julgamentos cegos do Fitipe. Cada mudança tem dono
e motivo em `decisoes-v3.1.md`; a medição que a justifica está em
`comparacao-70.md`.*

## O que a v3 acertou, medido

O portão literal × figurado funcionou nas duas direções. A bolsa `suspeito` deu
9/9 figurado e a `desejo` 10/10 — o qwen lia todos como sonho dormido. Na volta,
a bolsa `intensificador` entregou literais genuínos em três lotes: "tive um
pesadelo" é literal com a mesma frequência com que "que pesadelo" é figurado.

E a separação carga × tom se provou: o riso é o registro padrão do corpus,
inclusive sobre conteúdo pesado. Quem colapsar os dois num campo de "sentimento"
perde exatamente isso.

## 1. O PORTÃO — o que o texto é

Combinável. Um texto pode ser mais de um.

**LITERAL** — a pessoa dormiu e sonhou. Não exige que diga "dormi": reconhece-se
pela impossibilidade da cena, pelo tempo verbal, pela ausência de intenção, pelo
despertar mencionado. Inclui a **ausência** — "não sonhei", "não lembro o que
sonhei" entram como literal sem conteúdo, porque não sonhar é dado.

**FIGURADO** — "sonho"/"pesadelo" fora do sentido onírico. Quatro espécies:
`desejo` (~14.500) · `intensificador` (~8.300) · `nome_expressao` · `comercial`.
*Figurado não é sinônimo de desejo: o intensificador é quase tão comum e nunca
é desejo.*

**DEVANEIO** — acordada, a pessoa imagina, divaga, projeta.

**POEMA, LETRA, FICÇÃO** — o texto é obra, não relato: verso, canção, sinopse,
cena. *(novo — Fitipe)*

**NOTÍCIA** — jornalismo; alguém reportando um fato, não contando experiência
própria. A palavra costuma vir na manchete. *(novo — Fitipe)*

**PROPAGANDA** — anúncio de produto, serviço, show. *(novo — Fitipe)*

**DESCARTÁVEL** — nada sobre sonho. **Exige justificativa escrita.** Nos 70
julgados às cegas, o Fitipe não descartou nenhum e eu descartei 5; se essa
tendência for minha, o classificador a herda e o arquivo perde as bordas — que
numa tese sobre o imaginário são o material.

## 2. AS QUATRO MARCAS — combinam com qualquer coisa do portão

**`meta`** — o texto fala SOBRE o sonhar, além de (ou em vez de) contar um
sonho. *Na v3 isto era destino do portão, e estava errado: o Fitipe usou 20
vezes contra 3 minhas, quase sempre por cima de literal ou figurado.*

**`copy-paste`** — texto que circula: reaparece quase igual em contas
diferentes. Vale junto com poema, notícia, propaganda, o que for.
**Levantada por máquina** (ver §5), não por leitura.

**`falta contexto`** — o texto é peça de algo que a coleta não guardou: responde
a um fio perdido, ou depende de uma imagem que não temos. *Não é traço do texto,
é defeito do arquivo — e precisa ser contável.*

**`bandeira`** — ódio, violência, risco à própria pessoa. Não classifica nada,
só sinaliza para decisão posterior.

## 3. VALÊNCIA — três eixos, porque divergem

**`carga`** — o que acontece DENTRO do sonho: `prazerosa` · `neutra` ·
`aflitiva` · `mista` · **`nao_dito`**.

*O `nao_dito` é regra do Fitipe: "pra via geral acho melhor não assumirmos nada".
Nunca inferir afeto que o texto não dá — a carga obrigatória fabricava dado.*

**`tom`** — como a pessoa CONTA: `leve` · `irônico` · `lamento` · `aflito` ·
`hesitante` · `grave` · `seco`.

*Todos os rótulos são do Fitipe, achados enquanto marcava. `irônico` não exige
riso; `aflito` cobre o ansioso; `leve` não exige graça — nos três casos eu havia
posto um exemplo no lugar da definição.*

**`despertar`** — `alívio` · `decepção` · `acordou mal`. Só literal.

*Distinto da carga, e a v3 não tinha onde guardar: o sonho é ótimo, o despertador
toca, "quero chorar". O Fitipe e o agente 4 travaram no mesmo relato pela mesma
razão, sem se ver.*

> *"sonhei que eu estava grávida de novo. Chega acordei nervosa 🤣"*
> → carga **aflitiva**, tom **leve**

### A regra da ironia

`irônico` exige **as duas coisas juntas**: (a) conteúdo que o próprio texto marca
como ruim e (b) sinal de leveza — "kkk", emoji de riso, diminutivo, exagero que
estoura o registro, ressalva que desmente. Sem sinal, não se marca, **mesmo que
o desejo pareça inconcebível**: inconcebível para quem lê não é propriedade do
texto.

Protege as duas pontas. A fantasia transgressiva sincera segue lida como
sincera; e *"meu sonho é morrer antes dos 23 (tenho 22 😁)"* recebe a ironia **e**
a bandeira — registra-se que ela riu, não se conclui que estava brincando.

## 4. OS GRUPOS — só para o LITERAL

**`memoria`** — em branco se lembra. `esqueceu_um_pedaco` · `nao_lembra_nada` ·
`nao_sabe_se_sonhou`.

*A v3 tinha um `nao_lembra` só, e os cinco agentes convergiram nisto sem se ver:
o esquecimento parcial é a esmagadora maioria, e às vezes cai justo sobre o que
importa — uma gira de terreiro em que "não lembro do que foi falado".*

**`modo`** — `recorrente` · `retomado` (continua na mesma noite) · `fragmentado`
· `lucido` · `paralisia_do_sono` · `falso_despertar` · `hipnagogico`.

*`recorrente` exige que **o sonho** se repita: "sonhei que tava trabalhando de
novo" não é recorrência, é cena. Foi o falso positivo que os cinco agentes
acharam. `lucido` é lucidez, não vivacidade: "sonho muito lúcido" quase sempre
quer dizer vívido.*

**`presencas`** — `morto` · `morte_no_sonho` · `figura_publica` · `animal` ·
`religioso` · `personagem_ficcional` · `ex_parceiro` · `sexo` · `violencia` ·
lista aberta.

*`morto` é visita de quem já morreu; `morte_no_sonho` é alguém morrendo lá
dentro. Par de calibração: "sonhei com meu pai e ele morreu tem 8 anos" contra
"sonhei que meu pai morreu". Superfície quase igual, categorias opostas.*

**`atribuicao`** — espécie × força.
Espécie: `significa` · `aviso` · `premonicao` · `residuo_diurno` · `nega` ·
`pede_interpretacao`. Força: `afirma` · `cogita` · `jocoso`.

*A v3 só tinha o polo positivo. A recusa de significado — "não sou adepto de
misticismos" — é tão informativa quanto a crença, e virava campo vazio.*

**Uma passagem barata nos figurados**, que a v3 dispensava: o corpus figurado é
o maior do arquivo (~23 mil) e perdia todo o conteúdo — maldições jocosas,
fantasias sexuais explícitas, desejo de violência.

## 5. O QUE A MÁQUINA DECIDE SOZINHA

Comprimento × tempo separa quatro coisas que pareciam uma:

| | como se reconhece | no arquivo |
|---|---|---|
| frase curta e comum | curta, muita gente | 223 grupos · 2.707 relatos |
| **sonho coletivo** | curta, muita gente, janela de dias | 20 grupos · 121 relatos |
| **copy-paste / viral** | longa, muita gente, janela de dias | ex.: 24 cópias, 3 dias, 239 chars |
| **poema, letra** | longa, muita gente, **anos** | 23 grupos · 159 relatos |

O corte de 45 dias virou detector de canção sozinho. O classificador não precisa
reconhecer o Chico nem o Nando Reis — precisa saber que o texto já passou ali
muito antes. E o complemento vale mais que o detector: **relato sem gêmeo
distante é, por construção, fala de alguém.**

## 6. CONFIANÇA — obrigatória

`alta` · `media` · `duvida`, com `nota` livre dizendo o que travou.

Está calibrada, e agora isso é medido, não suposto: nos 70 julgados às cegas, o
Fitipe concordou em **94%** do que marquei `alta`, **100%** do que marquei
`media` e **52%** das dúvidas. Onde eu disse que sabia, eu sabia; onde disse que
não, era dúvida de verdade. É isso que autoriza mandar só os casos difíceis para
o modelo caro.

## Ficaram propostos, não testados

Tom `confidência` — o desabafo exposto, nem queixa nem ironia. E **estado do
desejo**: `pendente` · `realizado` · `perdido`. Os dois chegaram quando o
instrumento já estava congelado no cartão 54; entram quando houver amostra para
justificá-los.
