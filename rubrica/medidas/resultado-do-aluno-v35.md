# O aluno v3.5 — o que aprendeu, o que não aprendeu

*27/09/2026, noite. BERTimbau base, leitura em janelas, oito cabeças. Treinado
nas 3.473 anotações v3.5 **na versão v3.5.1** do `final_v35.jsonl` (regravado às
19h50 com 101 mudanças em despertar, carga e bandeira), mais o portão das
anotações antigas. Medido na amostra-prova (300, gabarito v3.5 feito do zero,
completo) e na revisão cega do Fitipe (83). Números completos, classe a classe:
`aluno/avaliacao_v35.md` e `.json`. Pesos: `aluno/aluno_v35.pt`.*

## Resumo em quatro linhas

- **Portão: 92,2% exato na prova** (chute 62,8%; aluno antigo 90,2% no mesmo
  gabarito). Literal F1 97%, figurado F1 95%, e **fala_do_sonhar deixou de ser
  zero**: 64% de revocação, 47% de precisão (n=11).
- **Texto longo: o ganho real.** Na validação, nos textos acima de 1.000
  caracteres, literal/figurado vão de **70% (aluno antigo, truncado) para 94%**.
  A prova não mede isso: **nenhum dos 300 sorteados passa de 1.000 caracteres.**
- **Revisão cega do Fitipe: 95,2%** em literal × não-literal (antigo 81,9%);
  figurado com revocação de 95% (antigo 24%).
- **Carga e despertar mal passam do chute constante no acerto exato** (82,1 vs
  80,6; 83,7 vs 82,7). Aprenderam as classes grandes (aflitiva F1 76%, conteúdo
  98%); nas pequenas, não há o que medir com 300 sorteados.

## Como foi treinado, e as decisões

**Dados.** 3.473 anotações v3.5.1 → 3.440 depois de tirar 28 textos repetidos
(mesma fôrma, outro id), 4 `copy_paste` e 1 texto idêntico a um da prova. Fora
do treino por construção: os 300 da `amostra_prova`, os 83 da revisão cega e os
70 antigos do Fitipe. Validação: 10% (344), semente 2015, só v3.5.

**As anotações v3 entraram, só no portão e célula a célula.** Havia 3.348
relatos com anotação v3.x fora do final_v35 (nenhuma sobreposição). Regras
(`dados_v35.rotulos_v3`):
- `literal=1` na v3 → literal 1, **fala_do_sonhar -100** (podia ser hábito com
  conteúdo, que a v3.5 marca com os dois);
- `fala_do_sonhar=1` na v3 → fala 1, **literal -100** (podia ter conteúdo);
- nenhum dos dois → literal 0, fala 0;
- figurado, obra, notícia, propaganda, descartável valem como estão;
  **devaneio -100** (a v3.5 exige cena; o devaneio sem cena virou figurado);
- vários anotadores no mesmo relato: a célula só vale se todos concordam;
- todas as outras cabeças -100 (carga tinha outro sentido, bandeira outra regra,
  figura outros valores). Peso 0,5 na perda.

A decisão foi tomada pela validação, não pela prova: corri as duas versões
(A2 = só v3.5.1; B2 = v3.5.1 + portão da v3) e o critério declarado para
escolher entre elas era o F1 do portão na validação, a única cabeça em que a v3
entra. B2 0,93 contra A2 0,91 (exato 87,1% contra 84,8%). **Ficou B2.** No
critério composto das sete cabeças quase empatam (0,861 contra 0,865): a v3
não prejudicou as outras cabeças de forma mensurável. Na prova, B2 fica 0,6 ponto
acima de A2 no portão, o que é ruído (2 textos). **Declaração:** vi a prova de A2
antes de B2 terminar; a escolha seguiu a regra da validação e teria sido a mesma
se A2 tivesse ganho na prova.

**`ambiguo` é máscara.** Em `["literal","figurado","ambiguo"]` as candidatas
ficam -100 e as outras 0; as cabeças condicionais valem se literal está entre as
candidatas. Na prova, os 4 ambíguos ficam fora do acerto exato do portão.

