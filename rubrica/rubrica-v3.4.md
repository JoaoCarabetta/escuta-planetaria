# Rubrica v3.4 — o hábito que também é sonho, e quem sustenta a leitura

*Fitipe + Claude, 2026-09-27 (tarde). Sai de 3.473 textos anotados com a v3.3
por 15 anotadores (`lotes/v33/observacoes_anotadores.md`) e das decisões do
Fitipe da tarde de 27/09, que mandam sobre tudo o que estiver escrito antes. A
v3.3 fica como histórico.*

## O que mudou da v3.3 para a v3.4

| campo | v3.3 | v3.4 | de onde veio |
|---|---|---|---|
| portão | sonho habitual = só `fala_do_sonhar`; marca `meta` para "conta e fala do sonhar" | **`literal` e `fala_do_sonhar` combinam.** Hábito **com** conteúdo = os dois; hábito **sem** conteúdo = só `fala_do_sonhar`. **`meta` sai** (vira o par no portão) | Fitipe; empate mais frequente em seis lotes |
| `carga` | `neutra` = afeto dito e nulo; `estranha` sozinha | **`neutra` sai** (funde-se em `sem_afeto_dito`); **`estranha` combina** com outra valência; o que se sentia **dentro** do sonho conta | Fitipe |
| `despertar` | choro sem valência = `acordou_neutro` | **choro depois de sonho = pelo conteúdo; sem conteúdo com valência = `acordou_mal`**; `acordou_neutro` só para "e acordei"; "triste porque não era real" = `decepcao` (+ `acordou_mal` se diz triste); "queria voltar" por curiosidade não conta | Fitipe; nº 1 das dúvidas em três lotes (~80 casos) |
| letra de música | letra como fala inteira = `obra` sem carga | **ser letra não quer dizer que não sonhou**: anote o sonho e marque `suspeita_circulacao`, com a letra na nota | Fitipe |
| `atribuicao_quem` | não existia (ia na nota) | **campo novo, paralelo**: `a_pessoa` · `familia` · `religioso` · `rede` · `busca` · `amigo_parceiro` · `dizem`. As genealogias do sonho | Fitipe; pedido em três lotes |
| `atribuicao_postura` | postura geral | postura **de quem escreve** diante da leitura; "?" = `pergunta`; "será que/acho que/deve ser" sem "?" = `cogita` | inconsistência entre lotes |
| `atribuicao_origem` | "sinal sem agente" = `universo_destino` | sinal/aviso/premonição **sem agente escrito = `nao_diz`**; ganha `outra` (fora da lista, com nota); gestos rituais e faculdade própria têm regra | inconsistência entre lotes (47 × 13 `universo`) |
| marca `pedido` | não existia | direção invertida: a pessoa **envia** ("recado pro universo") | três lotes |
| marca `texto_gerado` | não existia | texto de IA, template de app, copypasta | três lotes |
| `bandeira` | voz desperta | **só o que está presente no texto**; tentativa passada e superada não levanta | Fitipe; tentativa passada inflava a bandeira (39 em 160) |
| `figura` | 7 valores | ganha **`votos`** ("bons sonhos") e **`escape`** (nome a confirmar: "vivo nos meus sonhos"); o doce de padaria é `homonimo` | Fitipe; ~90 votos sem casa em três lotes |
| `desejo_estado` | 3 valores | ganha `nenhum` e `generico`; `null` permitido com `falta_contexto` | Fitipe |
| `sonhador` | um valor | **lista** (dois sonhadores); interpretação de sonho alheio = `terceiro` | Fitipe |
| fala do devaneio | sem lugar | `fala_do_sonhar` + nota | Fitipe |
| exibição | — | cargas combinadas aparecem em porcentagem na página | Fitipe |

---

## O PRINCÍPIO: o arquivo escuta

**O arquivo não decide se uma experiência é "real".** `literal` quer dizer só
isto: *aconteceu durante o sono*. O que a pessoa acha que aquilo foi (uma
mensagem, uma visita, uma saída do corpo, coisa da cabeça dela) entra pela
**atribuição**, com a palavra dela e sem tradução para a nossa.

Referência do Fitipe: Davi Kopenawa (*A queda do céu*) e Hanna Limulja (*O
desejo dos outros*, sobre sonhos yanomami). Ali o sonho é relação, é a imagem
que viaja, recebe visita e visita os outros, e não um evento privado dentro de
uma cabeça. A rubrica não adota essa ontologia nem nenhuma outra. Ela não pode é
apagar a ontologia de quem fala. Um texto que diz *"tive uma saída misturada com
sonho"* é `literal` e guarda na atribuição exatamente essa mistura.

Consequência prática: **não use as nossas palavras** ("premonição", "coincidência",
"resíduo diurno") onde a pessoa não as usou.

**E o arquivo registra de quem vem a leitura.** Um sonho quase nunca é
interpretado sozinho: *a mãe diz que sonhar com dente é morte*, *a mãe de santo
mandou fazer uma guia*, *a moça do TikTok falou*, *joguei no Google*. O campo
`atribuicao_quem` guarda isso, e para o Fitipe é o dado mais rico da rubrica:
ele **mapeia as genealogias do sonho**, as tradições e os modos de lidar com o
sonho que passam pela família, pelo terreiro, pela rede e pela busca.

---

## NÚCLEO DURO — o que o classificador aprende

### 1. Portão: o que o texto é (lista, combinável)

| valor | o que é |
|---|---|
| `literal` | a pessoa dormiu e sonhou; o texto conta ou menciona um sonho, particular **ou habitual com conteúdo** |
| `figurado` | "sonho"/"pesadelo" fora do sentido onírico: desejo, intensificador, nome, expressão |
| `fala_do_sonhar` | o texto fala do sonhar em geral: prática, crença, hábito, explicação, o próprio devaneio. **Combina com `literal`** |
| `devaneio` | acordada, a pessoa imagina uma cena. **Registrado, fora do núcleo treinado** (ver abaixo) |
| `obra` | o texto **é** obra alheia reproduzida: letra, trecho de livro, sinopse, cena |
| `noticia` | jornalismo: reporta um fato, não conta experiência |
| `propaganda` | anúncio de produto, serviço, show |
| `descartavel` | nada sobre sonho. **Exige justificativa escrita na nota** |
| `ambiguo` | o texto sustenta duas leituras do portão e nada as decide. **Vai sempre junto das leituras candidatas**: `["literal","figurado","ambiguo"]` |

