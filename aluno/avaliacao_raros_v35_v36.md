# aluno_v35.pt × aluno_v36.pt — validação extra dos raros (263) e validação do final_v35 (344)

Nenhuma das duas é a amostra-prova (300): são os cortes que decidiram a época de cada treino (final_v35) e a medida das classes raras que a rodada v3.6 visava (raros_enxuto). `L=0.5` em tudo, igual `avaliar_v35.py`.

## VALIDAÇÃO EXTRA — raros_enxuto (10% estratificado, semente 2015) (n=263)


### PORTÃO (fora 0 ambíguos)  (n=263)

acerto exato: **v3.5 67.7%** · **v3.6 81.0%** · chute constante 69.6% (`literal`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| literal | 222 | 84.4% | 100.0% | 91.5% | 93.4% | 95.9% | 94.7% | 91.5% |
| figurado | 8 | 0.0% | 0.0% | 0.0% | 57.1% | 50.0% | 53.3% | 5.9% |
| fala_do_sonhar | 71 | 62.1% | 90.1% | 73.6% | 78.9% | 78.9% | 78.9% | 42.5% |
| devaneio | 0 | — | — | — | — | — | — | — |
| obra | 1 | — | 0.0% | 0.0% | — | 0.0% | 0.0% | 0.8% |
| noticia | 0 | — | — | — | — | — | — | — |
| propaganda | 0 | — | — | — | — | — | — | — |
| descartavel | 2 | — | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 1.5% |

### CARGA (onde o gabarito abre a cabeça)  (n=221)

acerto exato: **v3.5 65.2%** · **v3.6 72.4%** · chute constante 42.1% (`sem_afeto_dito`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| prazerosa | 63 | 65.4% | 81.0% | 72.3% | 69.5% | 90.5% | 78.6% | 44.4% |
| aflitiva | 45 | 58.9% | 73.3% | 65.3% | 79.5% | 77.8% | 78.7% | 33.8% |
| mista | 9 | 0.0% | 0.0% | 0.0% | 38.5% | 55.6% | 45.5% | 7.8% |
| estranha | 20 | 70.8% | 85.0% | 77.3% | 75.0% | 90.0% | 81.8% | 16.6% |
| sem_afeto_dito | 93 | 81.2% | 69.9% | 75.1% | 83.3% | 80.6% | 82.0% | 59.2% |

### DESPERTAR (onde o gabarito abre a cabeça)  (n=222)

acerto exato: **v3.5 59.5%** · **v3.6 68.9%** · chute constante 43.2% (`(nada)`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| alivio | 19 | 40.0% | 10.5% | 16.7% | 73.9% | 89.5% | 81.0% | 15.8% |
| decepcao | 21 | 57.9% | 52.4% | 55.0% | 62.5% | 71.4% | 66.7% | 17.3% |
| acordou_mal | 22 | 34.8% | 72.7% | 47.1% | 41.0% | 72.7% | 52.5% | 18.0% |
| acordou_bem | 44 | 73.6% | 88.6% | 80.4% | 75.0% | 95.5% | 84.0% | 33.1% |
| desorientado | 31 | 72.0% | 58.1% | 64.3% | 67.5% | 87.1% | 76.1% | 24.5% |
| acordou_neutro | 1 | 5.9% | 100.0% | 11.1% | 6.7% | 100.0% | 12.5% | 0.9% |

### FIGURA (onde o gabarito abre a cabeça)  (n=8)

acerto exato: **v3.5 37.5%** · **v3.6 37.5%** · chute constante 50.0% (`desejo`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| desejo | 4 | 100.0% | 25.0% | 40.0% | 50.0% | 25.0% | 33.3% | 66.7% |
| intensificador | 2 | 28.6% | 100.0% | 44.4% | 0.0% | 0.0% | 0.0% | 40.0% |
| votos | 0 | — | — | — | — | — | — | — |
| outra | 2 | 50.0% | 50.0% | 50.0% | 66.7% | 100.0% | 80.0% | 40.0% |

### ORIGEM (onde o gabarito abre a cabeça)  (n=66)

acerto exato: **v3.5 12.1%** · **v3.6 36.4%** · chute constante 24.2% (`espirito_proprio`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| nao_diz | 13 | 25.0% | 53.8% | 34.1% | 42.1% | 61.5% | 50.0% | 32.9% |
| a_si | 10 | 18.2% | 40.0% | 25.0% | 42.9% | 30.0% | 35.3% | 26.3% |
| entidade_religiosa | 16 | 38.9% | 87.5% | 53.8% | 41.7% | 62.5% | 50.0% | 39.0% |
| espirito_proprio | 20 | 50.0% | 90.0% | 64.3% | 59.4% | 95.0% | 73.1% | 46.5% |
| universo_destino | 0 | — | — | — | — | — | — | — |
| morto | 10 | 75.0% | 30.0% | 42.9% | 66.7% | 80.0% | 72.7% | 26.3% |
| outra | 5 | 0.0% | 0.0% | 0.0% | — | 0.0% | 0.0% | 14.1% |

### CONTEÚDO (onde o gabarito é literal com conteúdo)  (n=219)

acerto exato: **v3.5 86.8%** · **v3.6 91.3%** · chute constante 76.3% (`narrado`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| narrado | 167 | 86.7% | 97.6% | 91.8% | 96.2% | 92.2% | 94.2% | 86.5% |
| so_mencionado | 52 | 87.1% | 51.9% | 65.1% | 78.0% | 88.5% | 82.9% | 38.4% |

### TEM_ATRIB  (n=254)

acerto exato: **v3.5 89.8%** · **v3.6 91.7%** · chute constante 74.0% (`(nada)`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| tem_atrib | 66 | 79.4% | 81.8% | 80.6% | 82.6% | 86.4% | 84.4% | 41.2% |

### BANDEIRA  (n=263)

acerto exato: **v3.5 99.6%** · **v3.6 99.6%** · chute constante 99.6% (`(nada)`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| bandeira | 1 | — | 0.0% | 0.0% | — | 0.0% | 0.0% | 0.8% |

## VALIDAÇÃO — final_v35 (10%, semente 2015; decidiu a época dos dois) (n=344)


### PORTÃO (fora 2 ambíguos)  (n=342)

acerto exato: **v3.5 87.1%** · **v3.6 88.0%** · chute constante 53.5% (`literal`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| literal | 212 | 96.8% | 98.6% | 97.7% | 94.5% | 97.2% | 95.8% | 76.5% |
| figurado | 110 | 98.1% | 93.6% | 95.8% | 96.4% | 96.4% | 96.4% | 48.7% |
| fala_do_sonhar | 50 | 70.4% | 76.0% | 73.1% | 85.4% | 70.0% | 76.9% | 25.5% |
| devaneio | 1 | — | 0.0% | 0.0% | — | 0.0% | 0.0% | 0.6% |
| obra | 3 | 0.0% | 0.0% | 0.0% | 100.0% | 33.3% | 50.0% | 1.7% |
| noticia | 1 | — | 0.0% | 0.0% | — | 0.0% | 0.0% | 0.6% |
| propaganda | 1 | 100.0% | 100.0% | 100.0% | — | 0.0% | 0.0% | 0.6% |
| descartavel | 0 | — | — | — | 0.0% | — | 0.0% | — |

### CARGA (onde o gabarito abre a cabeça)  (n=214)

acerto exato: **v3.5 82.7%** · **v3.6 80.4%** · chute constante 57.9% (`sem_afeto_dito`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| prazerosa | 37 | 74.4% | 86.5% | 80.0% | 70.8% | 91.9% | 80.0% | 29.5% |
| aflitiva | 22 | 71.4% | 68.2% | 69.8% | 75.0% | 81.8% | 78.3% | 18.6% |
| mista | 0 | — | — | — | 0.0% | — | 0.0% | — |
| estranha | 33 | 93.1% | 81.8% | 87.1% | 92.6% | 75.8% | 83.3% | 26.7% |
| sem_afeto_dito | 124 | 88.4% | 86.3% | 87.3% | 87.2% | 87.9% | 87.6% | 73.4% |

### DESPERTAR (onde o gabarito abre a cabeça)  (n=214)

acerto exato: **v3.5 81.8%** · **v3.6 78.0%** · chute constante 56.1% (`(nada)`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| alivio | 1 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.9% |
| decepcao | 22 | 76.9% | 90.9% | 83.3% | 72.4% | 95.5% | 82.4% | 18.6% |
| acordou_mal | 49 | 75.0% | 73.5% | 74.2% | 68.9% | 85.7% | 76.4% | 37.3% |
| acordou_bem | 19 | 80.0% | 84.2% | 82.1% | 78.3% | 94.7% | 85.7% | 16.3% |
| desorientado | 11 | 71.4% | 45.5% | 55.6% | 50.0% | 72.7% | 59.3% | 9.8% |
| acordou_neutro | 10 | 87.5% | 70.0% | 77.8% | 70.0% | 70.0% | 70.0% | 8.9% |

### FIGURA (onde o gabarito abre a cabeça)  (n=112)

acerto exato: **v3.5 85.7%** · **v3.6 86.6%** · chute constante 68.8% (`desejo`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| desejo | 82 | 91.9% | 96.3% | 94.0% | 89.7% | 95.1% | 92.3% | 84.5% |
| intensificador | 22 | 75.0% | 54.5% | 63.2% | 90.0% | 81.8% | 85.7% | 32.8% |
| votos | 10 | 90.0% | 90.0% | 90.0% | 100.0% | 90.0% | 94.7% | 16.4% |
| outra | 2 | — | 0.0% | 0.0% | — | 0.0% | 0.0% | 3.5% |

### ORIGEM (onde o gabarito abre a cabeça)  (n=79)

acerto exato: **v3.5 65.8%** · **v3.6 77.2%** · chute constante 54.4% (`nao_diz`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| nao_diz | 48 | 78.2% | 89.6% | 83.5% | 93.6% | 91.7% | 92.6% | 75.6% |
| a_si | 29 | 86.4% | 65.5% | 74.5% | 92.0% | 79.3% | 85.2% | 53.7% |
| entidade_religiosa | 9 | 88.9% | 88.9% | 88.9% | 80.0% | 88.9% | 84.2% | 20.5% |
| espirito_proprio | 1 | 33.3% | 100.0% | 50.0% | 50.0% | 100.0% | 66.7% | 2.5% |
| universo_destino | 2 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 4.9% |
| morto | 0 | — | — | — | — | — | — | — |
| outra | 0 | 0.0% | — | 0.0% | 0.0% | — | 0.0% | — |

### CONTEÚDO (onde o gabarito é literal com conteúdo)  (n=214)

acerto exato: **v3.5 96.7%** · **v3.6 96.3%** · chute constante 93.5% (`narrado`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| narrado | 200 | 96.6% | 100.0% | 98.3% | 99.5% | 96.5% | 98.0% | 96.6% |
| so_mencionado | 14 | 100.0% | 50.0% | 66.7% | 65.0% | 92.9% | 76.5% | 12.3% |

### TEM_ATRIB  (n=235)

acerto exato: **v3.5 91.1%** · **v3.6 91.5%** · chute constante 66.4% (`(nada)`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| tem_atrib | 79 | 93.9% | 78.5% | 85.5% | 88.3% | 86.1% | 87.2% | 50.3% |

### BANDEIRA  (n=344)

acerto exato: **v3.5 95.6%** · **v3.6 95.1%** · chute constante 96.5% (`(nada)`)

| classe | n | v3.5 prec | v3.5 rev | v3.5 F1 | v3.6 prec | v3.6 rev | v3.6 F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|---|---|
| bandeira | 12 | 28.6% | 16.7% | 21.1% | 38.1% | 66.7% | 48.5% | 6.7% |