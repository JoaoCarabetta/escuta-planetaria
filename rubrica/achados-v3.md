# O que a rubrica v3 não cobre — 519 relatos, seis anotadores

Cinco agentes anotaram fatias disjuntas (97+94+97+101+90) sem se ver, além das
40 que fiz à mão. Cada um recebeu a mesma instrução final: dizer o que a rubrica
não comporta. O que segue é o cruzamento. A coluna **n** é em quantos dos cinco
relatórios independentes o achado apareceu — não é opinião repetida, é o mesmo
buraco encontrado cinco vezes por leitores cegos entre si.

## Convergência forte (4 ou 5 de 5)

| n | achado | o que fazer |
|---|--------|-------------|
| 5 | **`nao_lembra` mistura amnésia total com esquecimento de um detalhe.** "não lembro do rosto, só uns cachinhos loiros" ≠ "não lembro de nada". A parcial é a esmagadora maioria. | separar `nao_lembra_parcial`; guardar **sobre o quê** caiu o esquecimento quando o texto diz (a fala, o rosto, quem eu era) |
| 5 | **"de novo" não quer dizer sonho recorrente.** Em ~40% dos casos pescados pela bolsa, o "de novo" é interno à cena ("sonhei que tava trabalhando de novo"). Quem treinar sobre as bolsas sem ler infla `recorrente`. | é defeito da pesca, não da rubrica — mas obriga a regra explícita: `recorrente` exige que **o sonho** se repita |
| 5 | **Falta rótulo para a morte DENTRO do sonho.** A rubrica só diz o que isso *não* é (não é `morto`, que é visita de quem já morreu). Sem rótulo, o mais frequente dos conteúdos aflitivos fica invisível. | `morte_no_sonho` em presenças. Par de calibração: "sonhei com meu pai, ele morreu tem 8 anos" (morto) × "sonhei que meu pai morreu" (morte no sonho) |
| 5 | **`atribuicao` só tem o polo positivo.** Aparecem, distintas: negar ("não sou adepto de significados"), pedir ("se alguém aí manja de sonhos"), temer ("que isso não seja premonição"), brincar ("foi premonição 😂"), e explicar a causa em vez do sentido ("sonhei com a palavra INSONE porque li um poema"). A recusa de significado é tão informativa quanto a crença e hoje vira campo vazio. | `atribuicao` vira {espécie × força}: espécie = `significa` · `aviso` · `premonicao` · `residuo_diurno` · `nega` · `pede_interpretacao`; força = `afirma` · `cogita` · `jocoso` |
| 4 | **Sonho retomado ou fragmentado na mesma noite ≠ recorrente.** "voltei a dormir e sonhei de novo (mesma coisa do lobisomem)"; "sonhava com o chico, acordava, depois com o ramiro". | modos `retomado` e `fragmentado` |
| 4 | **Presenças que faltam e são frequentes**: `figura_publica` (o povoador mais comum — ídolos de k-pop, Lula, Virgínia), `animal`, `religioso`/`entidade`, `personagem_ficcional`, `ex_parceiro`, `trabalho`, `escola_prova`, `perseguicao`, `desconhecido`. | promover as quatro primeiras a canônicas |
| 4 | **Sonhador ≠ autor.** "minha muiee: 'sonhei que você tava me traindo'"; "uma aluna sonhou". Marcar `literal=1` joga no mesmo balde o arquivo de sonhos próprios e o de sonhos ouvidos. | campo `sonhador`: `proprio` · `terceiro` |
| 4 | **Texto que é obra, não relato**: letra de música, verso, sinopse, título, análise de filme, piada construída em forma de diálogo. Virou `descartavel` a contragosto — e a canção é justamente onde o figurado já circula formado. | valor de portão `citacao` e `ficcional` (o pesadelo de um personagem) |
| 4 | **Violência e sexo somem no figurado.** A regra "presenças só valem para literal" apaga o conteúdo do corpus figurado, que é o maior do arquivo (~23 mil entre desejo e intensificador): maldições jocosas, fantasias sexuais explícitas, "meu sonho é encontrar o Elon [...] até cair mortinho no chão". | passagem barata de presenças também no figurado |
| 4 | **`desejo` é uma caixa só para coisas incomparáveis**: projeto de vida × capricho de cinco minutos; desejo irônico ("tudo que eu sempre sonhei (mais um ano chorando)"); desejo já realizado; desejo-luto ("a vida que eu sonhei morreu durante o regime bolsonaro"); desejo de terceiros; desejo-opinião. | qualificar `desejo` com `estado` (pendente · realizado · perdido) e `peso` (projeto · capricho), e marcar `ironia` |

