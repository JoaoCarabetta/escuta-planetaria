# As decisões que vão para a v3.1

Cada uma tem dono e motivo. As nove primeiras saíram da noite de 23/09, em que
o Fitipe julgou 70 relatos às cegas; as três últimas, da conversa sobre o que
ele achou ali.

## Do portão

**1. `meta` sai do portão e vira marca combinável.** Ele usou "fala sobre
sonhar" 20 vezes contra 3 minhas, e nos 20 dele eu havia posto `literal` em 8 e
`figurado` em 5 — ele marca meta POR CIMA do resto, como propriedade a mais do
texto. O esquema da v3 já concordava com ele (meta é coluna própria); foi a
página que pôs os dois na mesma linha e fez parecerem alternativas.

**2. Descartar exige justificativa escrita.** Ele não descartou nenhum dos 70;
eu descartei 5. Se essa tendência for minha e não dele, o classificador a herda
e o arquivo perde as bordas — que numa tese sobre o imaginário são o material.

**3. O portão ganha `poema, letra, ficção`, `notícia` e `propaganda`.** Os três
nasceram de cartões que ele deixou em branco por falta de opção, não por
hesitação. A distinção importa: texto difícil é dado sobre o arquivo,
instrumento curto não é.

**4. `copy-paste` é categoria própria.** Texto longo que reaparece quase igual
em contas diferentes. É o que ele leu primeiro como ironia — e não era ironia
nenhuma, era texto que passou de mão em mão, sem dono.

## Dos eixos

**5. Memória do sonho** separa três coisas que a v3 juntava: **esqueceu um
pedaço** (a maioria esmagadora), **não lembra nada**, **não sabe se sonhou**.
Foi o achado convergente dos cinco agentes e ele perguntou por ele sem saber
disso: "onde entra mesmo 'não lembrar do sonho'?".

**6. Eixo `o despertar`**: alívio · decepção · acordou mal. Distinto da carga.
Ele e o agente 4 travaram no mesmo relato pela mesma razão, sem se ver — o sonho
é ótimo, o despertador toca, "quero chorar": a carga é prazerosa e só o acordar
dói.

**7. Eixo `a quem o texto fala`**: solto · pergunta ao público · responde a algo
· dirigido. Nasceu de um cartão que ele não conseguiu classificar porque o texto
respondia a um fio que a coleta não guardou. Usado em 51 dos 70 — mais que
carga, memória e despertar somados. `responde a algo` apareceu em 32: quase
metade do que temos é peça de conversa truncada.

**8. Correções de vocabulário, todas dele.** `irônico` não exige riso (eu tinha
escrito "riso irônico", pondo o exemplo no lugar da definição). `aflito` cobre o
ansioso, sem categoria nova. `leve` não exige graça. `responde a algo` vale para
pessoa ou assunto.

**9. Ficam propostos, sem terem entrado na página** porque o instrumento foi
congelado no cartão 54: tom `confidência` (o registro do desabafo exposto, nem
queixa nem ironia) e **estado do desejo** — pendente · realizado · perdido,
pedido também pelo agente 4.

## Sobre a ironia, que era a decisão em aberto

**10. Marcar `irônico` exige as duas coisas juntas:** (a) conteúdo que o próprio
texto marca como ruim e (b) sinal de leveza junto — "kkk", emoji de riso,
diminutivo, exagero que estoura o registro, ressalva que desmente. Sem sinal,
não se marca, **mesmo que o desejo pareça inconcebível**: "inconcebível para
quem lê" não é propriedade do texto.

Isso protege as duas pontas. A fantasia transgressiva sincera continua sendo
lida como sincera. E "meu sonho é morrer antes dos 23 (tenho 22 😁)" recebe a
ironia marcada E a bandeira levantada — registra-se que ela riu, e não se conclui
daí que estava brincando.

## O detector que dispensa leitura

**11. Copy-paste, obra e sonho coletivo se separam por comprimento × tempo**, sem
ninguém julgar nada:

| | como se reconhece | no arquivo |
|---|---|---|
| frase curta e comum | curta, muita gente | 223 grupos · 2.707 relatos |
| **sonho coletivo** | curta, muita gente, janela de dias | 20 grupos · 121 relatos |
| **copy-paste / viral** | longa, muita gente, janela de dias | ex.: 24 cópias em 3 dias, 239 chars |
| **letra, poema** | longa, muita gente, **anos** | 23 grupos · 159 relatos |

O corte de 45 dias virou um detector de letra de música sozinho: quase tudo
nessa faixa é canção. O classificador não precisa reconhecer o Chico nem o Nando
Reis — precisa saber que aquele texto já passou por ali muito tempo antes.

E o complemento vale mais que o detector: **um relato sem gêmeo distante é, por
construção, fala de alguém.**

**12. Furo da régua a corrigir junto.** Dois relatos com 0,9965 de similaridade,
contas diferentes, diferindo em UMA letra ("sozinho"/"sozinha"), ficaram como
`eco_forte` porque a regra de repost entre contas exige hash de texto idêntico.
Passa a aceitar ≥0,995 com o piso de 200 caracteres que já existe — o piso
continua protegendo três pessoas que sonharam parecido e escreveram curto.

## Na interface, quando chegar a hora

Botão **"cópias"** na caixa do texto, no planeta: quantas contas postaram aquilo
e em que intervalo. O dado já existe na tabela `ecos`; falta só mostrar. Serve
para o leitor ver, sem explicação nenhuma, a diferença entre um sonho que 785
pessoas tiveram na mesma semana e um verso que atravessa dois anos.