**Viés de prior das bolsas.** Quatro das cinco bolsas foram pescadas por pista.
Tentei usar a bolsa `sorteio` para corrigir o prior e **não dá**: ela é sorteio
do arquivo inteiro (39% literal, 51% figurado), e a prova é sorteio dos 135.512
elegíveis (64% literal, 32% figurado). São populações diferentes. Não apliquei
correção nenhuma. Por sorte, no portão o treino (62% literal, 32% figurado) já
fica perto da prova; onde a pesca distorce mais é `fala_do_sonhar` (13,7% no
treino, 3,7% na prova) e `bandeira` (3,3% contra 0%), e é justamente ali que a
precisão cai (abaixo).

**Pesos de classe:** `pos_weight = sqrt(neg/pos)`, entre 1 e 10. Limiar 0,5 em
tudo; não ajustei limiar (a validação tem 1 ou 2 exemplos das classes raras).

**Raros agrupados (<15 exemplos):** em `figura`, metáfora (14), escape (14),
título de obra (6), comercial, homônimo, marca e topônimo viraram `outra`. Em
`origem`, `outra_pessoa` (12) foi para `outra`. Metáfora e escape ficaram por um
exemplo abaixo do corte; o corte é o que foi pedido, e com 14 exemplos cada não
seriam aprendidas.

**Janelas.** 256 tokens, passo de 200; até 4 janelas no treino e 12 na
inferência, com prioridade para a primeira janela e as que contêm
"sonh"/"pesadel". O `testar_janelas.py` (bge-m3) tinha mostrado que a **média**
de janelas puxa texto longo para o centro. Por isso a agregação é **atenção
aprendida sobre as janelas**, e não média: a janela do "sonhei" pode decidir
sozinha. 30% dos textos v3.5 de treino (916 de 3.096) têm mais de uma janela.

**Seleção de época:** média, na validação, de portão F1, carga F1, conteúdo,
despertar F1, figura F1, tem_atribuição F1 e origem F1. **A bandeira fica fora
do critério** porque a regra dela vai mudar. B2 foi melhorando até a 8ª época
(0,861) e ainda subia: há algum ganho a mais em treinar mais.

**Uma corrida morreu e foi refeita.** A primeira B (arquivo v3.5.1) esgotou a
memória do MPS na 4ª época, porque as janelas de tamanho variável fragmentam o
cache. Pus `torch.mps.empty_cache()` a cada 50 passos e refiz como B2. A corrida
A, feita com o `final_v35` **anterior** ao regravamento, fica no log só como
referência; nada do relatório sai dela.

## Portão — a vitória continua, e ficou mais larga

Amostra-prova, 296 (fora 4 ambíguos):

| | aluno v3.5 | aluno antigo, mesmo gabarito | chute constante | teto (v3.2) |
|---|---|---|---|---|
| **exato** | **92,2%** | 90,2% | 62,8% | 93% |

| classe | n | v3.5 precisão | v3.5 revocação | v3.5 F1 | antigo revocação | antigo F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|
| literal | 192 | 96,4% | **98,4%** | **97,4%** | 96,4% | 96,9% | 78,7% |
| figurado | 96 | 95,8% | **94,8%** | **95,3%** | 91,7% | 90,3% | 49,0% |
| fala_do_sonhar | 11 | 46,7% | **63,6%** | **53,8%** | 0% | 0% | 7,2% |
| obra | 1 | — | 0% | 0% | 0% | 0% | 0,7% |
| propaganda | 1 | 100% | 100% | 100% | 100% | 66,7% | 0,7% |
| descartável | 2 | 100% | 50% | 66,7% | 0% | 0% | 1,3% |
| notícia | 0 | (2 marcados à toa) | — | — | — | — | — |
| devaneio | 0 | — | — | — | — | — | — |

O teto de 93% é o da auditoria da v3.2, o único medido; **não há teto medido
para a v3.5**. A régua mudou pouco onde importa: nos mesmos 296 relatos, o
gabarito v3.5 coincide com a anotação v3.2 em 98,6% no literal e 99,0% no
figurado. Então o 92,2% está onde estava o teto antigo, e o que resta de erro é
provavelmente fronteira.

