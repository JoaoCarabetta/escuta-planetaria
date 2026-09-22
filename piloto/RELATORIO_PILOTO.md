# Escuta Planetária — Relatório do Piloto de Triagem

**Data:** 2026-09-17 · **Triagem:** Claude (manual, camada 3) · **Candidatos:** 491

## Setup

Coleta via **Arctic Shift** (API pública de arquivo do Reddit — validou de quebra a via do backfill: busca por data em 2015 funcionou). Seis lotes, embaralhados, anonimizados (IDs → hash, sem usernames):

| Lote | Fonte | N |
|---|---|---|
| dreams_recent | r/Dreams recentes (EN) | 98 |
| dreams_2015 | r/Dreams dez/2015 (EN, histórico) | 88 |
| lucid | r/LucidDreaming recentes (EN) | 56 |
| r_sonhos | r/sonhos 2017-2018 (PT) | 98 |
| desabafos_sonhei | r/desabafos com "sonhei" (PT) | 99 |
| desabafos_meusonho | r/desabafos com "meu sonho" (PT) | 52 |

**Bluesky:** bloqueado nesta rede (CDN devolve 403 ao curl). Pendência: testar via Jetstream (websocket, host diferente) — é o caminho do coletor diário de qualquer forma.

Arquivos: `piloto_candidatos.jsonl` (candidatos), `vereditos.txt` + `triagem.csv` (julgamentos), `raw/` (respostas brutas).

## Distribuição

| Cat | Categoria | N | % |
|---|---|---|---|
| 1 | Relato onírico | 178 | 36,3% |
| 2 | Desejo/aspiração | 51 | 10,4% |
| 3 | Pesadelo/angústia | 105 | 21,4% |
| 4 | Idiomático/vazio | 15 | 3,1% |
| 5 | Ruído comercial/spam | 102 | 20,8% |
| 6 | Indecidível | 5 | 1,0% |
| 7 | **Meta-discussão** (nova) | 35 | 7,1% |

Rendimento útil (1+2+3): **68%** — alto, porque as fontes já são dirigidas. Por lote, o retrato muda tudo:

- **r/sonhos (PT): 96% spam.** Quase todo o subreddit é fazenda de SEO de "dicionário de sonhos" ("Sonhar com cobra, o que significa | Significado dos Sonhos"). Inclui "Sonhar com bitcoin" (2017) — o dicionário comercial absorve o zeitgeist.
- **r/desabafos: a melhor fonte PT.** "sonhei" e "meu sonho" trazem mistura rica: 50 desejos, 69 angústias, 22 relatos oníricos. É onde o sonho-desejo brasileiro mora.
- **r/Dreams: ~65-70% relato onírico puro**, EN e multilíngue de fato (apareceram posts em russo e espanhol).
- **r/LucidDreaming: 37% meta-discussão** (técnicas, suplementos, apps) — daí a categoria nova.

## Descobertas estruturais (mudam a rubrica/pipeline)

1. **Categoria 7 — Meta-discussão sobre sonhar** é necessária: técnica de sonho lúcido, "como faço para...", apps, suplementos, perguntas filosóficas. Não é relato nem ruído; 7% do material. Proposta: manter no arquivo com flag própria (é a cultura do sonhar, não o sonho).
2. **Cat 3 precisa de um subcampo.** "Pesadelo relatado" (sonho ruim narrado) ≠ "angústia sem sonho" (desabafo onde 'sonhei/sonho' aparece de passagem). Proposta: campo booleano `tem_relato_onirico` transversal às categorias — muitos desabafos cat-3 não contêm sonho nenhum e talvez não devam entrar no arquivo.
3. **Dedup tem que ser semântico** (embeddings), não por hash: ~9 quase-duplicatas no lote — crossposts (r/Dreams↔r/LucidDreaming), reposts da mesma pessoa em dias seguidos, e a mesma história *reescrita* com outras palavras.
4. **Heurística camada 0 confirmada e ampliada:** filtrar `[deleted]`/`[removed]`, posts título-só com padrão "Sonhar com X", links puros, promo/estudo com URL. Só o padrão SEO já corta ~20% do volume PT.
5. **A faixa ambígua real é ~15-20%** (confiança baixa nos meus próprios julgamentos nesses casos) — consistente com o dimensionamento da camada Claude API.

## Casos de fronteira exemplares (para calibrar com João)

- **n15** — "hoje sonhei com você não queria mais ir embora queria voar com você" → onírico? desejo? poético-idiomático? **Indecidível assumido.**
- **n76** — "Make 2016 a turning point." postado em r/Dreams em 30/dez/2015 → desejo coletivo, na véspera exata do início da nossa série.
- **n214** — pesadelo simultâneo: duas pessoas da mesma família sonham a mesma coisa na mesma noite.
- **n246** — "acordo com palpitação porque sonhei que a Gupy recusou meu currículo" → o pesadelo do precariado; onírico e econômico ao mesmo tempo.
- **n276** — "A IA acabou com a minha carreira... o carro que você sempre sonhou" → desejo + ruptura tecnológica.
- **n289** — doutorando: "meu sonho sempre foi ser acadêmico... estou exausto".
- **n347** — luto: "Eu nunca sonhei com ele" → a *ausência* de sonho como dor. A rubrica não previa isso.
- **n350** — "Sonhei que tinha amigos e acordei triste" → onírico que é puro desejo.
- **n367** — "Meu sonho é nunca mais ver meus parentes" → desejo negativo, de fuga.
- **n381** — pesadelos recorrentes: ficar sem dinheiro, ser demitido, não terminar a faculdade → pesadelo inteiramente econômico.
- **n384** — "Meu maior sonho é ter minha casa própria" → o caso paradigmático brasileiro.
- **n396** — "comprei meu videogame dos sonhos... agora parece que estou vazio" → o desejo realizado que se esvazia.
- **n422** — sonhou com pessoa que não existe e acordou com saudade dela.
- **n432** — pesadelo com Trump, dez/2015 — o político invadindo o onírico exatamente onde a série começa.

## Próximos passos

1. Revisar os casos de fronteira acima com Fitipe + João → decidir n15-likes, `tem_relato_onirico`, destino da cat 7.
2. Congelar **prompt de triagem v1** (7 categorias + subcampos + exemplos de fronteira deste piloto).
3. Rodar Ollama (llama3.1:8b) sobre estes mesmos 491 e **medir concordância contra esta triagem manual** — isso dá o baseline da camada 1 antes de qualquer backfill.
4. Resolver acesso Bluesky via Jetstream.
