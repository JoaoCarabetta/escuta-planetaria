# O que já está decidido pela medição, para a v3.3

*Acumulado durante a noite de 24/09, à medida que os anotadores de treino
voltavam. Cada item tem o caso concreto e quantos anotadores independentes o
acharam. Escrito agora para não depender da minha memória de conversa.*

## Consertos de campo que a medição já decidiu

**1. A `carga` precisa do quarto quadrante.** Seis anotadores, independentemente.
A v3.2 partiu o antigo `nao_dito` em "não diz o quê" (`sem_conteudo`) e "não diz
o como" (`sem_afeto_dito`) e **esqueceu o inverso**: o texto que diz o *como* e
não o *quê* — *"tive um pesadelo horrível hj"*. É construção frequentíssima, e
sem o valor cada anotador resolveu de um jeito: uns `aflitiva`, outros
`sem_conteudo`. **É ruído de rótulo na fronteira mais movimentada do eixo mais
importante.** Valor a criar: `afeto_sem_conteudo`.

Sub-regra que um anotador declarou e vale adotar: **só palavra de afeto conta
como afeto dito; emoji sozinho não conta.**

**2. Falta `estranha` na carga.** "esquisito", "bizarro", "estranho" são dos
qualificadores mais comuns do arquivo e caem em `sem_afeto_dito`, o que é falso
— o afeto foi dito, só não é prazer nem aflição. E `neutra` não serve:
estranheza não é neutralidade. (`neutra` deu 0 ou 1% em todos os lotes.)

**3. `despertar` precisa do espelho, e perde um valor.**
Falta `acordou_bem` — *"Acordei hoje feliz"*, *"acordei rindo muito"*,
*"acordei saltitante"* —, falta `desorientado` (*"acordei bem confuso"*,
*"acordei assim????"*) e falta o **acordar sem valência** (*"e acordei"*), que
hoje só cabe forçando `acordou_mal`, que afirma mal-estar.

E **sai `sem_saber_se_foi_real`**, que é redundante com
`memoria: nao_sabe_se_sonhou`: um anotador achou o texto que ativa os dois e
mostrou que é o mesmo fato em dois campos. `despertar` é o eixo do afeto.

**4. `memoria` e `modo` valem sob `fala_do_sonhar`, não só sob `literal`.** Três
anotadores gravaram valores contra a regra, de propósito e declarando na nota,
porque perder o dado custava mais: *"não sei se não sonho ou só não lembro"*,
*"infelizmente eu tenho sonhos lúcidos"*, *"vou lembrando dos meus sonhos em
momentos aleatórios do dia"*. A restrição a literal está certa para `carga` —
onde não há sonho não há dentro — e errada para memória e modo.

**5. `devaneio` sai do núcleo.** Zero em 300 sorteados **e** zero na própria
bolsa que o pesca, em dois lotes de treino. A causa está diagnosticada: os textos
da bolsa **enunciam** o imaginar sem narrar cena. Com a fronteira dos auditores
escrita — *devaneio exige cena com ação e duração, não só verbo de imaginar* —
ele fica correto e raro. Cabeça de classificador com seis exemplos responde
sempre "não" e exibe 99% de acerto.

**6. `falta_imagem` e `falta_fio` colapsam numa marca só.** Quatro anotadores
usaram as duas e nenhum achou que a diferença importasse para o julgamento.
**`texto_truncado` fica** — é a única das três que mede defeito de coleta, e um
anotador mostrou que ela nem aparece no treino porque o filtro de 25 a 700
caracteres já remove o truncado.