**`fala_do_sonhar` agora existe.** Com 421 exemplos (a v3.5 permite o par
literal + fala), o aluno marca a classe e acha 7 dos 11. Mas marca 15 para
acertar 7: a precisão (47%) paga o prior inflado do treino (13,7% contra 3,7%
na prova). **Usar como candidato, não como contagem.**

**As raras continuam sem medida.** Obra, propaganda, descartável: 1, 1 e 2 casos
na prova. Acertar 1 de 1 não é aprendizado demonstrado. Os 2 falsos `noticia`
mostram a mesma pressão de prior: 32 notícias no treino, zero na prova.

**Texto longo, onde as janelas fazem a diferença** (validação; nenhum dos dois
alunos a viu no treino, porque o antigo treinou em `anotacoes_v3`, disjunta).
Acerto por célula em literal e figurado:

| | curtos ≤1.000 (237) | longos >1.000 (107) |
|---|---|---|
| **aluno v3.5 (janelas)** | 98,7% | **93,9%** |
| aluno v3.5 só v3.5 (A2) | 97,9% | 90,1% |
| aluno antigo (192 tokens) | 96,0% | **70,3%** |

**É o maior ganho desta rodada, e a prova não o enxerga**, porque o sorteio
uniforme dos elegíveis não trouxe nenhum texto longo. No arquivo inteiro, 25% do
material de treino passa de 1.600 caracteres. O aluno antigo errava quase um
terço deles.

## Revisão cega do Fitipe — o humano no topo

83 relatos, 55 literais, 21 figurados, no vocabulário dele (`nao_dormido` =
não literal):

| | v3.5 | antigo | chute constante |
|---|---|---|---|
| literal × não-literal | **95,2%** | 81,9% | 66,3% |
| literal: precisão / revocação | 93,2% / 100% | 82,3% / 92,7% | |
| figurado: precisão / revocação | 87,0% / 95,2% | 55,6% / 23,8% | |

É a melhor notícia do relatório: no único conjunto julgado por um humano, o
aluno chega a 95%, e o figurado sai de 24% de revocação para 95%. Ressalva: os
83 foram escolhidos por tipo (afeto, longo…) e não sorteados; não medem as
proporções do arquivo.

## Cabeças condicionais — medidas onde o gabarito abre a cabeça

### Carga (n=196 literais): passa do chute por pouco

| | aluno | chute constante |
|---|---|---|
| exato | **82,1%** | 80,6% (`sem_afeto_dito`) |

| valor | n | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|
| sem_afeto_dito | 158 | 93,5% | 91,1% | 92,3% | 89,3% |
| aflitiva | 22 | 80,0% | 72,7% | **76,2%** | 20,2% |
| prazerosa | 11 | 33,3% | 54,5% | 41,4% | 10,6% |
| estranha | 6 | 50,0% | 66,7% | 57,1% | 5,9% |
| mista | 1 | — | 0% | 0% | 1,0% |

**Comparado ao aluno antigo, o defeito diagnosticado sumiu em parte.** Antes ele
aprendia a ausência (90%) e não o afeto (aflitiva 48%, prazerosa 12% de
revocação). Agora aflitiva chega a 73% de revocação e 80% de precisão: partir o
eixo em carga × conteúdo funcionou. **Prazerosa continua fraca**: marca 18 para
acertar 6. A bolsa `afeto` inflou prazerosa no treino (11% dos literais) e a v3.5.1
ainda aumentou: "triste depois de sonho desejado" passou a ser prazerosa. Na
prova só 11 de 196 são prazerosos. É excesso de marcação por prior, não
cegueira.

### Conteúdo (n=196): aprendido

| | aluno | chute |
|---|---|---|
| exato | **97,4%** | 92,9% (`narrado`) |

`so_mencionado`: precisão 100%, revocação 64% (9 de 14), F1 78% (sempre-sim 13%).

### Despertar (n=196): no nível do chute

| | aluno | chute |
|---|---|---|
| exato | 83,7% | 82,7% (lista vazia) |

