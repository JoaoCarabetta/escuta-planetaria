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