## Convergência média (2 ou 3 de 5)

- **A carga é extra-diegética com frequência.** "Sonhei com ele de novo. Não aguento mais, esses sonhos viraram tortura": a aflição está na repetição e no despertar, não na cena. E o inverso: apocalipse zumbi vivido com tédio ("peguei uma arma e entrei de boa"). → terceiro campo `despertar` (alívio · decepção · ansiedade · dor · indiferente) e valor `nao_dito` na carga.
- **"Literal vazio":** afirma o sonho e não conta nada dele ("tive um pesadelo em plena madrugada"). Força `carga: neutra` e polui a estatística de valência — em uma leva, 26 de 49 literais ficaram neutros, boa parte por isso. → `sem_conteudo=1`.
- **"o falecido" = Twitter.** A bolsa `morto` pesca luto de plataforma em 5 casos. Ruído de pesca.
- **Premonição implícita pela justaposição**, sem ninguém nomear: "O ex-Ministro morreu. Há menos de 2 meses sonhei com ele e fiquei '?????'".
- **Efeito do sonho na vigília**, que não é atribuição de sentido: "agora estou pensando em realmente ir"; "acordei procurando o post pra deletar"; a criatura que "saiu de um pesadelo meu" e virou desenho; Zé Pelintra que "se apresentou em sonho" e daí decorre um vínculo religioso de anos — aí o sonho é credencial, não relato.
- **Homônimo ≠ figura de linguagem.** "Comi um sonho" (o doce). Hoje cai em `nome_expressao`; é ruído lexical.
- **Um texto, vários sonhos.** Carga, modo e presenças se aplicam a coisas diferentes dentro do mesmo registro.

## Achado único, mas que vale

- **`lucido` provavelmente vai colecionar falso positivo**: "sonhos mt lúcidos, como se eu estivesse vivendo" quer dizer *vívido*, não lucidez. Merece o mesmo aviso que o falso despertar recebeu.
- **Realidade-como-pesadelo**: "só queria acordar e perceber que 2020-2021 foi só um pesadelo". Não é intensificação — é o desejo de que o real seja onírico. É o avesso exato do erro que a v3 corrige.
- **Figurado dentro do sonho**: "Sonhei que o Twitter voltava e tudo tinha sido um pesadelo!!!! Daí acordei."
- **Sonho fabricado**: "não sonhei com vc, mas falei que sonhei pra puxar assunto". O sonho como moeda social.
- **Hipnagógico**: "quaase dormindo mas ainda n dormi, eu acordada e o pesadelo continuando". Nem devaneio, nem sonho pleno, nem paralisia.
- **Sonho aninhado**: "sonhei que eu lia um tweet seu contando que sua psicóloga sonhou que você tava grávida".
- **Descobrir dentro do sonho que o morto está morto** — e o sonho acabar por isso. Não é lucidez nem falso despertar.
- **Consulta interpretativa**: textos escritos para serem decifrados por outros, com descrição iconográfica precisa. Têm destinatário, e isso muda o que são.
- **Risco.** "meu sonho é morrer antes dos 23 (tenho 22 😁"; "sem sonhos, não tenho forças pra continuar". Nenhum campo os sinaliza. É decisão ética, não taxonômica.

## Duas coisas que a v3 acertou, medidas

O portão funcionou nas duas direções. A bolsa `suspeito` deu 9/9 figurado e a
bolsa `desejo` 10/10 — o qwen lia todos como sonho dormido. Na direção inversa,
a bolsa `intensificador` entregou literais genuínos em três levas: "tive um
pesadelo" é literal com a mesma frequência com que "que pesadelo" é figurado.
A armadilha mais fina é `sonhei com` + realização ("sempre sonhei com meus
amigos me servindo e hoje esse sonho se realizou"): a preposição "com" quase
sempre marca o onírico, e ali não marca.

E a separação carga × tom se provou: **o riso é o registro padrão do corpus**,
inclusive sobre conteúdo pesado. Numa leva, tom leve 50 contra carga aflitiva
15. Quem colapsar os dois num campo só de "sentimento" perde exatamente isso.