| valor | n | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|
| acordou_mal | 17 | 50,0% | 35,3% | 41,4% | 16,0% |
| acordou_neutro | 7 | 33,3% | 42,9% | 37,5% | 6,9% |
| desorientado | 6 | 33,3% | 16,7% | 22,2% | 5,9% |
| decepcao | 3 | 12,5% | 33,3% | 18,2% | 3,0% |
| acordou_bem | 2 | 50,0% | 100% | 66,7% | 2,0% |
| alivio | 0 | (0 marcados) | — | — | — |

Todo F1 fica acima do "sempre sim", mas o acerto exato empata com dizer "não
fala do acordar". Na validação (bolsas ricas em despertar) o micro-F1 é 0,77; no
sorteado, onde 83% dos literais não mencionam o acordar, cada falso alarme pesa.
**E esta cabeça é a que mais mudou na v3.5.1** (choro de emoção, triste-porque-
não-era-real): 101 anotações mexeram justamente aqui. **Não usar para contagem.**
Serve para puxar candidatos de `acordou_mal` para leitura.

### Figura (n=100 figurados): aprendida nas grandes

| | aluno | chute |
|---|---|---|
| exato | **84,0%** | 68,0% (`desejo`) |

| valor | n | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|
| desejo | 70 | 94,5% | 98,6% | **96,5%** | 82,4% |
| intensificador | 19 | 69,2% | 94,7% | **80,0%** | 31,9% |
| outra | 9 | — (1 marcado, errado) | 0% | 0% | 16,5% |
| votos | 0 | — | — | — | — |

`outra` (metáfora, escape, títulos, marcas…) é uma lixeira heterogênea de 37
exemplos: não se aprende como classe. Na prova ela vale 9% dos figurados, e o
aluno a joga quase sempre em intensificador (26 marcados para 19). **Votos** tem
81 exemplos no treino e zero na prova: não há como dizer se foi aprendido.

### Atribuição (n=201 literal/fala; 37 com atribuição)

| | aluno | chute |
|---|---|---|
| tem_atribuição, exato | 87,1% | 81,6% (não) |

`tem_atribuição`: precisão 74%, **revocação 46%**, F1 57% (sempre-sim 31%).
Conservador: quando marca, costuma acertar, mas deixa passar mais da metade.
A2 (só v3.5) fazia um pouco melhor aqui (60% de revocação, F1 66%).

Origem (n=37, exato 45,9%, chute 35,1%): `nao_diz` F1 65% (sempre-sim 55%),
`a_si` 58% (sempre-sim 58%, **empate com o chute**), `entidade_religiosa` 1 de 5.
Com 37 casos na prova, essa cabeça não tem medida estável. **Não usar sem
leitura.**

### Bandeira: sem medida, e a regra vai mudar

Na prova, **0 bandeiras no gabarito**; o aluno marcou 1 (`76b733033c0ab160`,
"Eu queria sumir e acabar logo com isso", perseguição da ex). Pela regra
v3.5 é desabafo e não levanta. **Pela regra que vem (ideação presente sem plano
levanta), talvez levante.** Na validação (12 positivos em 344) o F1 da bandeira
oscila entre 0,1 e 0,6 de época para época: é a cabeça menos estável do modelo.
O treino usou o `final_v35` v3.5.1, que já traz a regra nova da ideação
presente (112 bandeiras). **A cabeça foi treinada com a regra de hoje. Quando a
regra fechar, ela precisa de reanotação e retreino. Não usar para nada além de
separar candidatos para leitura humana.**

## O confundidor da propaganda continua sem teste

Zero textos da prova têm link ou preço sem ser anúncio, como na rodada anterior.
Sigo devendo o conjunto sorteado entre textos com link.

## Onde está no teto, e onde não

- **No teto (ou perto):** portão literal/figurado (92,2% contra 93% de teto
  v3.2; 95% na cega humana), conteúdo (97%), figura desejo/intensificador.
