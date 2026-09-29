# Planeta V3 — prévia local (28/09, madrugada)

Nada daqui foi publicado nem commitado. `planeta-v2/` (a que está no ar) não foi tocada.

## Ver a prévia

```
cd ~/Desktop/arte_c_joao_tta/escuta_planetaria
python3 -m http.server 8765 --bind 127.0.0.1
```
e abrir **http://127.0.0.1:8765/planeta-v3/**. É preciso servir a raiz do repositório,
não a pasta, para o link "ver v2" funcionar. No celular: o mesmo servidor com
`--bind 0.0.0.0` e o IP do Mac na rede, ou o túnel de sempre.

## Gerar de novo

```
cd planeta-v3
python3 gerar.py      # ~1 min; lê arquivo.db (só leitura) e rubrica/lotes/
python3 conferir.py   # relê o cuidado do zero e confere; sai com erro se algo vazou
```
A projeção (`dados/projecao.npy` + `projecao_ids.txt`) é a nova, copiada de
planeta-v2/dados (feita pela predicoes_v35; não cobre os ~3,7 mil ids que só a predicoes_v36 tem, que por isso ainda não entram na página). Não precisa ir para o repositório
(14 MB, reconstruível com planeta-v2/projetar.py).

## Números

| | |
|---|---|
| pontos na página | **493.016** |
| lidos | **3.669**: 3.587 pelo Opus e 82 pelo Fitipe (dos 3.773 + 83; os outros 187 têm bandeira ou não estão na projeção) |
| palpites (portão v3.5 · demais cabeças v3.6) | **489.347** |
| fora por cuidado | **4.339 pontos** (4.421 ids com bandeira; mais 89 por cópia canônica e 6 por texto idêntico) |
| forma | post 332.648 · comentário 143.792 · continuação 16.070 · bluesky não verificado 506 |

Os ids com bandeira vêm de: anotações sab 174 · conferência de risco (v2 e v3.5.1,
todos os 19 lotes) 3.094 · anotação v3.x 134 · cuidado manual 2 · anotação Sonnet 28/09 40 · **977 que só o
aluno marcou (predicoes_v35.bandeira = 1; v3.6 onde não há v3.5) e ninguém conferiu como falso**. Estes
últimos saíram por precaução e são uma fila de leitura: muitos devem ser desabafo
sem risco, que poderia voltar.

## O que mudou

**Aluno (28/09): portão v3.5, demais cabeças v3.6.** Portão (literal, figurado, fala do sonhar,
camada, p_literal, p_figurado) e bandeira vêm da `predicoes_v35`; carga, despertar, figura,
conteúdo, atribuição e origem vêm da `predicoes_v36`, abertas pelo portão da página. Por quê: o
v3.6 aprendeu as classes raras, mas o portão dele piorou 1,3 ponto na prova (92,2% → 90,9%) por
prior inflado (83,6% de literais no treino), e o corte calibrado (p_literal > 0,66) só corrige a taxa
de literal do arquivo, não o acerto (`rubrica/medidas/portao_v35_v36_calibrado.md`). Relatos só com
v3.6 usariam o portão do v3.6 com esse corte (`aluno/limiar_portao_v36.json`); hoje nenhum está na
projeção. Efeito nos palpites: passam a ter palpite mostrado *decepção* (aviso, acerta 15%) e
*só mencionado* (aviso, 78%).

**Cuidado.** Relato com bandeira não entra em arquivo nenhum: nem ponto, nem texto,
nem índice de busca. Na V2 ele ia para os textos e a página o escondia (quem baixasse os
dados lia do mesmo jeito). Tudo por id, não mais pelo texto. `cuidado.json` fica
vazio, e serve para esconder algo à mão sem regerar.