**7. `nome_expressao` está virando quatro coisas:** topônimo ("Vale dos
Sonhos"), marca ("Elseve Longo Sonhos"), título de obra ("Pesadelo na Cozinha") e
homônimo ("comi um sonho"). Três anotadores mapearam a mesma confusão.

## O critério da bandeira precisa de duas linhas

**O idiom brasileiro não levanta.** *"vou me matar"*, *"quase me matei quando
acordei"*, *"queria chorar e me matar"* são exasperação corrente. Um anotador
recusou os três e outro levantou um caso parecido — é divergência de critério, e
o critério é que está incompleto. **Hipérbole coloquial no pretérito não levanta
sozinha**; levanta com outro sinal (plano, meio, presente, pedido de ajuda).

**Dêixis conta como alvo identificável?** *"meu sonho é esfolar a cara dessa
guria"* tem alvo real e não nomeado. Precisa estar escrito.

**Transtorno alimentar e pró-ana** foram levantados por um anotador lendo "risco
a quem escreve" de forma abrangente, e a regra não diz. Decisão do Fitipe.

## A regra da ironia, terceira reescrita

O critério 1 — conteúdo ruim mais sinal de leveza — **dispara demais**. Um
anotador recusou quatro casos que satisfazem a letra e são humor-sobre-
adversidade, não ironia. Falta exigir explicitamente a **distância entre o dito
e o querido**, não só a coocorrência dos dois sinais.

E a hipérbole que *constitui* o intensificador ("que pesadelo" por um unfollow)
não vale como sinal — senão quase toda a bolsa `intensificador` viraria ironia.

## Categorias novas com massa medida

**Negação retórica do onírico** — *"então não tava tendo um pesadelo né"*,
*"queria acordar e ver que a morte do X foi só um pesadelo"*. Achada
independentemente por cinco anotadores: 2 em 80 na amostra-prova, 6 em 170 e 3
em 171 no treino. O sonho é invocado só para ser negado: o ruim é real.

**`celebratorio` no tom** — a v3.2 recusou por falta de massa. Apareceu em todos
os lotes desde então, sempre junto de `desejo_estado: realizado`, sempre forçado
em `leve` ou `confidencia`, que apagam a comemoração.

**`sonho_compartilhado`** — *"eu também sonhei com isso"*. O detector de
`copias.py` pega texto igual; não pega convergência declarada, que é o sonho
coletivo se reconhecendo.

**Texto gerado por aplicativo** — templates de app de leitura e de afiliado em
que "sonho" está só no título do produto. Um anotador achou quatro em 175 e
descartou com justificativa a contragosto: `descartavel` junta lixo de coleta
com texto humano sem assunto.

## Faltas de espécie em `atribuicao`

`teme_que_signifique` (*"espero que não seja um sinal"*) · `deseja_que_seja`
(*"eu só queria que isso fosse uma premonição"*) · `visita_do_morto` ·
`gatilho_emocional` (distinto de `residuo_diurno`) · `move_a_acao` (o sonho muda
uma decisão sem que se afirme sentido) · `fonte: popular` (jogo do bicho, dormir
de barriga para cima) e `fonte: alheia` ("me disseram").

## E uma ausência de campo que a `repeticao` revelou

**`repeticao` não tem `forca`, e `atribuicao` tem.** *"(ou já tinha sonhado esse
plot antes e buguei?)"* é recorrência **cogitada**: ou se afirma o que o texto
cogita, ou se perde o dado. A tripla `{especie, forca, fonte}` resolveu isso na
atribuição e é o modelo a copiar.

---

## O achado mais consequente da noite: o anticlímax colide com o despertar

Um anotador viu que o **critério 2 da ironia** (expectativa armada e esvaziada)
tem exatamente a mesma forma que o par `carga: prazerosa` + `despertar:
decepcao`. *"Sonhei q pai se importava cmg… acordei e vi q ele só se importava
com ele mesmo KK"*.

**Se o critério 2 bastar, todo sonho bom desmentido pelo acordar vira `ironico`**
— e isso são milhares de relatos, no padrão mais comum do arquivo. A cabeça do
tom aprenderia a marcar ironia em cima do eixo do despertar.

O desempate que ele aplicou ao lote inteiro e que entra na v3.3:

> **O anticlímax só é ironia quando o marcador incide sobre o esvaziamento como
> graça.** Quando o esvaziamento é a dor relatada e o marcador só a amacia, é
> `lamento`.

Par de calibração que ele deixou, com a mesma estrutura e decisões opostas:
`051b7e3f146022bf` (ironia) contra `034b77394460604f` (lamento).

E um item a devolver: a **"ressalva que desmente"** perdeu autonomia ao ser
absorvida no critério 1, e com ela se perdeu *"ngm precisa dele (eu queria
ele😭)"* — distância pura entre o dito e o querido, sem conteúdo ruim, sem
expectativa armada e sem marcador explícito. Volta como critério 4.

## `suspeita_circulacao` está medindo duas coisas incompatíveis

Dos 13 usos de um anotador, **8 são conta automatizada** (quatro do mesmo
template de afiliado, mais bots de horóscopo e agregador) e só 3 são circulação
humana — letra citada sem aspas, formato de meme.

São fenômenos de natureza diferente: bot é propriedade do **emissor**, copypasta
é propriedade do **texto**. E o detector por comprimento × tempo lê os dois como
"longa, muita gente, janela de dias" — o corte de 45 dias não os separa. Pede
marca própria: `conta_automatizada`.