- **Aprendeu, mas o prior das bolsas estraga a precisão:** fala_do_sonhar,
  prazerosa, notícia. Isso se conserta com limiar calibrado numa amostra
  sorteada, ou com uma correção de prior feita com uma amostra da mesma
  população da prova (a bolsa `sorteio` não serve).
- **Não aprendeu:** figura `outra`, carga `mista` (15 exemplos), `alivio`,
  origens raras, obra.
- **Sem medida:** bandeira, votos, devaneio, notícia, obra, propaganda (0 a 2
  casos em 300 sorteados). Para essas, a prova sorteada nunca vai bastar; só
  revocação contada em cima das bolsas.

## O veredito prático

**Usar:** o portão (literal, figurado), inclusive em textos longos, onde o
aluno antigo não servia. Conteúdo narrado × só mencionado.

**Usar com ressalva escrita:** fala_do_sonhar (candidato, precisão ~50%);
carga só em sem_afeto_dito × aflitiva; figura só em desejo × intensificador.

**Não usar sem leitura humana:** despertar, origem, tem_atribuição (perde metade),
prazerosa, e a bandeira (regra aberta).

## Arquivos

- `aluno/dados_v35.py`, `modelo_v35.py`, `treinar_v35.py`, `avaliar_v35.py`
  (os antigos não foram tocados)
- `aluno/aluno_v35.pt` = cópia de `aluno_v35_B2.pt` (escolhido);
  `aluno_v35_A2.pt` (só v3.5.1), `aluno_v35_A.pt` e `aluno_v35_B.pt` (corridas
  descartadas: arquivo antigo / morreu por memória)
- `aluno/treino_v35.log`, `aluno/aluno_v35_*_historico.json`
- `aluno/avaliacao_v35.md` e `.json`: todas as tabelas, inclusive A2

## Taxa de acerto do palpite, para a página

*Acrescentado 27/09, 23h. É o número para mostrar ao lado de cada palpite do
aluno: **quando ele diz X, quantas vezes X está certo** (precisão na
amostra-prova, 300 sorteados, gabarito v3.5). "Palpites na prova" é o n que
sustenta o número; a faixa é o intervalo de 95% (Wilson), que é o que 300
sorteados permitem afirmar. Limiar 0,5 em todas as classes.*

Critério da coluna "mostrar" (sugestão): **sim** com ≥20 palpites e a faixa
toda acima de 60%; **com aviso** com ≥10 palpites; **não** abaixo disso. Aí a
página diz "palpite sem taxa medida". Classes que o aluno não marcou nenhuma
vez na prova (devaneio, obra, votos, mista, alívio, morto…) não têm taxa.

Duas ressalvas para quem escrever a legenda. **(1)** Nas cabeças condicionais
(carga, conteúdo, despertar, figura, atribuição) a taxa foi medida nos textos
em que o *gabarito* abre a cabeça. Na página, o palpite aparece onde o *aluno*
abre a cabeça, e o portão erra cerca de 4%, então a taxa real ali fica um pouco
abaixo. **(2)** A taxa vale para a população da prova: posts e comentários
elegíveis, curtos, sem nenhum texto acima de 1.000 caracteres. Em texto longo o
portão foi medido só na validação (94% por célula).