**Dados.** O ponto ganhou 4 bytes (26 em vez de 22): um bit por classe de carga,
despertar, figura, origem da atribuição e "só mencionado". O campo `bits` ganhou
forma, fala do sonhar, lido/palpite (e por quem), narrado, tem atribuição. A
atribuição por extenso (palavra, origem, postura, quem) está em `dados/lidos.json`
(420 KB). A taxa de acerto está no `meta.json` (`taxas`), copiada da tabela do
relatório v3.5 para o portão e refeita com o v3.6 (aluno/avaliacao_v36.md) para carga, despertar, figura,
conteúdo, atribuição e origem, com a mesma regra de "mostrar" (sim: ≥20 palpites e faixa de Wilson 95% acima de 60%;
aviso: ≥10 palpites; não: abaixo). O `pontos.bin` passou de 15 para 18,5 MB. No total são ~200 MB publicáveis,
como na V2.

**Lido e palpite.** Na ficha:
- **lido**: os rótulos sem número, com "lido · por Opus" ou "por Fitipe" (o Fitipe tem
  precedência; nenhum texto foi lido pelos dois). A atribuição aparece com a palavra da
  pessoa entre aspas, a origem, a postura e quem diz. Clicar na palavra busca quem mais a usou.
- **palpite**: só as classes com "mostrar" sim ou com aviso. Cada uma vem com
  "(acerta N%)", e as com aviso trazem "medida frágil", em outra cor, e a faixa de 95%
  no título. Classe com "não" não aparece.
- **carga combinada** do palpite aparece como "mistura: prazerosa 41% + aflitiva 59%", a
  proporção entre as probabilidades do aluno para as cargas que ele afirma. Vem no bloco
  de texto, só onde há mais de uma (6.561 relatos).
- As etiquetas são clicáveis e ligam o filtro correspondente.

**Filtros novos** (coluna da direita):
- *leitura*: quem leu, carga (em % dos que têm carga), despertar, o texto (narrado, só
  mencionado, fala do sonhar), figura, atribuição · origem e atribuição · quem diz.
- *forma do texto*.

Classes sem taxa para o palpite trazem a marca "só lidos": filtram apenas os lidos. Os
filtros ligados aparecem sob a busca com ×, porque no celular os chips ficam no menu fechado.

**Datas.** A linha do tempo da V2 continua (filtro por período). No celular ela agora mora no
fim do menu, antes não aparecia.

**Placa de vídeo (28/09, manhã).** A V3 tinha sido montada sobre a V2 e ficou só com o
laço do processador: no zoom médio os pontos voltavam a sair quadrados (o Fitipe viu).
O bloco WebGL da V2.5 (disco de borda suave a partir de 2 px, blending aditivo,
véu da busca e máscara de filtros no shader) foi trazido para cá. `?cpu` na URL força o
laço antigo. Conferido no navegador: zoom 1,6 / 6 / 14, busca, filtro e ficha, sem erro.

**Piscar no zoom rápido (bug herdado da V2.5, 28/09).** A luz total de cada ponto tinha
dois degraus no tamanho: em 2 px o disco de borda suave (a borda de 1 px cobria o disco
inteiro) ficava com ~30% da luz do quadrado, e em 3 px o fator 1,27 saía de uma vez. Num
zoom rápido todos os pontos cruzam o degrau no mesmo quadro e a tela toda pisca. Agora o
quadrado escurece aos poucos entre 1 e 2 px e o fator sai entre 2,5 e 4 px; modelado em
Python (luz por ponto ao longo do zoom, DPR 1 e 2): sem quedas. Falta o Fitipe confirmar
no olho. O laço do processador (`?cpu`) ainda tem o degrau em 3 px.

**Explorar por dentro (V2.5) trazido (28/09).** Botão "explorar por dentro" / tecla X,
WASD/QE, olhar com o mouse capturado, controle, A/B lê o sonho na mira, + ou Esc volta.
Perspectiva no shader (`uModo` 1) e no laço do processador. Escondido em tela de toque.
Ao voltar à órbita, o giro só retoma depois da quietude. Testado: entra, anda (por
JavaScript), volta; sem erro. Controle físico e captura do mouse não testados aqui.

