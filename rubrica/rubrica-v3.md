# Rubrica v3 — o portão é literal × figurado

*Fitipe + Claude, 2026-09-23. Substitui a v2.1, que lia uso figurado como sonho
literal em cerca de 1 de cada 5 casos.*

## Por que mudou

A v2.1 tinha por portão `natureza_texto` (relato · meta · idiomático · ruído) e
88,1% de tudo caía em "relato". Numa amostra uniforme de 30 relatos lidos um a
um, discordei do julgamento em 6 — e **quatro dos seis eram o mesmo erro**: uso
figurado lido como sonho literal.

```
"espero acordar amanha e tudo isso ser um pesadelo"   → marcado sonho dormido + premonitório
"essa tl é tão horrivel... que horror pesadelo"        → marcado sonho dormido
"eu SONHEI c o dia de hoje, to largada no sofá"        → marcado sonho dormido
"meu sonho era dar em todas as posições"               → marcado sonho dormido
```

Nenhum dos quatro é sonho. A v3 põe essa decisão em primeiro lugar.

## 1. O PORTÃO — três estados, não excludentes

**LITERAL** — a pessoa dormiu e sonhou. **Não exige que o texto diga "dormi" ou
"sonhei"**: reconhece-se pela impossibilidade da cena, pelo tempo verbal do
relato, pela ausência de intenção, pelo despertar mencionado.

> *"Sonhei que o Gaara chunin e o Gaara shippuden estavam discutindo por telepatia
> na cozinha aqui de casa"* — não diz que dormiu, e é inequivocamente literal.

Inclui a **ausência**: "não sonhei" e "não lembro o que sonhei" entram como
literal sem conteúdo. *Não sonhar, ou não lembrar, é dado — decisão do Fitipe.*

**FIGURADO** — usa "sonho"/"pesadelo" fora do sentido onírico. Quatro espécies:

| figura | exemplo | volume no arquivo |
|---|---|---|
| `desejo` | "meu sonho é comprar uma casa" | ~14.500 |
| `intensificador` | "essa tl é um pesadelo" | ~8.300 |
| `nome_expressao` | "Vale dos Sonhos", "bons sonhos", "sonho molhado" | — |
| `comercial` | "Liso dos Sonhos, de R$121 por R$77,90" | — |

*Cuidado registrado: **figurado não é sinônimo de desejo.** O intensificador é
quase tão comum quanto ele e nunca é desejo.*

**DEVANEIO** — acordada, a pessoa imagina, divaga, projeta. Nem sonho dormido,
nem desejo declarado.

> *"tava meio sonhando acordada e sonhei q tava no dentista, do nada fiquei
> mostrando meus dentes pro nada ai veio um baque de realidade"*

Raro por palavra (~470 nomeados), mas quem lê pega os que não se nomeiam.

**Os três se combinam.** O caso mais comum é literal + figurado:

> *"sonhei que a noise era campeã da nfa, espero que isso se realize"*

E há dois destinos fora do portão: `descartavel` (anúncio, link solto, nada
sobre sonho) e `meta` (fala SOBRE sonhar sem contar um sonho).

## 2. VALÊNCIA — duas, porque divergem

Um campo só obrigaria a escolher, e o que se perde é justamente o interessante.

**`carga`** — o que acontece DENTRO do sonho: `prazerosa` · `neutra` ·
`aflitiva` · `mista`

**`tom`** — como a pessoa CONTA: `leve` · `neutro` · `grave` · `ambivalente`

> *"sonhei que eu estava grávida de novo. Chega acordei nervosa 🤣"*
> → carga **aflitiva**, tom **leve**
>
> *"Sonhei com o Nênis, meu gatinho q virou estrelinha. Foi tão bom abraçar ele de
> novo, mas doeu tanto quando eu acordei"*
> → carga **mista**, tom **grave**

`mista` é para quando o sonho é bom e o despertar dói — padrão frequente no
sonho com morto.

## 3. OS TRÊS GRUPOS — só para o LITERAL

As seis "qualidades" da v2 eram três coisas diferentes empilhadas. Separadas:

**`modo`** — como se sonhou (o fenômeno)
`recorrente` · `lucido` · `paralisia_do_sono` · `falso_despertar` ·
`nao_lembra` · `nao_sonhou`

*`falso_despertar` é sonhar que acordou — o qwen vinha chamando isso de paralisia
do sono, que é outra coisa.*

**`presencas`** — o que ou quem aparece (lista aberta, vai crescendo)
`morto` · `sexo` · `violencia` · …

*`morto` é visita de quem já morreu. Alguém que morre DENTRO do sonho não é
visita de morto — é conteúdo aflitivo.*

**`atribuicao`** — o que o sonhador AFIRMA sobre o sonho
`premonicao` · `aviso` · `mensagem` · `significa_algo`

*Isto não descreve o sonho, descreve a relação da pessoa com ele. Num arquivo
sobre o imaginário talvez seja o mais interessante: o dado não é que o sonho
previu, é que alguém leu o próprio sonho como aviso.*

**Nada disso vale para o figurado.** Desejo com conteúdo sexual não é sonho
erótico. Se um dia quisermos descrever os figurados, roda-se uma passagem só
neles — barata, porque o portão já os separou.

## 4. CONFIANÇA — obrigatória

`alta` · `media` · `duvida`, com `nota` livre dizendo o que travou.

As dúvidas vão para o Fitipe decidir. Vão **misturadas com certezas**, sem
avisar quais são quais: se ele discordar onde eu estava confiante, essa é a
informação mais valiosa de todas, e o único jeito de saber se a minha confiança
significa alguma coisa.
