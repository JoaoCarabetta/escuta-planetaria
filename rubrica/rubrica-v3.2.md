# Rubrica v3.2 — com o núcleo duro separado da camada aberta

*Fitipe + Claude, 2026-09-24. Sete anotadores releram 471 relatos com a v3.1 e
disseram, cada um sem ver os outros, o que ela não comportava. Esta versão é
mais de correção do que de acréscimo: a maior parte do que chegou era campo que
já existia e estava mal definido.*

## O que a v3.1 provou, medido nos mesmos textos

**96% dos julgamentos do núcleo (literal/figurado/devaneio) ficaram idênticos aos
da v3.** A rubrica nova não desmontou a antiga, acrescentou onde faltava.

**Os descartes caíram de 11 para 1 em 471.** A exigência de justificativa escrita
— decisão do Fitipe — recuperou dez textos, sete dos quais eram uso figurado
jogado fora por não ter onde entrar. Escalado para o arquivo, são uns 3.700.

**`meta` passou de 10 para 59 usos** ao sair do portão e virar marca. Não é
mudança de opinião: antes não dava para dizer "isto conta um sonho **e** fala
sobre sonhar".

---

## NÚCLEO DURO — o que o classificador aprende

Poucos campos, cada um com exemplos suficientes para treinar. É aqui que a
precisão importa e é isto que vai rodar nos 174 mil.

### 1. Portão — o que o texto é (combinável)

| valor | o que é |
|---|---|
| `literal` | a pessoa dormiu e sonhou |
| `figurado` | "sonho"/"pesadelo" fora do sentido onírico |
| `devaneio` | acordada, imagina, divaga, projeta |
| `fala_do_sonhar` | o assunto é o sonhar — prática, crença, hábito — e nenhum sonho é contado |
| `obra` | o texto **é** obra: verso, letra, cena, sinopse |
| `noticia` | jornalismo: reporta um fato, não conta experiência |
| `propaganda` | anúncio de produto, serviço, show |
| `descartavel` | nada sobre sonho — **exige justificativa escrita** |

`literal` não exige que o texto diga "dormi": reconhece-se pela impossibilidade
da cena, pelo tempo verbal, pela ausência de intenção, pelo despertar
mencionado. Inclui a ausência — "não sonhei" é literal sem conteúdo.

**`fala_do_sonhar` é novo e fecha um buraco que a v3.1 abriu.** Ao tirar `meta`
do portão (decisão certa), sobraram textos sem destino nenhum: *"Toda vez que a
Laine sonha ou eu falo que sonhei, ela vai em site de sonhos ver o que
significa"*. Três anotadores gravaram portão vazio por isso.

*Regra que faltava: **texto sobre obra não é obra.** Uma resenha de Dostoiévski
julga-se pelo que ela faz — quase sempre `fala_do_sonhar` ou `figurado` — e o
fato de discutir uma obra vai na nota.*

### 2. Quem sonhou — `sonhador`

`proprio` · `terceiro` · `citado`

**Cinco anotadores pediram, separadamente.** Sem este campo, *"minha namorada
ainda tem pesadelos com isso"* e *"uma aluna teve sonhos sucessivos"* entram como
relato em primeira pessoa, e o classificador aprende sonho alheio como sonho
próprio. Pior: quando o sonhador é outro, **a carga é de quem sonhou e o tom é de
quem conta** — sem saber quem é quem, os dois eixos ficam ambíguos.

### 3. Carga — só sob `literal`

`prazerosa` · `neutra` · `aflitiva` · `mista` · `sem_afeto_dito` · `sem_conteudo`

**Carga deixa de existir fora do literal.** Três anotadores apontaram: no
figurado não há "dentro do sonho", e marcar `nao_dito` ali afirma que houve um
sonho cujo conteúdo não foi contado — mentira diferente da que a regra queria
evitar. Um deles mediu: 32 dos 66 `nao_dito` dele eram figurados. Mantido assim,
o classificador aprenderia `nao_dito` como o valor padrão do figurado.

**E o antigo `nao_dito` se parte em dois**, porque juntava coisas incompatíveis:
- `sem_conteudo` — o texto não diz o que aconteceu ("sonhei com ele de novo vsf")
- `sem_afeto_dito` — diz **o que** aconteceu e não diz **como foi**: *"sonhei com
  um puteiro, sonhei com um tipo de round 6, sonhei com mto sexo e perseguição"*

Sem essa divisão, `nao_dito` vira o valor-lixo do eixo — foi 52 de 90 num lote —
e perde o poder que a regra do Fitipe quis lhe dar. **Nunca inferir afeto que o
texto não dá.**

### 4. Tom — como se conta

`leve` · `ironico` · `lamento` · `aflito` · `confidencia` · `indignado` ·
`hesitante` · `grave` · `seco`

`confidencia` é o desabafo exposto, nem queixa nem ironia — *"Se eu pudesse,
colocaria a cena desse sonho em um quadro"*. Três anotadores pediram com caso
concreto; ficava forçado em `seco`, que apaga exatamente o que o texto tem.