**Vínculos (28/09, tarde) — `dados/vinculos.json` (2,9 MB, carregado na primeira ficha).**
Linha "vínculos" na ficha, com etiquetas clicáveis que listam os iguais como uma busca
(pedido do Fitipe de 25/09): **circulação (N)** (grupos_copia tipo circulacao: letra, meme,
corrente que rodou entre contas por meses), **idêntico (N)** (frase comum ou copy-paste entre
contas), **quase idêntico (N)** (ecos fortes entre contas, vizinho a vizinho — sem componente
conexa, que por encadeamento viraria um megagrupo; um relato tem até 388 vizinhos),
**repetido N× pela mesma conta (datas)** (as cópias escondidas por canonico_de; não clicável,
elas não estão no planeta), **responde a um relato do arquivo** (abre o pai) e **N respostas no
arquivo** (lista os filhos). Números: cópias 32.276 em 4.149 grupos · quase idênticos 4.481 ·
repetidos 4.117 · conversa 23.297 respostas / 17.738 pais.
**Duas datas do Bluesky** (tuítes importados na migração do X): 2.034 relatos mostram
"publicado originalmente em … · trazido ao Bluesky em …" (data de criação real decodificada do
rkey/TID da URI). **A linha do tempo deixou de grampear em 2015**: vai de 2008 a 2026, pela
data declarada (decisão do Fitipe: é quando foi sonhado); post do Bluesky sem data no coletor
entra pela data do rkey em vez de 2015/01.

**Legenda do palpite e menu recolhível (28/09, ~17h15).** A caixa "leitura" ganhou uma
legenda fixa, retirada a pedido do Fitipe (28/09, 19h). Na ficha, "palpite · do aluno" traz o
link "o que é palpite?", que abre um parágrafo com as ressalvas (taxas condicionais,
medida frágil nas raras, classe calada quando erra demais); a escolha fica no navegador
(localStorage). No celular, cada grupo do menu recolhe pelo título (+/−), só "o sonho é…"
começa aberto; a linha do tempo, que entra no menu sem título, não recolhe. Filtro ligado
num grupo fechado continua visível nos chips sob a busca. Conferido na emulação 375×812.

**Conteúdo sensível (28/09, ~14h40).** Ver `ids_sensiveis()` em gerar.py e `dados/sensivel.json`:
endosso da vigília a violência sonhada fica na página com etiqueta laranja no cabeçalho da
ficha; risco real continua fora.

**Menu (28/09, noite, pedidos do Fitipe ao mexer na prévia).** A legenda fixa de "leitura" e o
grupo "quem leu" saíram do menu (o filtro por quem leu continua vivo por baixo, para as
etiquetas da ficha). "De onde vem" saiu do fim da coluna para uma coluna própria
(`#fontesCol`), à esquerda de "o sonho é…"; no celular volta para dentro do menu (medir()).
Dentro dela, os r/ ficaram juntos num item "reddit" (clicável: liga/desliga todos; setinha
abre a lista dos r/), e "bluesky" abre em post · comentário · continuação — um filtro de
forma só do Bluesky (`formaBsky`, dentro de `okCom`); os ~500 "não verificados" ficam no
todo. "nenhuma/todas" sincroniza mestres e sub-itens. O giro: o mouse só o segura sobre o
disco do globo; fora dele (ou fora da tela) volta em 1 s (`saiuDosPontos`).

## Navegação (NOTAS-V3, itens 1-5)

1. **Zoom no desktop.** Pronto e testado. A primeira volta da roda fixa o relato sob o
   cursor, ou o ponto no plano em foco se não houver relato ali, em coordenadas do globo.
   As voltas seguintes giram rumo à projeção atual dele. O alvo se solta depois de 6 px
   de mouse ou 700 ms sem roda. No teste, o alvo ficou o mesmo por 14 voltas e convergiu
   ao centro.