## Emoji não fixa tom, e isso precisa estar escrito como se escreveu do "kkk"

O mesmo anotador mostrou 😭 marcando entusiasmo num texto e dor em dois outros,
e 🥲 não decidindo nada. A v3.2 escreveu que "kkk sozinho não é sinal" e parou
ali. **Listar explicitamente 😭 🥲 🫠 como insuficientes sozinhos.**

## Duas exceções nomeadas que a rubrica deve trazer

A regra "'meu sonho é X' é quase sempre figurado" tem contraexemplo direto:
*"**meu sonho clássico** é voltar pro primeiro emprego. sempre sonho q voltei pra
C&A"* — é literal. E a simétrica: há quem use "sonhei" para devaneio
autodeclarado.

## A definição de devaneio que a v3.3 deve usar, escrita por um sonhador

Um relato do próprio arquivo faz a distinção melhor do que eu fiz em três
versões: *"meus sonhos (**enquanto durmo, nao os devaneios**) estao mais
imersivos"*. A fronteira é do falante, não nossa.

---

## DECIDIDO (Fitipe, 24/09): a bandeira é só discurso de ódio, e só na voz desperta

Resolve as duas colisões abaixo e substitui o critério da v3.2.

**Levanta:** discurso de ódio dito pela **mente desperta e intencional** — no uso
figurado de sonho/pesadelo ("meu sonho é ver esses [grupo] sumirem") ou no
comentário de vigília sobre um sonho ("sonhei que bati em uma mulher, acordei
até mais leve": o endosso é de quem acordou).

**Não levanta:** nada que esteja **dentro do sonho literal** — nem ódio, nem
violência, nem a própria morte. Sonhar a própria morte não levanta.

**Ódio dirigido a si mesmo também levanta (Fitipe, 24/09, mesma conversa)** —
sem marca separada. Suicídio e auto-ódio ditos pela voz desperta, com intenção,
entram na mesma bandeira. **Desabafo não é ódio:** "não aguento mais, quero
sumir" é desabafo, e "quero sumir" é quase sempre figurado em PT-BR. A
fronteira é sutil e não vai ser pega sempre — por isso:

**A bandeira carrega uma probabilidade** ("x% de ser discurso de ódio"), não só
0/1. Cuidado já medido: confiança AUTO-DECLARADA por LLM é inútil (490/491 do
llama ≥0,7). A porcentagem tem que vir de onde é calibrada — a saída de uma
cabeça do BERTimbau treinada nisso, ou a confiança alta/média/dúvida dos
anotadores Claude, que o julgamento cego mostrou calibrada (94/100/52%).
Problema prático: a bandeira é rara (0/70 no Fitipe, quase zero na prova) —
uma cabeça precisa de exemplos positivos, que teriam de ser buscados de
propósito (anotação dirigida, não amostra uniforme).

As seções abaixo ficam como histórico da pergunta.

## PARA O FITIPE DECIDIR: o critério da bandeira se contradiz num ponto

Um anotador achou o texto que quebra a regra: *"sonhei que tava tentando me matar
de diversas maneiras e não conseguindo"*, aberto com *"É muito pesado dizer
que…?"*.

A exceção escrita diz **não levantar** quando alguém morre dentro do sonho — ela
existe para impedir que conteúdo onírico narrado seja lido como violência. A
cláusula de risco diz **levantar** quando há sinal de risco a quem escreve. As
duas se aplicam ao mesmo texto. Ele levantou com `duvida`, que é o que a rubrica
manda na dúvida, e avisou: **é o único ponto do critério que precisa de uma frase
antes de rodar nos 174 mil.**

**O que eu proponho, e é você que decide:** a exceção cobre **outras pessoas**
morrendo no sonho. Quando o sonhador sonha a própria morte ou a própria
automutilação **e a moldura fora do sonho mostra sofrimento** — a pergunta
hesitante, o pedido de ajuda, o "não aguento mais" —, levanta.

O que me faz propor assim é que a moldura está fora do sonho: *"é muito pesado
dizer que"* não é conteúdo onírico, é alguém se perguntando se pode falar. Mas
isto decide o que o arquivo faz com relato de sofrimento real, e essa não é
decisão técnica.

## A `carga` deve virar dois campos, e agora são três anotadores dizendo

A formulação mais limpa veio assim: **um campo para o conteúdo** (dito / não
dito) e **um para o afeto** (prazeroso · aflitivo · misto · estranho · nulo /
não dito).

O eixo único obriga a escolher entre duas verdades — *"acordei no meio da noite,
de um sonho ruim"* é `aflitiva` **e** `sem_conteudo` ao mesmo tempo. E resolve de
uma vez o quadrante que falta, o `estranha` que falta, e o `neutra` que quase não
aparece mas tem uso legítimo: um anotador achou o caso exato, conteúdo
violentíssimo com afeto explicitamente nulo (*"isso nunca me incomodou muito"*)
— afeto **dito** e nulo, que é diferente de não dito.

## Uma frase que precisa entrar, ou metade dos desejos vira "perdido"

**O imperfeito "meu sonho ERA" não significa desejo perdido** no português
falado. É tempo de narrativa, não de luto. Sem essa frase escrita, um anotador
prevê que metade dos `pendente` viraria `perdido` — e o classificador aprenderia
o tempo verbal em vez do estado.

## Armadilha lexical nova, e das boas

*"Sonhei horrores de novo"* — **"horrores" é "muito", não "horrores"**. O texto
segue com *"Um lugar lindo"* e a carga é prazerosa. Um classificador de
superfície lê aflitiva com confiança.

## E um pedido de aperto que eu aceito

**`tom` deveria ser dispensado em `propaganda`, `obra` e `noticia`**, pelo mesmo
argumento que dispensou `carga` fora do literal: num anúncio o tom mede registro
de marketing, não maneira de alguém contar. Numa letra, mede o eu-lírico.

---

## Achado sobre a integridade do arquivo, e é o mais consequente da noite

Um anotador encontrou um **script de sedução** que ensina a mandar um relato de
sonho fabricado: *"Sonhei com você, mas ainda tô tentando entender se foi um
sonho ou um aviso"*. E encontrou, no mesmo lote, o texto que é indistinguível
dele pela leitura pura — *"catarina essa tarde sonhei com você"* — e um terceiro
que é a mesma jogada feita com hesitação sincera.

**Existem no arquivo relatos literais que ninguém sonhou**: curtos, repetidos
entre contas, e trazendo `atribuicao: aviso` de brinde, porque o script manda
dizer isso. Não é ruído de coleta — é gênero de fala. E o pior é que o script
*ensina* a marca que a rubrica usa para reconhecer sinceridade.

Isto não se resolve com campo novo. Resolve-se sabendo que existe, contando
quantos são (o detector de fôrmas ajuda) e dizendo na tese que uma parte do
corpus é performance de intimidade, não relato.

## Duas observações de desenho que não são valores faltando

**Nada marca onde o sonho acaba.** Em vários relatos não há como saber se a
última frase é conteúdo do sonho ou reação da vigília — e isso **muda a carga**,
que é o eixo mais importante. A rubrica pressupõe uma fronteira que o texto não
dá.

**`sem_afeto_dito` mede o dito, não a ausência de afeto**, e isso precisa estar
escrito onde o número aparece. O caso que o anotador deu: aranhas, o cachorro
tentando salvá-la e sendo picado, *"acordei chorando a morte dele"* — recebeu
`sem_afeto_dito` porque nenhuma palavra diz como ela se sentiu **dentro** do
sonho. A regra é certa e o rótulo engana: **os 60,4% não dizem que o arquivo é
afetivamente mudo, dizem que ele não nomeia o afeto.** Quem usar o dado depois
vai confundir as duas coisas se ninguém escrever isso.

## Segunda colisão na bandeira, também para o Fitipe

*"meu deus leva o bolsonaro"* é praga jocosa **com alvo real e nomeado**. O
gatilho manda levantar; a exclusão isenta praga jocosa "sem alvo nomeado". O
anotador levantou com dúvida e avisou da consequência: **isso levanta bandeira em
massa no gênero mais comum do Twitter brasileiro.**

E um vizinho que expõe um buraco de verdade: *"sonhei que bati em uma mulher,
acordei até mais leve"* — a exclusão cobre o **conteúdo do sonho** e não previu o
**endosso feito na vigília**. Esse é diferente dos outros e provavelmente é o
único dos três que a regra deveria pegar.

## O pedido que eu levaria mais a sério, se fosse escolher um

> *"Meia página mapeando os vinte emojis mais frequentes a tons renderia mais
> que qualquer dado novo."*

Cinco textos de um lote de 175 tiveram o tom decidido **inteiramente por um
emoji ambivalente** — 😫 😪 🥹 🤓 😍 — e a rubrica não diz uma palavra sobre
emojis. O tom concordou em 75%, e esta é provavelmente a maior fatia desses 25%.