`indignado` separa a revolta do `lamento`, que soa passivo demais.

`aflito` cobre o ansioso. `leve` não exige graça. *(regras do Fitipe)*

### 5. A regra da ironia, reescrita

A versão da v3.1 — conteúdo ruim **e** sinal de leveza — errava nas duas
direções, e os anotadores mostraram como.

**Marque `ironico` quando houver distância entre o dito e o querido, evidenciada
por pelo menos um destes:**

1. **conteúdo que o texto marca como ruim, mais um sinal de leveza que incida
   sobre o conteúdo** — não sobre a conversa;
2. **anticlímax**: uma expectativa armada e esvaziada. *«vc vai ter sonhos
   premonitórios» — Hoje sonhei que escorreguei num tapete.* Nada ali é ruim, e
   é ironia pura;
3. **marcador explícito**: "sqn", "aham", citar a fala de outro para derrubá-la.

**"kkk" sozinho não é sinal.** É amaciador padrão de conversa brasileira: *"É bem
sinistro kkk"* satisfaz a letra da regra antiga e não é ironia nenhuma. Como
`leve` foi o tom mais frequente em quase todos os lotes, esse falso positivo se
repetiria muito.

**E continua valendo, acima de tudo: nunca marque ironia porque o desejo parece
inconcebível.** Isso é limite de quem lê, não propriedade do texto. A regra
protegeu bem essa ponta — nenhum falso positivo em sete lotes — e é ela que
mantém a fantasia transgressiva sincera lida como sincera.

### 6. Confiança — obrigatória

`alta` · `media` · `duvida`, com nota livre. Está calibrada e isso é medido: nos
70 julgados às cegas pelo Fitipe, concordamos em 94% do que marquei `alta`, 100%
do `media` e 52% das dúvidas.

---

## CAMADA ABERTA — registrada, buscável, não treinada

Aqui a cobertura importa mais que a precisão. Estes campos existem para que o
caso raro continue achável no arquivo sem envenenar o classificador com classes
de três exemplos.

### Recorrência — `repeticao` (só literal)

A v3.1 tinha um `recorrente` só, e **todos os sete anotadores** relataram estar
empilhando fenômenos distintos nele. Um mediu: metade dos recorrentes dele era
outra coisa.

| valor | o que se repete |
|---|---|
| `sonho_recorrente` | o mesmo sonho, em noites diferentes |
| `figura_recorrente` | a mesma pessoa ou coisa, em sonhos diferentes |
| `tema_recorrente` | o mesmo assunto, cenas diferentes |
| `repetido_na_noite` | o mesmo sonho, na mesma noite |
| `retomado` | continua de onde parou, depois de acordar |
| `fragmentado` | sonhos diferentes numa noite entrecortada |

**A regra prática, que nenhuma versão anterior escrevia:** o desempate está na
**posição do "de novo"**. Colado ao ato de sonhar — *"sonhei com ele de novo"* —
é repetição. Colado à cena — *"sonhei que tava trabalhando de novo"* — não é.
É exatamente onde cinco anotadores erraram na primeira rodada.

### Modo — `modo` (só literal)

`lucido` · `paralisia_do_sono` · `falso_despertar` · `hipnagogico` ·
`memoria_revivida`

**Eixo separado de `repeticao`**, e a distinção não é cosmética: `repeticao` diz
o que se repete, `modo` diz o fenômeno do sonhar. Um sonho pode ter os dois.
*(Ao criar `repeticao`, a primeira escrita desta versão dissolveu o `modo` e
deixou estes quatro valores sem casa — um anotador achou o buraco no primeiro
falso despertar que encontrou.)*

`lucido` é lucidez, não vivacidade: "sonho muito lúcido" quase sempre quer dizer
vívido.

### Memória — `memoria` (só literal)

`esqueceu_um_pedaco` (a esmagadora maioria) · `nao_lembra_nada` ·
`nao_sabe_se_sonhou` · `nao_sonhou` · `lembrou_depois`

`nao_sonhou` é afirmação, não falha de memória: *"dormi tanto q chega nem
sonhei"*. Dois anotadores deixaram o campo vazio para não mentir.
`lembrou_depois` é o inverso dos outros — *"agora que eu lembrei que eu sonhei"*.

### Despertar — `despertar` (só literal)

`alivio` · `decepcao` · `acordou_mal` · `sem_saber_se_foi_real`

**Foi o melhor acréscimo da v3.1**, por unanimidade dos que o usaram: raro (39 em
471) e, em quase toda aparição, o único lugar onde o afeto cabia. Sem ele, o
sonho bom cuja perda dói viraria "carga mista" e falsificaria o sonho.

### Presenças — `presencas`, **para o portão inteiro**

`morto` · `morte_no_sonho` · `figura_publica` · `animal` · `religioso` ·
`personagem_ficcional` · `pessoa_inexistente` · `parceiro` · `ex_parceiro` ·
`familiar` · `sexo` · `violencia` · `trabalho` · `escola` · `perseguicao` ·
lista aberta.