2. **Pinça no mobile.** Pronto, mas **não testado num aparelho real**. O body tem
   `touch-action:none`, os painéis que rolam têm `pan-y` (rola, não amplia) e o viewport
   tem `maximum-scale=1, user-scalable=no`. Para o iOS, `gesturestart/change/end` são
   bloqueados. A pinça agora é tratada no documento inteiro: começada sobre a busca, ela
   aproxima o globo. O campo de busca tem 16 px no celular, porque abaixo disso o iOS
   amplia a página ao focar, e é provável que isso também fizesse "os menus crescerem".
3. **Faixas pretas.** Pronto, **não testado em aparelho**. O `medir()` usa o
   `visualViewport` e não mede enquanto a escala está fora de 1: guarda a medida anterior.
   Quando a escala volta, o `visualViewport.resize` pede uma nova medida.
4. **Ficha no mobile.** Pronto e testado na emulação 375×812. A ficha virou uma folha de
   baixo com alça: arrastar para cima abre até 88% da tela, arrastar para baixo fecha, e um
   toque alterna. Com ela aberta a busca some. "← voltar aos resultados" aparece quando a
   ficha veio da busca e devolve a lista.
5. **Giro volta sozinho.** Pronto e testado na lógica do quadro. O giro pára com qualquer
   toque, roda, arrasto, tecla ou mouse andando sobre o globo. Volta depois de 10 s de
   quietude, e nunca com um sonho aberto.

## Pendências

- **Testar 2 e 3 num iPhone e num Android de verdade.** A emulação do navegador não
  reproduz o zoom da página.
- **Confirmar a leitura de "cargas combinadas em porcentagem".** Fiz as duas coisas:
  proporção no palpite ("mistura: …%") e a caixa de carga em % dos que têm carga. Nos
  lidos com carga combinada aparece só "estranha + prazerosa", sem número, porque a leitura
  não tem proporção. Misturar ali a probabilidade do aluno seria pôr palpite dentro do lido.
- **Os 977 marcados só pelo aluno** estão fora por precaução. Ler, ou mandar para a
  conferência de risco, para decidir quais voltam.
- **Legenda da taxa.** O "(acerta N%)" tem as duas ressalvas do relatório (cabeças
  condicionais e população da prova) só no título ao passar o mouse. Talvez mereça uma linha
  visível ("o que é palpite?").
- **Ficaram de fora:** a conversa em torno do post (`vinculos`); `datas_bluesky.json` e
  `duplicatas_exatas.json`, que a página não lia e estão indexados pelas posições da V2; e
  as marcas do Opus (se_cumpriu, de_brincadeira…) e as notas dele, que não publiquei.
- **O menu do celular ficou longo** com a leitura. Talvez recolher os grupos.
- **Antes de publicar**: pôr `planeta-v3/dados/projecao*` no `.gitignore`, trocar o link da
  página inicial e rodar `conferir.py` de novo.

## Fios (28/09 noite)
- **ver fios entre posts e comentários** (abaixo de "de onde vem"): 22.918 pares
  filho→pai de `dados/vinculos.json`, desenhados na placa (`gl.LINES`, segundo
  programa `progL`, mesma rotação/profundidade). Peso pelo comprimento 3D
  (régua = percentil 90): curtos fracos, longos fortes. Com ficha aberta, só a
  conversa dela (sobe até a raiz, desce pelos filhos); na ficha há a etiqueta
  "ver a conversa inteira", que liga o botão.
- **criar linhas** (abaixo da busca): palavras → busca lexical (modo
  todas/qualquer no título; vírgula separa várias constelações de uma vez) →
  cada aceso liga aos 2 acesos mais próximos em 3D (grade espacial, sem
  modelo) ou ao centro médio. Os pontos da constelação acendem na cor dela.
  Clique liga/desliga, × apaga, dois cliques mostra os acesos como busca.
  Refeito quando os filtros mudam.
- Só com WebGL: em `?cpu` as duas caixas somem. No celular, as duas entram no menu.
- Backup de antes: scratchpad da sessão (`index_antes_fios.html`).