**Como se reconhece `literal`.** Não exige "dormi": reconhece-se pela
impossibilidade da cena, pelo tempo verbal, pela ausência de intenção, pelo
despertar mencionado. Inclui a ausência: "não sonhei" é literal (com
`memoria: nao_sonhou`).

**`literal` e `fala_do_sonhar` não se excluem** *(Fitipe)*:

| o texto | portão |
|---|---|
| conta um sonho e nada mais | `literal` |
| hábito **com conteúdo** (quem, o quê, como acorda): *"sonho com ela toda noite e acordo chorando"*, *"já sonhei com isso 3x"*, *"as vezes ela vem de ladrão em sonho"* (`f84e64c0539d18be`) | `literal` + `fala_do_sonhar`, com `repeticao`, carga e despertar |
| hábito **sem conteúdo**: *"pesadelos todas as noites"*, *"os pesadelos que eu tinha quando dormia de barriga cheia"* | só `fala_do_sonhar` |
| conta um sonho **e** fala do sonhar em geral (Jung, significados, "sempre sonho muito") | `literal` + `fala_do_sonhar` |
| fala do sonhar, nenhum sonho | só `fala_do_sonhar` |

O mínimo de conteúdo é o mesmo de `conteudo: narrado`: **quem ou o quê** aparece
no sonho. A menção marginal ("li sobre sonho lúcido") não basta para
`fala_do_sonhar`: o sonhar precisa ser assunto do texto, nem que seja de uma
frase.

**`figurado` nos relatos longos.** Desabafos do Reddit com "namoro dos sonhos",
"garota dos meus sonhos", "faculdade dos sonhos" ou "era um sonho meu de
infância" (conhecer o Rio) são `figurado`, por mais longo que seja o resto do
texto. "Meu sonho é X" é quase sempre figurado. A exceção nomeada: *"**meu sonho
clássico** é voltar pro primeiro emprego. sempre sonho q voltei pra C&A"* é
literal. E "sonhei com X e se realizou" costuma ser figurado: aí a preposição
"com" não marca o onírico.

**`devaneio`: fronteira e estatuto.** Exige **cena com ação e duração**
imaginada acordada. Verbo de imaginar sem cena ("fico imaginando como seria")
não basta. A melhor definição veio de um relato do próprio arquivo: *"meus sonhos
(enquanto durmo, nao os devaneios)"*. **A fronteira é do falante**: quem chama o
próprio devaneio de "sonhei" e diz que estava acordado é `devaneio`. Deu zero em
300 sorteados, por isso não tem cabeça no classificador. Continua no portão para
o caso raro ficar achável.

**Devaneio sem cena.** *"vivo nos meus sonhos"*, *"sonho acordado o dia todo"*
sem cena contada são `figurado` com `figura: escape`. **Falar do devaneio**
(maladaptive daydreaming, "passo horas imaginando") sem cena é `fala_do_sonhar`
com nota "fala do devaneio".

**Poema, letra, texto literário** *(regra do Fitipe na revisão)*:
- **Poema autoral** (a pessoa escreve em verso, em primeira pessoa, sobre a
  própria vida) **não é `literal`**, mesmo que um verso diga "sonhei". Julga-se
  pelo que o "sonho" faz no poema: quase sempre `figurado` ou `fala_do_sonhar`.
  Escreva "poema autoral" na nota. Exemplo: `9b8ce432db3497ee`, poema de luto por
  um animal com *"Lembro dos sonhos que eu tive e todos, você sempre esteve lá"*.
  O Fitipe marcou figurado + fala sobre sonhar.
- **Letra de música: ser letra não quer dizer que a pessoa não sonhou** *(Fitipe,
  corrige a v3.3)*. *"tive um sonho ruim e acordei chorando / por isso eu te
  liguei"* é letra conhecida. Quando ela vem solta ou no formato da letra
  (`7598eebea4123f14`, `c5b6c314014b9c8b`), **anote o sonho normalmente**
  (`literal`, `aflitiva`, `acordou_mal`), marque `suspeita_circulacao` e escreva
  na nota "letra de música". A pessoa pode estar dizendo a própria noite com as
  palavras da canção. `obra` fica só para a reprodução que é claramente obra:
  vários versos, título ou autor citado, e nenhuma voz própria.
- **Trecho de música, livro ou autor citado no meio de um relato não muda o
  portão do relato.** A epígrafe de Jung num ensaio não torna o ensaio `obra`, e
  a letra citada numa conversa não torna literal quem a cita.
- **Texto sobre obra não é obra.** Uma resenha julga-se pelo que ela faz: quase
  sempre `fala_do_sonhar` ou `figurado`.

**`ambiguo`, casos da revisão.** *"Eu tive um sonho lindo = próximo episódio de
Agatha all along com 53 minutos"* (`553cd18de979583f`): sonho dormido parecido
com o episódio, ou "sonho" como elogio? *"quanto tempo eu sonhei que te dava um
beijo novamente"* numa carta de amor (`19033a0b5e9d5ec6`): sonho recorrente ou
fantasia acordada? Marque as duas leituras + `ambiguo`, com `confianca: duvida`,
e diga na nota qual pende. Os eixos de `literal` só se preenchem quando `literal`
está entre as candidatas.

### 2. Quem sonhou: `sonhador` (lista)

`proprio` · `terceiro` · `citado`

**É lista**: *"sonhei que minha mãe sonhava comigo"*, *"eu e minha irmã sonhamos
a mesma coisa"* levam `["proprio","terceiro"]`. Quando o sonhador é outro, **a
carga é a que o texto atribui ao sonho dele**, não a de quem conta.