**Correção de uma contradição minha**, apontada por quatro anotadores: a v3.1
dizia que os grupos valiam "só para o literal" e, três parágrafos antes, pedia
uma passagem pelos figurados para não perder as fantasias e as maldições. Dois
usaram presenças em figurado assim mesmo; um preferiu perder o dado. **Vale para
tudo** — o corpus figurado é o maior do arquivo e sem isso sai sem conteúdo
nenhum.

`morto` é visita de quem já morreu, e **vale para bicho** (será frequente).
`morte_no_sonho` é alguém morrendo lá dentro.

### Atribuição — `atribuicao`, como tripla

Cada atribuição é `{especie, forca, fonte}`, não um rótulo solto.

- **espécie**: `significa` · `aviso` · `premonicao` · `residuo_diurno` · `nega` ·
  `pede_interpretacao` · `recusa_a_pratica`
- **força**: `afirma` · `cogita` · `jocoso`
- **fonte**: `propria` · `familiar` · `internet` · `religiosa`

Um anotador mostrou por que a lista chapada não serve: *"Vai procurar sentido
kkkkkk. Ps. Qnd é aviso eu sei."* nega jocosamente para aqueles sonhos **e**
afirma a crença no geral — e não havia como dizer qual força ia com qual
espécie. A `fonte` separa *"minha mãe sempre diz que significa morte"* de uma
crença própria.

`recusa_a_pratica` é novo e não é `nega`: recusar anotar sonhos é diferente de
recusar que sonhos signifiquem.

### O estado do desejo — `desejo_estado` (só figurado/desejo)

`pendente` · `realizado` · `perdido`

Quatro anotadores chamaram de a maior perda do lote figurado, que é o maior bolo
do arquivo. *"Era o meu sonho, talvez em outra vida"*, *"esse drone foi a
realização de um sonho"* e *"meu sonho é ir num show"* entram hoje como o mesmo
`desejo` raso. O tom não salva: um desejo realizado e feliz fica codificado igual
a um pendente.

### Marcas

`meta` — conta um sonho **e** fala sobre o sonhar. Vale também no figurado.

`suspeita_circulacao` — o anotador reconhece letra, meme ou copypasta. **A
confirmação é da máquina** (`copias.py`), que classifica por comprimento × tempo.
*A v3.1 pedia `copy_paste` no formulário e proibia o anotador de chutar: deu 2
usos em 471. Um anotador reconheceu letra de rap citada sem aspas e não pôde
marcar. Agora ele levanta a suspeita e a máquina decide.*

`bandeira` — ver o critério abaixo.

### Falta de contexto — três marcas, não uma

`falta_imagem` · `falta_fio` · `texto_truncado`

Um anotador usou a marca única em 24 de 90 e **desconfiou do próprio número, pela
razão exata que nos fez cortar o eixo "a quem o texto fala"**: o campo está
sempre disponível e qualquer dêixis o dispara.

Aperto da definição: **marque só quando o texto não puder ser julgado sem o que
falta**, não quando houver um "isso daí" solto. E `texto_truncado` é outra coisa
que as duas primeiras — é defeito da **coleta**, não do arquivo: *"sonhei sobre
."* chegou mutilado ao banco, e isso precisa ser contável em separado.

### O critério da bandeira, que faltava

Três anotadores pediram a regra por escrito, e cada um arbitrou de um jeito.

**Levante quando:**
- o texto expressa desejo de dano a **pessoa real e identificável**;
- ou sinaliza risco a quem escreve — ideação, automutilação, sofrimento agudo
  declarado.

**Não levante quando:**
- alguém morre **dentro do sonho** (relatar sonho de morte não é ódio, e a marca
  perde poder de discriminação se subir aí);
- o alvo é personagem de ficção ou jogo;
- é praga jocosa sem alvo real nomeado.

Na dúvida, levante com `confianca: duvida`. **A bandeira não classifica nada** —
ela reserva o caso para decisão humana posterior, e essa decisão (excluir do
planeta público, manter sem exibir, ou só contar) ainda é do Fitipe.

---

## O que segue proposto e não entrou

`conteudo_sem_afeto` foi absorvido em `sem_afeto_dito`. Ficaram de fora, com
caso concreto registrado mas sem volume que justifique classe:

- tom **celebratório** — *"sou mais do que sonhei um dia ser"*, dez anos de
  transição hormonal. Nem leve, nem confidência.
- **consciência dentro do sonho que não é lucidez** — *"me dei conta no sonho de
  que meu pai morreu, e aí ele parou de falar"*.
- **sonho que revive cena real** sem distorção.
- **homônimo** ("comi um sonho", o doce), hoje forçado em `nome_expressao`.
- **voto formular** — "bons sonhos", "que realizem seus sonhos". Provavelmente
  volumoso; vale medir na amostra-prova antes de decidir.
- **sonho aninhado** — sonho dentro de sonho, dois ou três níveis.

Estes vão para a nota livre. Se a amostra-prova mostrar volume, sobem ao núcleo.