## "de onde vem" por tipo + isolar constelações (28/09 noite, 2ª rodada)
- Filtro = comunidade × TIPO (`ON[com*8+tipo]`): posts solo · posts vinculados ·
  comentários solo · comentários vinculados · continuações (threads) · (não
  verificados, ~500, só no todo). Vinculado = tem pai ou filho em
  vinculos.json → vinculos.json agora carrega na abertura (2,9 MB, em paralelo
  com pontos.bin). Bluesky: tipos direto. Reddit: tipo → seus r/.
  Contagens das ~95 chaves numa passada só (histograma por CONTA_VEZ).
- Setas 75% maiores. "criar linhas" → "criar constelações"; botão "isolar"
  por constelação (várias isoladas = união; entra em visivel() como filtro).
  Pontos das constelações 1/3 maiores.
- Backup de antes desta rodada: scratchpad (`index_antes_tipos.html`).

## 3ª rodada (28/09 noite)
- Bug: com os sub-itens do bluesky apagados e o mestre aceso sobravam ~500
  "não verificados" (tipo 5, sem item). Agora o tipo 5 segue os irmãos.
- Tirado "nenhuma/todas". Títulos BUSCAR e CRIAR CONSTELAÇÕES na cor do título.
- Linhas das constelações em faixa (2 triângulos por segmento, largura em px
  no shader, `bufFaixa`, atributos 3-4 aOutro/aLado): largura (zr/1,1)^(2/3)
  → afinam 1/3 do que afinavam em relação aos pontos. Conversa segue gl.LINES.
- Colunas: "o sonho é" › "de onde vem" › botão "classificações" (abre leitura,
  forma, tamanho, camadas; body.classes). Computador < 1020 px: "o sonho é"
  entra na coluna de "de onde vem". Celular: tudo no menu, nessa ordem.
- Explorar: Esc com relato aberto fecha só o relato; o seguinte sai.

## Arranjos por classe (28/09 noite)
- `projetar_classes.py [classes]` → `dados/classe_{literal,figurado,incerto}.bin`
  (só membros, ordem da página, int16 xyz/32767). Mesmo UMAP do
  planeta-v2/projetar.py (3D, cosseno, n_neighbors 15, min_dist 0, 200 épocas,
  raio por posto), init = posição de hoje, depois Procrustes para a de hoje.
  Classe tirada do próprio pontos.bin (bits 0-2, só NAT 0); os 680
  literal+figurado entram nas duas (Fitipe). Página↔id casada pela posição
  exata em projecao.npy (asserts). **Refazer sempre que o gerar.py rodar** —
  se os membros não baterem, a página recusa o arquivo (aviso no console).
- Página: botões todos/literal/figurado/incerto ao lado do título (abaixo
  dele se não couber). Placa com duas posições (aPos/aPara, w = presença) e
  uT suavizado em 1,6 s; fios esperam o fim; no fim POS vira o arranjo
  novo (clique, fios, constelações usam). Em classe: "o sonho é" some,
  camadas ficam fora, okMarc vira pertença à classe. Sem WebGL: salto.
- Régua incerto: 58% na projeção própria vs 55% nas posições de hoje.
- Backup antes: scratchpad (`index_antes_classes.html`).
- Régua literal: 54% própria vs 50% hoje (UMAP 4,8 min).

## Conversa e tecla X (28/09 noite)
- X: com relato aberto fecha o relato; sem relato liga/desliga explorar (o Esc
  é engolido pela trava do mouse).
- "ver a conversa inteira" abre, na mesma ficha, a árvore da conversa (raiz →
  respostas, irmãs em ordem de índice = data; recuo por nível, até 6),
  clique abre o relato; rodapé "← voltar ao post/comentário/à continuação" e
  "isolar" (CONV_ISO entra na união de isolar(); some ao fechar a ficha).
- Régua figurado: 59% própria vs 58% hoje (UMAP 6,1 min).