| cabeça | palpite | palpites na prova | acertos | **taxa de acerto** | faixa 95% | mostrar |
|---|---|---|---|---|---|---|
| portao | literal | 196 | 189 | **96%** | 93–98% | sim |
| portao | figurado | 95 | 91 | **96%** | 90–98% | sim |
| portao | fala_do_sonhar | 15 | 7 | **47%** | 25–70% | com aviso |
| portao | noticia | 2 | 0 | **0%** | 0–66% | não (n pequeno) |
| portao | propaganda | 1 | 1 | **100%** | 21–100% | não (n pequeno) |
| portao | descartavel | 1 | 1 | **100%** | 21–100% | não (n pequeno) |
| carga | prazerosa | 18 | 6 | **33%** | 16–56% | com aviso |
| carga | aflitiva | 20 | 16 | **80%** | 58–92% | com aviso |
| carga | estranha | 8 | 4 | **50%** | 22–78% | não (n pequeno) |
| carga | sem_afeto_dito | 154 | 144 | **94%** | 88–96% | sim |
| conteudo | narrado | 187 | 182 | **97%** | 94–99% | sim |
| conteudo | so_mencionado | 9 | 9 | **100%** | 70–100% | não (n pequeno) |
| despertar | decepcao | 8 | 1 | **12%** | 2–47% | não (n pequeno) |
| despertar | acordou_mal | 12 | 6 | **50%** | 25–75% | com aviso |
| despertar | acordou_bem | 4 | 2 | **50%** | 15–85% | não (n pequeno) |
| despertar | desorientado | 3 | 1 | **33%** | 6–79% | não (n pequeno) |
| despertar | acordou_neutro | 9 | 3 | **33%** | 12–65% | não (n pequeno) |
| figura | desejo | 73 | 69 | **95%** | 87–98% | sim |
| figura | intensificador | 26 | 18 | **69%** | 50–83% | com aviso |
| figura | outra | 1 | 0 | **0%** | 0–79% | não (n pequeno) |
| tem_atrib | tem_atrib | 23 | 17 | **74%** | 54–87% | com aviso |
| origem | nao_diz | 23 | 12 | **52%** | 33–71% | com aviso |
| origem | a_si | 9 | 7 | **78%** | 45–94% | não (n pequeno) |
| origem | entidade_religiosa | 1 | 1 | **100%** | 21–100% | não (n pequeno) |
| origem | espirito_proprio | 1 | 1 | **100%** | 21–100% | não (n pequeno) |
| origem | universo_destino | 1 | 1 | **100%** | 21–100% | não (n pequeno) |
| bandeira | bandeira | 1 | 0 | **0%** | 0–79% | não (n pequeno) |

## Inferência no arquivo inteiro (27–28/09)

`aluno/inferir_v35.py` → tabela nova `predicoes_v35` (505.320 linhas, uma por
relato; `predicoes_v32` intocada). Guarda a probabilidade de cada classe de cada
cabeça, a decisão com limiar 0,5 e as portas da rubrica, `margem_portao`,
`n_janelas` e `herdado_de`. **Tempo: 36 minutos** (MPS, ~235 textos/s).
**Duplicatas herdam do canônico**: 7.961 linhas, com `herdado_de` preenchido;
52 delas eram cadeias (o canônico também era duplicata). Conferência: lendo a
decisão da tabela, a prova dá os mesmos 92,2%.

| portão (limiar 0,5) | todos (505.320) | post (340.993) | comentário (147.289) | continuação (16.517) |
|---|---|---|---|---|
| literal | 40,5% | 51,7% | 16,1% | 27,5% |
| figurado | 54,2% | 44,0% | 77,2% | 61,9% |
| fala_do_sonhar | 10,5% | 9,4% | 12,4% | 15,0% |
| propaganda | 1,3% | 1,6% | 0,3% | 4,6% |
| notícia | 0,8% | 1,0% | 0,1% | 1,2% |
| descartável | 0,7% | 0,8% | 0,3% | 2,8% |
| obra | 0,6% | 0,7% | 0,2% | 1,7% |
| devaneio | 93 textos | | | |
| nenhuma classe | 0,8% | 0,7% | 1,0% | 1,6% |

**Como ler.** Isto é o arquivo inteiro, não os 135 mil elegíveis da prova (onde
o literal é 64%). A taxa de acerto medida vale para a população da prova. Fora
dela, e sobretudo nos comentários, é extrapolação.
**fala_do_sonhar a 10,5% está inflada**: na prova o aluno marcou 5% contra 3,7%
reais, com precisão de 47%. **Bandeira: 2.479 marcados (0,5%)**, e muitos são
desabafos depressivos sem plano ("sou um infeliz, deprimido"). Isso vale só como
fila de leitura humana, até a regra fechar. **Portão vazio (3.973)**: textos
curtos de uma linha ("pesadelo mds", "Odeio acordar de sonhos bons") em que
nenhuma classe passa de 0,5. São os primeiros candidatos a anotação, junto com
os 34.745 de margem < 0,1.