**Interpretação de sonho alheio** (quem comenta o sonho que outro contou: *"isso
é sinal de gravidez"*) é `literal` com `sonhador: ["terceiro"]`. A leitura vai em
atribuição com `atribuicao_quem: a_pessoa` (quem escreve é quem interpreta).

**`sonhador_autodeclarado`** (camada aberta, curto): marcas como "H(20)",
"M(25)", "Eu, H(22)" são autodeclaração de gênero e idade, comuns no Reddit.
Copie como aparecem, em qualquer formato: `"H(20)"`, `"(M21)"`, `"22F"`, `"homem,
30"`. Se não houver, `null`. Não infira de nada mais. Confira antes de gravar: um
lote deixou "(M21)" passar como `null`.

### 3. Carga: o afeto que o texto atribui ao sonho (só sob `literal`)

**Definição:** o afeto que o texto **diz em palavra** sobre o sonho, conte ele ou
não o que aconteceu. *"tive um sonho bom"* → `prazerosa`. *"pesadelo horrível"*
→ `aflitiva`. Se o conteúdo foi contado é outro eixo (`conteudo`, abaixo).

| valor | quando |
|---|---|
| `prazerosa` | bom, lindo, gostoso, "o sonho mais legal da minha vida", "não queria acordar", "eu estava feliz lá" |
| `aflitiva` | ruim, horrível, pesadelo, medo, desespero, angústia; interjeição sobre o sonho: "Deus me livre", "credo", "que trauma" |
| `mista` | **o mesmo sonho** carrega os dois, ou muda de um para o outro: *"começava um sonho bom… de repente alguém muito querido morria"* (`e93c9a2ad6fa8e8a`) |
| `estranha` | esquisito, bizarro, estranho, louco, doido, inusitado, surreal, bombástico, intrigante, curioso. **Combina com outra valência**: *"esquisito mas bom"* = `estranha` + `prazerosa`; *"bizarro… UM HORROR"* = `estranha` + `aflitiva` |
| `sem_afeto_dito` | nenhuma palavra diz como foi o sonho. Inclui o "normal", "sem nada de mais" (a antiga `neutra`) |

**`neutra` sai** *(Fitipe)*: na revisão ela foi usada onde o texto não
falava do afeto. Se o texto diz explicitamente que o sonho foi
indiferente (*"isso nunca me incomodou"*), marque `sem_afeto_dito` e escreva isso
na nota.

**Regras, na ordem em que travam:**

1. **Só palavra de afeto conta. Emoji sozinho não conta**, e isso inclui 😭 🥲 🫠
   🥹 🥺, que mudam de sentido de um texto para outro. "kkk" também não conta.
2. **A palavra "pesadelo" já é afeto dito**: `aflitiva`, mesmo sem conteúdo.
   Vale enquanto ela nomeia o sonho. Se é intensificador de outra coisa, não vale.
3. **Palavra de conteúdo não é palavra de afeto.** *"sonhei umas coisa trauma da
   infancia transtorno alimentar… tudo misturado"* (`485366a519781976`) é
   `sem_afeto_dito`. O Fitipe: *"botei aflitivo só pq tinha a palavra trauma, mas
   não fica claro"*. Morte, acidente e perseguição narrados sem qualificador
   também são `sem_afeto_dito`, e o conteúdo vai para `presencas`.
4. **"louco" sozinho é `estranha`**: *"tive um sonho muito louco, tira isso da
   minha cabeça Deus"* (`b2ae9448219f5c5c`). Ao lado de uma valência, "louco" é só
   intensificador: *"um sonho MUITO LOUCO… em partes mto bom"* é `prazerosa`.
   Palavras que dizem estranheza de fato ("esquisito", "bizarro", "estranho")
   **somam**: `estranha` + a valência.
5. **"horrores" é "muito".** *"Sonhei horrores de novo. Um lugar lindo"* é
   `prazerosa`.
6. **O despertar feliz causado pelo sonho diz que o sonho foi bom.** *"acordei
   feliz pq sonhei com mingyu"*, *"Hoje eu acordei feliz / Sonhei com ela a noite
   inteira"*: `carga: prazerosa` **e** `despertar: acordou_bem`. **O inverso não
   vale.** *"sonhei com a minha tia e acordei triste e com muita saudade"* não diz
   que o sonho foi ruim (saudade depois de sonho bom é o caso mais comum):
   `sem_afeto_dito` + `acordou_mal`. Acordar mal é ambíguo, acordar feliz não é.
7. **O que o sonhador sentia dentro do sonho é carga.** *"eu estava feliz lá"*,
   *"no sonho eu tava desesperada"* dão `prazerosa` e `aflitiva`, em geral. Se o
   sentir lá dentro contradiz como o texto qualifica o sonho, liste os dois.
   Exemplo: *"um pesadelo, mas eu tava rindo"* = `aflitiva` + `prazerosa`, com
   nota.
8. **Onde o sonho acaba não importa mais para a carga.** Como a carga é o que o
   texto atribui ao sonho, a palavra conta esteja dentro da narração ou no
   comentário de quem acordou. O que é reação ao acordar vai **também** para
   `despertar`.

**`sem_afeto_dito` mede o dito, não a ausência de afeto.** *"acordei chorando a
morte dele"* depois de narrar o cachorro picado pelas aranhas recebe
`sem_afeto_dito` na carga, porque nenhuma palavra qualifica o sonho, e
`acordou_mal` no despertar. Quem usar o número depois precisa ler assim: **o
arquivo não é afetivamente mudo, ele não nomeia o afeto.**

**Carga do sonhador terceiro:** é a que o texto atribui ao sonho *dele*.

**Exibição:** na página, quando um relato tem cargas combinadas, elas aparecem
em porcentagem (ex.: 50% estranha · 50% prazerosa).

### 4. Conteúdo: o texto conta o sonho? (só sob `literal`)

`narrado` · `so_mencionado`

- `narrado`: o texto diz **ao menos quem ou o quê** estava no sonho. *"sonhei com
  minha ex"*, *"Sonhei a noite toda com Ad****"* e *"sonhei com a minha tia"* já
  são `narrado`, e na revisão o Fitipe os tratou como sonhos com conteúdo.
- `so_mencionado`: o sonho é afirmado e nada dele é dito. *"tive um sonho tão bom,
  queria voltar a cochilar pra voltar pra ele"* (`873c3376389b853c`); *"Tive um
  sonho horrível e AGR n consigo esquecer das piores partes"*
  (`18782818f87ee9f1`); *"Sonhei duas noites seguidas a mesma coisa"*.

Os dois eixos são independentes: `prazerosa` + `so_mencionado` é o quadrante que
a v3.2 esquecia, e `sem_afeto_dito` + `narrado` é o mais comum do arquivo. Com
`memoria: nao_sonhou` ou `nao_lembra_nada`, `conteudo` fica `null`.

### 5. Confiança (obrigatória)

`alta` · `media` · `duvida`, com a razão na nota quando não for `alta`. Está
calibrada: na revisão de 27/09, o portão coincidiu com o do Fitipe em 27 de 27
dos `alta`. Use `duvida` de verdade. Dúvida inflada estraga tanto quanto
confiança inflada.

---

## CAMADA ABERTA — registrada, buscável, não treinada

### Onde cada campo vale

| campo | literal | fala_do_sonhar | figurado | demais |
|---|---|---|---|---|
| `sonhador` | sim | sim | — | — |
| `carga`, `conteudo`, `despertar`, `repeticao` | sim | só se `literal` também | — | — |
| `figura`, `desejo_estado` | — | — | sim | — |
| `memoria`, `modo` | sim | **sim** | — | — |
| `atribuicao_*` | sim | sim | — | — |
| `presencas` | sim | sim | **sim** | sim |
| `marcas` | sim | sim | sim | sim |

Onde o campo não vale: lista vazia `[]` ou `null`, **nunca** um valor-padrão.
Quando o portão é `literal` + `fala_do_sonhar`, valem os campos dos dois.

### Despertar: o afeto da vigília sobre o sonho (lista, combinável)

`alivio` · `decepcao` · `acordou_mal` · `acordou_bem` · `desorientado` ·
`acordou_neutro`

| valor | exemplo |
|---|---|
| `alivio` | "ainda bem que era só um sonho"; alegria ao acordar **porque o sonho não era real** (não é `acordou_bem`, e não faz a carga `prazerosa`) |
| `decepcao` | *"queria nunca ter acordado"* (`c45dd9f0e7a5b502`); "queria voltar pro sonho"; *"acordei triste porque não era real"* |
| `acordou_mal` | *"acordei com medo"* (`ed4ba913f392666c`), "acordei triste", "ainda me sinto mal", **choro depois de sonho sem conteúdo com valência** |
| `acordou_bem` | "acordei feliz", *"acordei rindo"* (`b226441a768783b3`), "acordei felizinha" |
| `desorientado` | confuso, sem saber onde está, testando o sonho contra o real: *"quando acordei fui correndo confirmar se era um sonho"* (`ebe1fa7c53207b39`), *"acordei e olhei pra trás / Era mentira >:("* (`aa90b6169175c0b5`) |
| `acordou_neutro` | **só** "e acordei": menciona o acordar e não dá afeto nenhum |

**Lista vazia = o texto não menciona o acordar.** Na revisão isso aparecia como
"nada"; na saída é `[]`.

**Vale o acordar e o lembrar.** *"como pode um sonho bom se tornar em dor ao
lembrá-lo?"* é `acordou_mal`: é o afeto da vigília sobre aquele sonho.

**Não é despertar** *(regras do Fitipe)*:
- **O acordar com "conteúdo próprio" sem afeto**, em que a pessoa acorda e toma o
  sonho como mensagem: *"tá bom, universo, já entendi a msg"*
  (`fa7c7db2bceff578`). Isso vai para **atribuição**.
- **O acordar bem por motivo externo ao sonho.** *"Tive um sonho bizarro, e uma
  ótima (pra mim) historinha pra uma História em quadrinho"* (`b7274254cae0fb03`):
  a alegria vem de o sonho virar material de arte, não do sonho. `despertar: []`.
- **A curiosidade.** *"queria voltar pra ver como terminava"* não é `decepcao` nem
  faz a carga `prazerosa`. Se não houver outro afeto, `despertar: []` e nota.

**"Acordei chorando"** *(Fitipe)*:
- se o texto menciona o sonho, **o conteúdo do sonho dá o sentido do choro**:
  luto, perda, medo → `acordou_mal`; sonho de reencontro dito como bom →
  `acordou_bem` ou `decepcao`, conforme o texto;
- se o conteúdo não tem valência (*"sonhei com o casamento das minhas amigas /
  acordei chorando pra caramba"*, `706dedf36d2434bb`), **choro depois de sonho =
  `acordou_mal`**;
- nunca `acordou_neutro`, que fica só para "e acordei".

**"Acordei triste porque não era real"** = `decepcao` (o sonho era melhor que
acordar) **+ `acordou_mal`** quando o texto diz "triste" ou outro mal-estar além
da decepção. Se só diz "queria que fosse real", fica só `decepcao`. Em todos
esses casos a carga é `prazerosa`: o texto diz que o sonho era melhor.

Sai `sem_saber_se_foi_real`: é o mesmo fato de `memoria: nao_sabe_se_sonhou`.

### Vários sonhos no mesmo texto

Quando o texto conta **dois ou mais sonhos** (na mesma noite ou em noites
diferentes):
- **`carga` e `despertar` cobrem o conjunto**: liste o valor de cada sonho.
  *"Sonhei tava fazendo xixi, mas… era tipo sangue… tempinho atrás sonhei meu
  xixi era um tom dourado"* (`689fd5a7f944a33e`) tem dois sonhos em noites
  diferentes.
- **Confira se o segundo é mesmo sonho.** *"acordei feliz pq sonhei com mingyu
  mas dps de 15min tentando voltar pro sonho minha mente escolheu lembrar q o
  hannie vai embora e eu enjooei"* (`a8c1ccaac1b19d50`): o Fitipe perguntou "2
  sonhos?", mas a segunda parte é lembrança acordada. Fica um sonho só,
  `prazerosa`, e a virada vai para o despertar (`acordou_bem`, `acordou_mal`).
- `mista` fica reservada para **um mesmo sonho** com os dois afetos. Dois sonhos,
  um bom e um ruim, são `["prazerosa","aflitiva"]`, não `mista`.
- Marque **`multiplos_sonhos`** em `marcas` e diga na nota qual valor vai com
  qual sonho.
- `conteudo`: `narrado` se ao menos um sonho foi narrado.

Não é `multiplos_sonhos` o mesmo sonho repetido (isso é `repeticao`), nem a
retomada depois de acordar (`retomado`).

### Recorrência: `repeticao` (só literal)

| valor | o que se repete |
|---|---|
| `sonho_recorrente` | o mesmo sonho, em noites diferentes |
| `figura_recorrente` | a mesma pessoa ou coisa, em sonhos diferentes: *"as vezes ela vem de ladrão em sonho"* (`f84e64c0539d18be`, portão `literal` + `fala_do_sonhar`) |
| `tema_recorrente` | o mesmo assunto, cenas diferentes |
| `repetido_na_noite` | o mesmo sonho, na mesma noite |
| `retomado` | continua de onde parou, depois de acordar |
| `fragmentado` | sonhos diferentes numa noite entrecortada |

**A regra da colagem** vale para todas as bolsas: **decide a que a palavra está
colada.**

| a palavra | colada ao ato de sonhar | colada à cena | colada a outra coisa |
|---|---|---|---|
| "de novo" | repetição do sonho | "trabalhando de novo": não é | ao *dormir* ("dormi de novo e sonhei") = `fragmentado`; à insônia = nada |
| "esqueci" | falha de memória | — | ao *contar* ("esqueci de contar gnt") = nada |
| "não lembro" | amnésia | detalhe da cena | dentro da fala do sonho = nada |
| "significa", "premonição" | atribuição | **dentro** do sonho = nada | linguístico = nada |

A posição resolve a palavra, mas não dispensa ler o resto: *"eu só sonho com isso
agora"* afirma recorrência sem "de novo".

### Modo: `modo` (literal e fala_do_sonhar)

`lucido` · `paralisia_do_sono` · `falso_despertar` · `hipnagogico` ·
`memoria_revivida`

`modo` é o fenômeno do sonhar, e `repeticao` é o que se repete. Um sonho pode
ter os dois. **`lucido` é lucidez** (saber que sonha), não vivacidade: "sonho
muito lúcido" quase sempre quer dizer vívido. Sob `fala_do_sonhar`: *"infelizmente
eu tenho sonhos lúcidos"* → `lucido`. Imagens intrusivas ao adormecer, fora de
um sonho contado, são `hipnagogico` sob `fala_do_sonhar`. A **saída do corpo** não
vira `modo`: vai para a atribuição, com a palavra da pessoa.

### Memória: `memoria` (literal e fala_do_sonhar)

`esqueceu_um_pedaco` (a esmagadora maioria) · `nao_lembra_nada` ·
`nao_sabe_se_sonhou` · `nao_sonhou` · `lembrou_depois`

`nao_sonhou` é afirmação, não falha: *"dormi tanto q chega nem sonhei"*.
`lembrou_depois`: *"Lembrei agora que sonhei com a mamãe"*. Sob `fala_do_sonhar`:
*"não sei se não sonho ou só não lembro"* → `nao_sabe_se_sonhou`; *"vou lembrando
dos meus sonhos em momentos aleatórios do dia"* → `lembrou_depois`.

### Figura: `figura` (só figurado, lista)

| valor | o que é |
|---|---|
| `desejo` | "meu sonho é X", "sempre sonhei em X" |
| `intensificador` | "que pesadelo", "um sonho de pessoa", "casa dos sonhos" |
| `toponimo` | lugar: "Vale dos Sonhos" |
| `marca` | produto ou empresa: "Elseve Longo dos Sonhos" |
| `titulo_obra` | título de filme, série, livro, música: "Pesadelo na Cozinha" |
| `homonimo` | outra palavra com a mesma grafia: **o sonho de padaria (o doce)**: "comi um sonho de creme", "sonho de doce de leite" |
| `votos` | Boa-noite, despedida, felicitação: "bons sonhos", "doces sonhos", "sonhe com os anjos", "lindos sonhos", "realize seus sonhos" |
| `escape` | *nome a confirmar.* "Sonho" como devaneio ou fuga sem cena: "vivo nos meus sonhos", "sonho acordado" |
| `comercial` | "sonho" como apelo de venda sem nome próprio: "realize o sonho da casa própria" |

`toponimo`, `marca`, `titulo_obra` e `homonimo` substituem o antigo
`nome_expressao`. `votos` fecha o maior buraco da v3.3: cerca de 90 votos
formulares ficaram com `figura: []` em três lotes. "Realize seus sonhos" dito
como voto é `votos`, e a crença no desejo alheio não entra em `desejo`.

### O estado do desejo: `desejo_estado` (só com `figura: desejo`)

`pendente` · `realizado` · `perdido` · `nenhum` · `generico`

*"meu sonho é ir num show"* é `pendente`, *"esse drone foi a realização de um
sonho"* é `realizado`, *"a vida que eu sonhei morreu"* é `perdido`. **O
imperfeito "meu sonho ERA" não quer dizer perdido**: no português falado é tempo
de narrativa. *"era um sonho meu de infância"* (conhecer o Rio, e ele foi) é
`realizado`. Marque `perdido` só quando o texto disser que o desejo acabou
(*"meu sonho era X, desisti"*).

- `nenhum`: *"não tenho sonhos"*, *"sem sonhos"*.
- `generico`: o desejo como ideia, sem objeto de ninguém: *"siga seus sonhos"*,
  *"nunca desista dos seus sonhos"*.
- **"meu sonho" sozinho num comentário**, sem dizer o quê: `figura: desejo` +
  `falta_contexto`, `desejo_estado: null`.

### Presenças: `presencas` (para o portão inteiro)

`morto` · `morte_no_sonho` · `figura_publica` · `animal` · `religioso` ·
`personagem_ficcional` · `pessoa_inexistente` · `parceiro` · `ex_parceiro` ·
`familiar` · `sexo` · `violencia` · `trabalho` · `escola` · `perseguicao` ·
lista aberta.

`morto` é a visita de quem já morreu, e vale para bicho. `morte_no_sonho` é
alguém morrendo lá dentro. Par de calibração: "sonhei com meu pai e ele morreu tem
8 anos" contra "sonhei que meu pai morreu". `religioso` cobre entidade, orixá,
santo, guia, anjo e Deus quando **aparecem** no sonho. Deus invocado no
comentário ("misericórdia") não é presença. Sob `literal`, presença é **o que
aparece no sonho**: o pai morto de verdade que não aparece no sonho não é
`morto`.

### Atribuição: a palavra da própria pessoa (literal e fala_do_sonhar)

Registra **como a pessoa nomeia a experiência, ou a quem ou a que atribui a
origem e o alcance dela**, com a palavra dela, **e quem sustenta essa leitura**.
Quatro campos **paralelos**: são listas do mesmo tamanho, e o item *i* de cada
uma forma uma atribuição. Um texto pode ter várias.

**`atribuicao_palavra`**: a expressão literal do texto, curta, entre aspas, sem
corrigir a grafia: `"premonição"`, `"mensagem de Xangô"`, `"saída misturada com
sonho"`, `"viagem astral"`, `"visita"`, `"aviso"`, `"sinal do universo"`, `"já
entendi a msg"`, `"coisas da minha cabeça"`, `"significa"`.

**`atribuicao_origem`**: a quem ou a que a pessoa atribui.

| valor | quando |
|---|---|
| `a_si` | cabeça, subconsciente, medo, ansiedade, o que comeu, o que viu no dia: *"nos sonhos o que vem é sempre o que mais desejamos no nosso subconsciente"* |
| `entidade_religiosa` | orixá, santo, Deus, anjo, guia, entidade, "mundo espiritual" |
| `morto` | quem morreu vem, fala, visita |
| `universo_destino` | **só quando está escrito** "universo", "destino", "céus", "a vida" |
| `outra_pessoa` | um vivo: "sonhar com alguém é essa pessoa pensando em mim" |
| `espirito_proprio` | a própria pessoa (alma, espírito, corpo astral, "a imagem") sai e vai: saída do corpo, viagem astral. Também a **faculdade própria**: "minha mediunidade", "tenho previsão", com nota (menos prioritário). *A confirmar: use* |
| `outra` | origem dita e fora da lista (vidas passadas, astrologia, universo paralelo, figura pública: "o Kanye me avisou"). Diga qual na nota |
| `nao_diz` | nenhuma origem escrita. **"sinal", "aviso", "premonição" sem agente = `nao_diz`** |

**`atribuicao_quem`**: quem sustenta a crença ou a leitura.

| valor | quando |
|---|---|
| `a_pessoa` | quem escreve, por conta própria (inclui quem interpreta o sonho de outro) |
| `familia` | mãe, avó, tia, pai… *"minha vó dizia que sonhar com dente é morte"* |
| `religioso` | mãe ou pai de santo, pastor, padre, centro, terreiro, igreja |
| `rede` | TikTok, Instagram, "a moça do TikTok", cartomante online, perfil de sonhos |
| `busca` | Google, site de significados, ChatGPT ou outra IA |
| `amigo_parceiro` | amiga, namorado, colega |
| `dizem` | voz anônima: "dizem que", "é o que falam" |

**`atribuicao_postura`**: a postura **de quem escreve** diante dessa leitura
(dela mesma ou do outro). `afirma` · `cogita` · `pergunta` · `nega`

- `afirma`: toma como certo.
- `cogita`: considera possível, teme ou deseja, **sem "?"**: *"será que é um
  sinal"*, *"acho que foi aviso"*, *"deve ser"*, *"espero que não seja um sinal"*.
- `pergunta`: **a frase tem "?"**: *"será que é um sinal?"*, *"o que pode
  significar?"*, *"Sinais?"*.
- `nega`: duvida ou recusa: *"parecem ser mais coisas da minha cabeça"*, *"minha
  mãe diz que é aviso, eu não acredito"* (`familia` · `nega`).

**Regras que os lotes leram diferente, agora uniformes:** (a) sinal, aviso ou
premonição sem agente escrito é `nao_diz`, nunca `universo_destino`; (b) o "?"
decide entre `pergunta` e `cogita`.

**Casos com regra:**
- **Direção invertida**: a pessoa **envia** o sonho ou o desejo (*"recado pro
  universo"*, *"jogar pro universo"*, *"universo, eu recebo"*, *"se for sinal eu
  devolvo"*). Palavra entre aspas, origem `universo_destino` (ou a entidade
  nomeada) e marca **`pedido`**.
- **Gesto ritual ao acordar** (fazer guia, acender vela, oferenda, *"tá
  repreendido"*, recusar o chamado): é atribuição mesmo sem palavra de sentido.
  A palavra é o gesto entre aspas (`"acendi uma vela pra Exu Caveira"`), a
  origem é a entidade do gesto e o quem é quem mandou fazer, se dito.
- **Zombaria**: *"todo sonho tem significado"* citado para rir de um sonho
  absurdo = postura `nega` + marca `de_brincadeira`.
- **A fala da entidade dentro do sonho** não é atribuição. A leitura de quem
  acordou é.

**Exemplos da revisão:**

| texto | palavra | origem | postura | quem |
|---|---|---|---|---|
| *"tive uma saída misturada com sonho"* (`f9a32c77c2d27af2`) | `"saída misturada com sonho"` | `espirito_proprio` | `afirma` | `a_pessoa` |
| *"acho q foi uma mensagem msm / to acostumada a ter sonhos estranhos do mundo espiritual"* (`78e634f24547b0be`) | `"mensagem"` | `entidade_religiosa` | `cogita` | `a_pessoa` |
| *"tá bom, universo, já entendi a msg"* (`fa7c7db2bceff578`) | `"já entendi a msg"` | `universo_destino` | `afirma` (+ `de_brincadeira`?) | `a_pessoa` |
| Sonho com Erê (`d963c7c013af3131`) | `"comunicação efetiva"` · `"coisas da minha cabeça"` · `"um Erê pregando uma peça"` | `entidade_religiosa` · `a_si` · `entidade_religiosa` | `nega` · `cogita` · `cogita` | `a_pessoa` ×3 |
| *"medo de tsunami… me fez ter inúmeros sonhos premonitorios"* (`6600644c59672226`) | `"sonhos premonitorios"` | `a_si` | `afirma` | `a_pessoa` |
| *"pedi mais uma confirmação, e ele é tão incrível que eu sonhei mais uma vez"* (`20fc92c7f56456ca`) | `"confirmação"` | `nao_diz` ("ele" não identificado; `falta_contexto`) | `afirma` | `a_pessoa` |

**Correspondência sem nome.** *"sonhei que a casa do meu vizinho desmoronava e
quando acordei descobri que ele tinha se mudado, tenho medo dessas coisas"*
(`c1287e2104b8ea22`): a pessoa não dá nome à experiência. **Não escreva
"premonição"**. Marque `se_cumpriu`. Se o texto não traz nenhuma expressão
própria sobre o que aquilo foi, as quatro listas ficam vazias. Aqui traz uma, e
ela vai como está: `"tenho medo dessas coisas"` · `nao_diz` · `cogita` ·
`a_pessoa`.

**Não é atribuição:** "premonição" dita **dentro** do sonho; "significa" em uso
linguístico; o sonho usado como credencial social ("falei que sonhei pra puxar
assunto"), que vai para a nota.

### Marcas (lista, combinam com qualquer portão)

| marca | quando |
|---|---|
| `multiplos_sonhos` | dois ou mais sonhos no texto (ver acima) |
| `suspeita_circulacao` | o anotador reconhece letra de música ou meme. Quem confirma é a máquina (`copias.py`). Com letra, escreva "letra de música" na nota e anote o sonho normalmente |
| `texto_gerado` | texto gerado por IA, template de aplicativo ou de afiliado, copypasta. Anote o portão pelo que o texto faz |
| `pedido` | a pessoa **envia** o sonho ou o desejo ao universo ou a uma entidade (ver atribuição) |
| `falta_contexto` | **o texto não pode ser julgado** sem a imagem ou o fio que a coleta não guardou. Um "isso daí" solto não basta. *(Junta as antigas `falta_imagem` e `falta_fio`)* |
| `texto_truncado` | o texto chegou mutilado ao banco ("sonhei sobre ."). É defeito da coleta |
| `se_cumpriu` | *a confirmar; use.* O texto diz que algo do sonho aconteceu depois, na vigília: *"tive um sonho horrível e ele literalmente se realizou meia hora depois"* (`37213ddd7394fca2`). Registra o fato relatado, não o avaliza. Responde ao pedido do Fitipe de contar "quantos textos falam sobre coisas sonhadas que se concretizam" sem chamar isso de premonição |
| `de_brincadeira` | *a confirmar; use.* Ver abaixo |
| `bandeira` | ver o critério abaixo |

### `de_brincadeira`: a ironia como marca solta (a confirmar)

*Os valores marcados "a confirmar" (`de_brincadeira`, `se_cumpriu`,
`espirito_proprio`, `escape`) **devem ser usados**: é a medição que
vai decidir se ficam e com que nome.*

**Por que sobrevive, com `tom` fora.** A ironia é o único traço de tom que
**inverte a leitura de outros eixos**. *"Hoje eu tive aquele sonho bom) / (Sonhei
que era o fim do mundo"* (`4dae40d92b498663`): a palavra dita é "bom", e o Fitipe
marcou `prazerosa` e perguntou "ironia?". Sem a marca, o arquivo guarda como
prazeroso um sonho do fim do mundo dito com deboche. Com ela, a carga continua
registrando a palavra dita (a regra não muda) e a marca avisa que ela está
invertida. **Não corrija a carga: marque.**

**Marque `de_brincadeira` quando houver distância entre o dito e o querido,
evidenciada por pelo menos um destes:**
1. **conteúdo que o texto marca como ruim, com um sinal de leveza que incide
   sobre o conteúdo**, e não sobre a conversa. A simples coocorrência não basta;
   humor sobre adversidade não é ironia;
2. **anticlímax com graça**: expectativa armada e esvaziada, **com o marcador
   incidindo sobre o esvaziamento como piada**;
3. **marcador explícito**: "sqn", "aham", citar a fala de outro para derrubá-la;
4. **ressalva que desmente**: *"ngm precisa dele (eu queria ele😭)"*.

**O anticlímax colide com o despertar, e o desempate é este:** *"Sonhei q pai se
importava cmg… acordei e vi q ele só se importava com ele mesmo KK"* tem a mesma
forma que carga + `despertar: decepcao`. **Quando o esvaziamento é a dor relatada
e o marcador só a amacia, não é `de_brincadeira`**: fica em carga e despertar.
Par de calibração: `051b7e3f146022bf` (brincadeira) contra `034b77394460604f`
(dor amaciada). Sem este desempate, todo sonho bom desmentido pelo acordar
viraria ironia, e esse é o padrão mais comum do arquivo.

**Não são sinal sozinhos:** "kkk", 😭 🥲 🫠 🥹, a hipérbole que *constitui* o
intensificador ("que pesadelo" por um unfollow). **Nunca marque porque o desejo
parece inconcebível.** Isso é limite de quem lê, não propriedade do texto.

### O critério da bandeira (Fitipe, 24/09 e 27/09)

**Levanta:** discurso de ódio dito pela **voz desperta e intencional**, seja no
uso figurado ("meu sonho é ver esses [grupo] sumirem"), seja no comentário de
vigília sobre um sonho (*"sonhei que bati em uma mulher, acordei até mais leve"*:
quem endossa é quem acordou). **Ódio dirigido a si mesmo também levanta**:
suicídio e auto-ódio ditos pela voz desperta, com intenção.

**Não levanta:** nada que esteja **dentro do sonho literal**: nem ódio, nem
violência, nem a própria morte. **Desabafo não é ódio**: "não aguento mais, quero
sumir" é desabafo, e "quero sumir" quase sempre é figurado. Hipérbole coloquial
("vou me matar", "quase me matei quando acordei") não levanta sozinha.

**A bandeira depende do presente** *(Fitipe, 27/09)*. Tentativa, ideação ou
autolesão **passada e superada**, sem discurso de ódio nem (auto)mutilação no
presente do texto, **não levanta**: é discurso de superação, e vai na nota
("tentativa passada, superada"). Levanta só o que está presente no texto. Uma
overdose em curso, um plano dito agora, ou tentativas que continuam, levantam.

Na dúvida, levante com `confianca: duvida` e explique na nota. **A bandeira não
classifica nada**: reserva o caso para decisão humana.

---

## FORMATO DE SAÍDA — uma linha JSON por relato

Um objeto por linha (JSONL), com todas as chaves presentes, na ordem abaixo.
Listas vazias `[]` e `null` onde o campo não se aplica. Nunca invente valor fora
dos listados, exceto em `presencas`, que é aberta.

```
{"id": "…",
 "portao": [literal|figurado|fala_do_sonhar|devaneio|obra|noticia|propaganda|descartavel|ambiguo],
 "sonhador": [proprio|terceiro|citado],
 "sonhador_autodeclarado": "H(20)"|null,
 "carga": [prazerosa|aflitiva|mista|estranha|sem_afeto_dito],
 "conteudo": "narrado"|"so_mencionado"|null,
 "despertar": [alivio|decepcao|acordou_mal|acordou_bem|desorientado|acordou_neutro],
 "repeticao": [sonho_recorrente|figura_recorrente|tema_recorrente|repetido_na_noite|retomado|fragmentado],
 "modo": [lucido|paralisia_do_sono|falso_despertar|hipnagogico|memoria_revivida],
 "memoria": [esqueceu_um_pedaco|nao_lembra_nada|nao_sabe_se_sonhou|nao_sonhou|lembrou_depois],
 "presencas": [...],
 "figura": [desejo|intensificador|toponimo|marca|titulo_obra|homonimo|comercial|votos|escape],
 "desejo_estado": "pendente"|"realizado"|"perdido"|"nenhum"|"generico"|null,
 "atribuicao_palavra": ["\"…\""],
 "atribuicao_origem": [a_si|entidade_religiosa|morto|universo_destino|outra_pessoa|espirito_proprio|outra|nao_diz],
 "atribuicao_postura": [afirma|cogita|pergunta|nega],
 "atribuicao_quem": [a_pessoa|familia|religioso|rede|busca|amigo_parceiro|dizem],
 "marcas": [multiplos_sonhos|suspeita_circulacao|texto_gerado|falta_contexto|texto_truncado|se_cumpriu|pedido|de_brincadeira|bandeira],
 "confianca": "alta"|"media"|"duvida",
 "nota": "…"}
```

**Checagens antes de gravar:**
- `carga`, `conteudo`, `despertar` e `repeticao` só com `literal` no portão
  (ou com `literal` entre as candidatas de `ambiguo`).
- `memoria`, `modo` e `atribuicao_*` só com `literal` ou `fala_do_sonhar`.
- `figura` só com `figurado`; `desejo_estado` só com `figura: desejo`.
- Hábito com conteúdo: `literal` + `fala_do_sonhar`, com `repeticao` preenchida.
- As quatro listas `atribuicao_*` têm o mesmo tamanho.
- `sem_afeto_dito` não vem com outra valência; `estranha` pode vir.
- `despertar` não traz `acordou_neutro` junto de valor com afeto.
- `sonhador` é lista, e `sonhador_autodeclarado` foi conferido.
- `descartavel`, `ambiguo`, `de_brincadeira` e `bandeira` pedem nota.
- Os ids do arquivo são exatamente os do lote servido.

**Exemplos:**

```
{"id":"689fd5a7f944a33e","portao":["literal"],"sonhador":["proprio"],"sonhador_autodeclarado":null,"carga":["sem_afeto_dito"],"conteudo":"narrado","despertar":["desorientado"],"repeticao":["tema_recorrente"],"modo":[],"memoria":[],"presencas":[],"figura":[],"desejo_estado":null,"atribuicao_palavra":[],"atribuicao_origem":[],"atribuicao_postura":[],"atribuicao_quem":[],"marcas":["multiplos_sonhos"],"confianca":"media","nota":"dois sonhos (xixi de sangue hoje; xixi dourado pastoso antes), nenhum qualificado em palavra. 'algo estranho kkk' é sobre a checagem ao acordar, não sobre o sonho."}
{"id":"f9a32c77c2d27af2","portao":["literal","fala_do_sonhar"],"sonhador":["proprio"],"sonhador_autodeclarado":null,"carga":["mista"],"conteudo":"narrado","despertar":["acordou_bem"],"repeticao":[],"modo":["lucido"],"memoria":[],"presencas":["parceiro","familiar","animal","religioso"],"figura":[],"desejo_estado":null,"atribuicao_palavra":["\"saída misturada com sonho\""],"atribuicao_origem":["espirito_proprio"],"atribuicao_postura":["afirma"],"atribuicao_quem":["a_pessoa"],"marcas":[],"confianca":"media","nota":"'será que estou sonhando?' dentro da experiência. Fala também das saídas do corpo em geral (fala_do_sonhar). Ex-sogra como figura materna."}
{"id":"873c3376389b853c","portao":["literal"],"sonhador":["proprio"],"sonhador_autodeclarado":null,"carga":["prazerosa"],"conteudo":"so_mencionado","despertar":["decepcao"],"repeticao":[],"modo":[],"memoria":[],"presencas":[],"figura":[],"desejo_estado":null,"atribuicao_palavra":[],"atribuicao_origem":[],"atribuicao_postura":[],"atribuicao_quem":[],"marcas":[],"confianca":"alta","nota":""}
{"id":"f84e64c0539d18be","portao":["literal","fala_do_sonhar"],"sonhador":["proprio"],"sonhador_autodeclarado":null,"carga":["sem_afeto_dito"],"conteudo":"narrado","despertar":[],"repeticao":["figura_recorrente"],"modo":[],"memoria":[],"presencas":["ex_parceiro"],"figura":[],"desejo_estado":null,"atribuicao_palavra":["\"o que mais desejamos no nosso subconsciente\""],"atribuicao_origem":["a_si"],"atribuicao_postura":["afirma"],"atribuicao_quem":["a_pessoa"],"marcas":[],"confianca":"media","nota":"primeira paixão de infância volta 'de ladrão em sonho'; hábito com conteúdo."}
```

---

## Ainda em aberto para o Fitipe

1. **Nome provisório:** `escape` em `figura`.
2. **Bandeira:** dêixis ("dessa guria") conta como alvo? Praga jocosa com alvo
   nomeado ("meu deus leva o bolsonaro") levanta? Pró-ana e transtorno alimentar
   no presente entram em ódio a si? Auto-depreciação forte sem intenção?
3. **Marcas com massa medida, ainda sem decisão:** `negacao_do_onirico` ("queria
   acordar e ver que foi só um pesadelo"), `sonho_compartilhado` ("eu também
   sonhei com isso"), `conta_automatizada` (bot), e `repeticao` cogitada ("ou já
   tinha sonhado esse plot antes?").

Os valores *a confirmar* (`de_brincadeira`, `se_cumpriu`, `espirito_proprio`,
`escape`) estão em uso. A decisão sai da medição.