## 4ª rodada (28/09 noite)
- Transição: presença e cor andam na frente (uF: começa com o movimento,
  termina em 55% do tempo, ease-out); movimento continua suave (uT). O tranco
  do começo era atualizarContas (~100 varreduras): na partida só a máscara;
  as contas vão para depois da chegada (setTimeout). Relógio começa depois
  do trabalho de preparo.
- Arranjo literal: cor = carga. `cargas_literal.py` → `dados/carga_literal.bin`
  (5 × uint8 por literal: prazerosa, aflitiva, estranha, mista, sem afeto;
  aluno v3.6 p_carga; lidos pela leitura). Mistura pesada por p²; legenda
  #cargaLeg só no literal. Estranha/mista têm taxa baixa (57%/33%): tendência.
  Refazer junto com projetar_classes.py a cada gerar.py.
- "de onde vem" atrás do botão "origens" (nasce fechado); fios fora dele.
- Ficha: botão − (minimizar) à esquerda do ×.

## Classes "só lidos" ocultas (28/09 noite, temporário)
`OCULTAR_SO_LIDOS = true`: fora do menu (e grupo "quem diz"), das cores e
legenda da carga (estranha, mista). Voltam só quando o pipeline (BERT,
moinhos, rubricas, pesos) estiver validado e as classes tiverem taxa.
- Literal: grupo "carga" some da Leitura; os itens da legenda "carga do sonho"
  são os chips dela (clique liga/desliga, % espelhada). Figurado e incerto:
  carga, despertar e atribuição somem da Leitura e são desligados ao entrar
  (GRUPOS_FORA), para não apagarem o planeta escondidos.

## Fita de Möbius (28/09 noite)
- `mobius.py` → `dados/mobius_{todos,literal,figurado,incerto}.bin` (+ mapas
  2D intermediários `dados/umap2d_*.npy`, no .gitignore). Pele da fita
  engrossada: u de 0 a 4π percorre as duas faces (são uma só). todos =
  literal numa face, figurado na outra, incerto na alma (d = 0); a passagem
  literal↔figurado fica onde uma face termina e a outra começa. Classe = pele
  inteira. (u, v) = UMAP 2D por classe, eixo maior ao longo, posto por eixo.
  Camadas fora da fita. R 0,62 · meia largura 0,34 · meia espessura 0,045.
- Página: arranjo = FORMA × CLASSE (mudarArranjo); botões globo/möbius sob
  "todos". Refazer mobius.py a cada gerar.py.
- Régua incerto: fita 46% · mapa 2D 51% · bola 58%.
- Régua literal: fita 43% · 2D 48% · bola 54%. Figurado: fita 52% · 2D 54% · bola 59%. UMAP 2D: literal 2,4 min, figurado 3,1 min.

