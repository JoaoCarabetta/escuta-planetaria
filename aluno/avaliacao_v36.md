# Avaliação v3.6 — prova 300 (prova_1: 200 linhas) · cega 83

## aluno_v36.pt — AMOSTRA-PROVA (300 relatos, gabarito v3.5)


### PORTÃO (fora 4 ambíguos)  (n=296)

acerto exato 90.9% · chute constante 62.8% (`literal`)

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| literal | 192 | 203 | 93.6% | 99.0% | 96.2% | 78.7% |
| figurado | 96 | 92 | 94.6% | 90.6% | 92.6% | 49.0% |
| fala_do_sonhar | 11 | 16 | 50.0% | 72.7% | 59.3% | 7.2% |
| devaneio | 0 | 0 | — | — | — | — |
| obra | 1 | 2 | 0.0% | 0.0% | 0.0% | 0.7% |
| noticia | 0 | 0 | — | — | — | — |
| propaganda | 1 | 0 | — | 0.0% | 0.0% | 0.7% |
| descartavel | 2 | 6 | 33.3% | 100.0% | 50.0% | 1.3% |

### CARGA (onde o gabarito abre a cabeça)  (n=196)

acerto exato 83.2% · chute constante 80.6% (`sem_afeto_dito`)

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| prazerosa | 11 | 27 | 37.0% | 90.9% | 52.6% | 10.6% |
| aflitiva | 22 | 25 | 76.0% | 86.4% | 80.9% | 20.2% |
| mista | 1 | 3 | 33.3% | 100.0% | 50.0% | 1.0% |
| estranha | 6 | 7 | 57.1% | 66.7% | 61.5% | 5.9% |
| sem_afeto_dito | 158 | 139 | 97.8% | 86.1% | 91.6% | 89.3% |

### DESPERTAR (onde o gabarito abre a cabeça)  (n=196)

acerto exato 84.7% · chute constante 82.7% (`(nada)`)

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| alivio | 0 | 0 | — | — | — | — |
| decepcao | 3 | 13 | 15.4% | 66.7% | 25.0% | 3.0% |
| acordou_mal | 17 | 13 | 69.2% | 52.9% | 60.0% | 16.0% |
| acordou_bem | 2 | 5 | 40.0% | 100.0% | 57.1% | 2.0% |
| desorientado | 6 | 6 | 83.3% | 83.3% | 83.3% | 5.9% |
| acordou_neutro | 7 | 8 | 50.0% | 57.1% | 53.3% | 6.9% |

### FIGURA (onde o gabarito abre a cabeça)  (n=100)

acerto exato 86.0% · chute constante 68.0% (`desejo`)

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| desejo | 70 | 74 | 94.6% | 100.0% | 97.2% | 82.4% |
| intensificador | 19 | 26 | 69.2% | 94.7% | 80.0% | 31.9% |
| votos | 0 | 0 | — | — | — | — |
| outra | 9 | 1 | 100.0% | 11.1% | 20.0% | 16.5% |

### ORIGEM (onde o gabarito abre a cabeça)  (n=37)

acerto exato 43.2% · chute constante 35.1% (`a_si`)

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| nao_diz | 14 | 20 | 55.0% | 78.6% | 64.7% | 54.9% |
| a_si | 15 | 9 | 88.9% | 53.3% | 66.7% | 57.7% |
| entidade_religiosa | 5 | 1 | 100.0% | 20.0% | 33.3% | 23.8% |
| espirito_proprio | 2 | 2 | 100.0% | 100.0% | 100.0% | 10.3% |
| universo_destino | 1 | 1 | 100.0% | 100.0% | 100.0% | 5.3% |
| morto | 0 | 3 | 0.0% | — | 0.0% | — |
| outra | 2 | 2 | 0.0% | 0.0% | 0.0% | 10.3% |

### CONTEÚDO (onde o gabarito é literal com conteúdo)  (n=196)

acerto exato 98.0% · chute constante 92.9% (`narrado`)

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| narrado | 182 | 178 | 100.0% | 97.8% | 98.9% | 96.3% |
| so_mencionado | 14 | 18 | 77.8% | 100.0% | 87.5% | 13.3% |

### TEM_ATRIB  (n=201)

acerto exato 89.6% · chute constante 81.6% (`(nada)`)

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| tem_atrib | 37 | 20 | 90.0% | 48.6% | 63.2% | 31.1% |

### BANDEIRA  (n=300)

acerto exato 98.3% · chute constante 100.0% (`(nada)`)

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| bandeira | 0 | 5 | 0.0% | — | 0.0% | — |

ids marcados com bandeira: ['76b733033c0ab160', 'a3ad8c1f7e1f9316', 'cfd08e67a960e250', '2bdaf45e8e7c69f6', '6e3fca69006a62e7']

confundidor da propaganda: 0 textos da prova com link/preço e sem propaganda no gabarito; marcados propaganda: 0

## aluno_v36.pt — REVISÃO CEGA DO FITIPE (83 relatos)

literal × não-literal: acerto 92.8% · chute constante 66.3%

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| literal | 55 | 57 | 93.0% | 96.4% | 94.6% | 79.7% |
| figurado | 21 | 24 | 83.3% | 95.2% | 88.9% | 40.4% |

## ALUNO ANTIGO (aluno.pt, v3.2) — mesma prova, gabarito v3.5


### PORTÃO  (n=296)

acerto exato 90.2% · chute constante 62.8% (`literal`)

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| literal | 192 | 190 | 97.4% | 96.4% | 96.9% | 78.7% |
| figurado | 96 | 99 | 88.9% | 91.7% | 90.3% | 49.0% |
| fala_do_sonhar | 11 | 0 | — | 0.0% | 0.0% | 7.2% |
| devaneio | 0 | 0 | — | — | — | — |
| obra | 1 | 0 | — | 0.0% | 0.0% | 0.7% |
| noticia | 0 | 0 | — | — | — | — |
| propaganda | 1 | 2 | 50.0% | 100.0% | 66.7% | 0.7% |
| descartavel | 2 | 0 | — | 0.0% | 0.0% | 1.3% |

## ALUNO ANTIGO — REVISÃO CEGA

literal × não-literal: acerto 81.9% · chute constante 66.3%

| classe | n | marcados | precisão | revocação | F1 | F1 "sempre sim" |
|---|---|---|---|---|---|---|
| literal | 55 | 62 | 82.3% | 92.7% | 87.2% | 79.7% |
| figurado | 21 | 9 | 55.6% | 23.8% | 33.3% | 40.4% |

## Deriva da régua: gabarito v3.5 × anotação v3.2 dos mesmos relatos (n=296)
literal coincide em 98.6% · figurado coincide em 99.0%

## Textos longos — validação (literal e figurado, acerto por célula)

| modelo | curtos (n) | longos (n) |
|---|---|---|
| aluno_v36.pt | 97.9% (237) | 92.5% (107) |
| aluno.pt (v3.2, 192 tokens) | 96.0% (237) | 70.3% (107) |