## Fita, 2ª rodada (28/09 noite)
- Botão único "globo ⇄ / möbius ⇄" (#formaBtn).
- Abre de frente (MAT_FITA = rotX(−0,38), girarAte pelo caminho curto); de
  longe o giro automático corre a fita em torno do próprio eixo.
- Bordas: campos SUAVES (senos de baixa frequência, periódicos em 4π) na
  largura e na espessura + focos (10% mais densos do mapa 2D saltam até
  0,11 da face) + fiapo mínimo. Ruído ponto a ponto custou ~10 pontos de
  régua e foi trocado. Régua agora: incerto 46% · literal 41% · figurado 51%.
- Zoom na fita = zoom de mapa (PAN em raios, uniforme uPan nos dois
  programas, proj/telaDoAlvo/fixarAlvo): o alvo fica sob o cursor. Foco de
  repouso da fita = 0 (plano dela), não +1 — antes, no zoom a fita toda ficava
  cinza e inclicável. Brilho × 0,55 (FORMA_K). Clique em zoom ≥ 1,5 centraliza
  pelo PAN em vez de girar. Sem WebGL (?cpu) o PAN não vale; explorar ignora PAN.
- Testado: zoom 14,7× na fita, 9.543/9.543 pontos na tela clicáveis.
- 3ª versão das bordas (Fitipe: "espinhos"): focos empurrados pela normal
  viravam colunas. Agora dispersão gaussiana 3D, maior na borda (poeira) e
  nos 10% mais densos (nuvem). Régua: incerto 40% · literal 38% · figurado 47%
  (custou 3-6 pontos frente à versão com espinhos). Versão anterior do script
  no scratchpad (mobius_espinhos.py). Aviso "dentro · no centro" não aparece
  na fita.
- 4ª versão (Fitipe: "só difuso; queria os caminhos/fios entre aglomerados
  do globo"): a fita agora é a BOLA de cada classe (classe_*.bin) deformada —
  x por posto vira o comprimento, cada fatia redonda vira a seção (y, z
  divididos pelo raio da fatia → largura × espessura). Contínua: aglomerados
  e fios vêm junto, esticados ao longo da fita. Sem poeira/nuvem. Camadas:
  face a 0,065 ± 0,05; incerto na alma ± 0,02. Régua: incerto 47% · literal
  42% · figurado 49%. **Depende de classe_*.bin: rodar projetar_classes.py
  antes de mobius.py.** Testado e descartado: UMAP 3D com início em laje
  comprida (o UMAP desfaz a proporção, sai ~1:1:1,3). Versões anteriores no
  scratchpad (mobius_espinhos.py, mobius_difuso.py).
- 5ª versão: camadas encostam no meio (FACE = ESP) — o vão entre elas era a
  "fenda" vista onde a fita fica de perfil. Régua: 46% · 41% · 49%.
- RIO: mobius_*.bin agora guarda (u, v, d) NA FITA (u uint16 sobre 4π, v/W e
  d/0,2 int16) + mobius_meta.json {R, W, D_ESC}; a página calcula xyz
  (peleFita, igual no shader e no JS). O shader faz u + uFase: os pontos
  correm ao longo da fita e, como u vai a 4π, passam de uma face à outra.
  Corre quando a página está quieta 2,5 s e sem relato aberto; ao parar,
  POS é sincronizado (sincronizarRio) e fios/constelações voltam. Botão
  "rio ▸ / rio ❚❚" ao lado de "möbius". Volta inteira (4π) em 4 min.
- 6ª versão (Fitipe: "vácuo no meio da torção"; "o rio parece só girar"):
  seção disco → quadrado (grade elíptica) — cada camada enche a largura, as
  duas se encostam em toda ela (antes, elipses que só se tocavam no meio).
  Rio com correnteza: u = u0 + fase + 0,9·s·sin(fase/2), s = 0,8·(1 − 2(v/W)²)
  + pitada por ponto (aFita.w). O meio adianta, as bordas atrasam; o desvio
  fecha na volta inteira (3 min), então o arranjo se refaz a cada ciclo.
  Medido: em ~9 s, distância entre pares muda mediana 0,043 (giro rígido = 0).
- 7ª versão: emenda mascarada — cada face passa SOBRA = 0,3 rad da emenda
  (as pontas das bolas se sobrepõem e se entremeiam). Régua 45% · 42% · 48%.
  Rio começa parado; botão "rio" só na fita, embaixo da chave; chave única
  "globo | möbius" com as duas palavras (a acesa é a forma atual).
- 8ª versão: o "vácuo" que restava era a ALMA rala (a grade elíptica deixa
  a borda do quadrado com menos pontos, e essa borda é o meio da espessura,
  onde as camadas se encostam; de perfil, na torção, lia-se como vão).
  Espessura por posto + camadas interpenetrando (FACE = 0,8·ESP). Medido
  antes: nenhuma falha ao longo da fita em fatias de 0,05° (não era a emenda).
  Régua 44% · 41% · 48%.
- Zoom na fita pelo CENTRO (sem PAN; o zoom de mapa foi desfeito a pedido do
  Fitipe — ao arrastar/afastar a fita não voltava ao centro). Na fita
  fatia/alcance = 9: sem cinza de profundidade, tudo clicável; o clique
  prefere o que está à frente.
- 9ª versão (Fitipe: "por que continua a faixa de vácuo?"): mapa de densidade
  volta × largura por face mostrou VAZIOS DO DADO — setores de uma fatia da
  bola sem relatos (vãos entre aglomerados), que no globo ficam escondidos
  atrás de outras camadas e na fita fina ficam expostos; ao longo da fita o
  vão desliza e vira faixa oblíqua. enche_largura(): CDF local da largura por
  trecho (interpolada entre trechos, sem cortes), misturada 70/30 com a
  posição original. Células < 30% da mediana: 291 → 60 (face +), 653 → 147
  (face −), o resto quase todo nas bordas. Régua 43% · 39% · 45%.
  Na emenda aparecem raios finos (pontas das bolas entremeadas).
- 10ª/11ª versões (Fitipe: "tire os raios da emenda; bordas demarcadas"):
  * raios = (a) sobreposição SOBRA dobrava a densidade na emenda (2,5×) →
    SOBRA = 0, as pontas se entremeiam por dispersão em u (PONTA 6%, até
    0,35 rad); (b) polos ocos: dividir pelo raio da fatia levava a casca da
    bola (quase tudo perto dos polos) para a beira da seção → seção agora
    por ordem local de y e z por trecho (enche_largura), sem divisão.
  * borda: largura ondula (campo suave, 10%) e a beira (|v| > 0,8) vaza na
    própria largura com cauda exponencial (VAZA_V 0,12); espessura idem.
    Arquivo guarda v/(2W) (mobius_meta.W = 2W). Na beira do furo o vazamento
    aparece como fiapos curtos.
  * Régua: incerto 41% · literal 38% · figurado 43%.
  Versões anteriores do script: scratchpad (mobius_v4, _v9, _difuso, _espinhos).
- 12ª versão (Fitipe: "o vazamento voltou a fazer espinhos; use o que veio
  depois deles"): a borda volta à POEIRA da 3ª versão — gaussiana isotrópica
  no referencial local (ao longo, largura, espessura), desvio 0,045·|v|⁴ —
  sobre a fita da bola (11ª). Ondulação lenta da largura mantida (10%).
  Régua: incerto 38% · literal 35% · figurado 40%.
  LIÇÃO: na fita, deslocamento numa direção só (normal na 2ª, largura na 10ª)
  sempre vira espinho/fiapo; o que desfia sem espinho é o isotrópico.
- 13ª versão (Fitipe: "como no geóide — caminhos que saem e entram; anéis
  que conversam e vazam um no outro"): vazamento DO DADO. Relatos com raio
  da bola > R_FIO = 0,88 (os mais externos, que no globo formam os fios que
  vazam) têm a seção (v, t) esticada até 1 + FIO·k² (FIO 0,9) na direção que
  já têm: vazam para fora da largura, para fora da face ou atravessam o miolo
  para a outra camada. Vizinhos de um fio vão para o mesmo lado (caminhos,
  não espinhos). Poeira isotrópica reduzida a 0,015 (só fiapo). Medido:
  ~13% dos literais (26.398) e figurados (32.847) cruzam para a camada do
  outro; 33.793 além da largura; 47 no teto do arquivo. Régua 42% · 38% · 43%
  (melhor que a poeira pura, 38/35/40).
- 14ª versão (Fitipe: "ainda um pouco difuso"): poeira 0,015 → 0,004;
  redistribuição local da largura 0,7 → 0,5 e da espessura 1,0 → 0,75 (ela
  uniformiza a densidade e apaga o contraste aglomerado/vão). Régua 42% ·
  39% · 45%. Abertura da fita: MAT_FITA = rotX(−(π/2 − 0,32))·rotZ(π/2) —
  anel na horizontal, visto ~18° de cima, torção (u = π) de frente.
- Rio: não pára mais com mouse/arrasto/zoom; só com relato aberto. Ao fechar
  o relato, volta depois de 5 s (RIO.retomaEm). Giro da fita com rio
  desligado mantido.
- "ver fios entre posts e comentários" agora fica dentro de "origens" (escondido com ele).
