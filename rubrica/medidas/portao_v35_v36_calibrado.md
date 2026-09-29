# Portão v3.5 × v3.6 cru × v3.6 calibrado

*28/09/2026. Gerado por `aluno/calibrar_portao_v36.py` (só lê o banco; não reinfere: usa `p_portao`/`p_literal`/`p_figurado` gravados em `predicoes_v36`). O limiar é escolhido só na validação de 344 do final_v35 (semente 2015, 342 sem ambíguo); prova e cega só medem.*

## 1. Calibração (validação, n=342)

Literal real: 212/342 (62.0%) — o treino do v3.6 tem 83,6% de literais. O v3.6 cru marca 218 literais aqui (acerto exato do portão 88.0%); o v3.5 marca 216 (acerto 87.1%, n=342).

Acerto exato = as 8 células do portão idênticas ao gabarito. O limiar do literal varia; as outras sete classes ficam em 0,5 (figurado em 0.5).

| limiar p_literal | acerto exato do portão | acerto só do literal | literais marcados | taxa marcada |
|---|---|---|---|---|
| 0.30 | 88.0% | 95.0% | 227 | 66.4% |
| 0.35 | 88.3% | 95.0% | 225 | 65.8% |
| 0.40 | 88.6% | 95.3% | 224 | 65.5% |
| 0.45 | 88.6% | 95.3% | 222 | 64.9% |
| 0.50 **←** | 88.0% | 94.7% | 218 | 63.7% |
| 0.55 | 89.2% | 95.9% | 212 | 62.0% |
| 0.60 | 89.2% | 96.2% | 211 | 61.7% |
| 0.65 | 89.5% | 96.8% | 209 | 61.1% |
| 0.70 | 89.2% | 96.5% | 208 | 60.8% |
| 0.75 | 89.5% | 96.5% | 206 | 60.2% |
| 0.80 | 88.6% | 95.6% | 203 | 59.4% |
| 0.85 | 87.7% | 95.0% | 197 | 57.6% |
| 0.90 | 86.0% | 93.3% | 191 | 55.8% |
| 0.95 | 82.5% | 89.5% | 176 | 51.5% |

(A taxa real é 62.0%; 0,50 é o corte cru.)

- **Máximo acerto exato:** 89.5% num platô de limiares de 0.61 a 0.75 (passo 0,01); escolhido o do meio do platô, **0.66**.
- **Taxa marcada = taxa real:** limiar **0.55** → 212 marcados de 342 (real 212), acerto 89.2%.
- **p_figurado:** melhor 90.1% com limiar 0.35-0.37; em 0,50 dá 89.5% (diferença de 2 casos de 342). Ganho dentro do ruído: **p_figurado fica em 0,50**.

| limiar p_figurado (com literal em 0.66) | acerto exato | figurados marcados (real 110) |
|---|---|---|
| 0.30 | 89.2% | 118 |
| 0.35 | 90.1% | 115 |
| 0.40 | 89.8% | 113 |
| 0.45 | 89.5% | 111 |
| 0.50 | 89.5% | 110 |
| 0.55 | 89.5% | 110 |
| 0.60 | 89.5% | 109 |
| 0.65 | 88.9% | 107 |
| 0.70 | 88.9% | 107 |
| 0.75 | 88.3% | 105 |
| 0.80 | 88.0% | 103 |
| 0.85 | 88.0% | 101 |
| 0.90 | 86.5% | 95 |
| 0.95 | 83.3% | 83 |

Caveat: com n=342 um caso vale 0,29 ponto; o platô de 0.61-0.75 é a evidência, não o pico exato.

## 2. Prova (300; 296 sem ambíguo)

### Prova — 8 classes do portão

| portão | acerto exato | chute constante | teto entre anotadores | literais marcados (real) |
|---|---|---|---|---|
| v3.5 (gravado) | 92.2% | 62.8% | 93% | 196 (192) |
| v3.6 cru (gravado) | 90.9% | 62.8% | 93% | 203 (192) |
| v3.6 calibrado (literal>0.66) | 90.9% | 62.8% | 93% | 198 (192) |
| v3.6 taxa igualada (literal>0.55) | 90.5% | 62.8% | 93% | 202 (192) |

**v3.5**

| classe | n | marcados | precisão | revocação | F1 |
|---|---|---|---|---|---|
| literal | 192 | 196 | 96.4% | 98.4% | 97.4% |
| figurado | 96 | 95 | 95.8% | 94.8% | 95.3% |
| fala_do_sonhar | 11 | 15 | 46.7% | 63.6% | 53.8% |
| devaneio | 0 | 0 | — | — | — |
| obra | 1 | 0 | — | 0.0% | 0.0% |
| noticia | 0 | 2 | 0.0% | — | 0.0% |
| propaganda | 1 | 1 | 100.0% | 100.0% | 100.0% |
| descartavel | 2 | 1 | 100.0% | 50.0% | 66.7% |

**v3.6 cru**

| classe | n | marcados | precisão | revocação | F1 |
|---|---|---|---|---|---|
| literal | 192 | 203 | 93.6% | 99.0% | 96.2% |
| figurado | 96 | 92 | 94.6% | 90.6% | 92.6% |
| fala_do_sonhar | 11 | 16 | 50.0% | 72.7% | 59.3% |
| devaneio | 0 | 0 | — | — | — |
| obra | 1 | 2 | 0.0% | 0.0% | 0.0% |
| noticia | 0 | 0 | — | — | — |
| propaganda | 1 | 0 | — | 0.0% | 0.0% |
| descartavel | 2 | 6 | 33.3% | 100.0% | 50.0% |

**v3.6 calibrado**

| classe | n | marcados | precisão | revocação | F1 |
|---|---|---|---|---|---|
| literal | 192 | 198 | 94.9% | 97.9% | 96.4% |
| figurado | 96 | 92 | 94.6% | 90.6% | 92.6% |
| fala_do_sonhar | 11 | 16 | 50.0% | 72.7% | 59.3% |
| devaneio | 0 | 0 | — | — | — |
| obra | 1 | 2 | 0.0% | 0.0% | 0.0% |
| noticia | 0 | 0 | — | — | — |
| propaganda | 1 | 0 | — | 0.0% | 0.0% |
| descartavel | 2 | 6 | 33.3% | 100.0% | 50.0% |

Curva na prova, só informativa (NÃO usada para escolher; literal real 192):

| limiar p_literal | acerto exato | literais marcados |
|---|---|---|
| 0.50 | 90.9% | 203 |
| 0.55 | 90.5% | 202 |
| 0.60 | 90.5% | 200 |
| 0.66 | 90.9% | 198 |
| 0.70 | 91.2% | 195 |
| 0.75 | 91.6% | 192 |
| 0.80 | 91.2% | 191 |
| 0.85 | 90.9% | 187 |

## 3. Revisão cega (83; literal × não-literal e figurado)

O teto de 93% é do portão de 8 classes na auditoria v3.2; não foi medido para literal×não-literal da cega.

### Cega

| portão | acerto exato | chute constante | teto entre anotadores | literais marcados (real) |
|---|---|---|---|---|
| v3.5 (gravado) | 95.2% | 66.3% | — | 59 (55) |
| v3.6 cru (gravado) | 92.8% | 66.3% | — | 57 (55) |
| v3.6 calibrado (literal>0.66) | 90.4% | 66.3% | — | 55 (55) |
| v3.6 taxa igualada (literal>0.55) | 92.8% | 66.3% | — | 57 (55) |

**v3.5**

| classe | n | marcados | precisão | revocação | F1 |
|---|---|---|---|---|---|
| literal | 55 | 59 | 93.2% | 100.0% | 96.5% |
| figurado | 21 | 23 | 87.0% | 95.2% | 90.9% |

**v3.6 cru**

| classe | n | marcados | precisão | revocação | F1 |
|---|---|---|---|---|---|
| literal | 55 | 57 | 93.0% | 96.4% | 94.6% |
| figurado | 21 | 24 | 83.3% | 95.2% | 88.9% |

**v3.6 calibrado**

| classe | n | marcados | precisão | revocação | F1 |
|---|---|---|---|---|---|
| literal | 55 | 55 | 92.7% | 92.7% | 92.7% |
| figurado | 21 | 24 | 83.3% | 95.2% | 88.9% |

## 4. Taxa de literal no arquivo inteiro (o prior visível na página)

| portão | relatos | literal | taxa | figurado | taxa |
|---|---|---|---|---|---|
| v3.5 | 505320 | 204726 | 40.5% | 274073 | 54.2% |
| v3.6 cru | 509060 | 218216 | 42.9% | 278235 | 54.7% |
| v3.6 calibrado (>0.66) | 509060 | 205478 | 40.4% | 278231 | 54.7% |
| v3.6 taxa igualada (>0.55) | 509060 | 214098 | 42.1% | 278231 | 54.7% |

Nos 505320 relatos presentes em ambas as tabelas: v3.5 40.5% · v3.6 cru 43.1% · calibrado 40.6% · taxa igualada 42.3%.
Só canônicos (sem herdados, 501151): v3.6 cru 43.4% · calibrado 40.9%.

Referência: literal real na prova (sorteio uniforme) ≈ 65% (192/296), na validação 62.0%. A prova e a validação são amostras de outras populações do arquivo; a taxa do arquivo não tem gabarito.

## 5. Notas

- Órfãs: `inferir_v36.py --orfas` classificou 4 relatos na primeira passada e mais 52 na segunda (as 52 eram duplicatas cujo canônico é ele mesmo duplicata/herdado; a consulta de órfãs foi ajustada para incluir canônico com `herdado_de` preenchido). Tabela `predicoes_v36`: 509.060 linhas = `relatos`. `predicoes_v35` tem 505.320 (3.740 a menos); por isso a seção 4 traz também a taxa nos ids comuns.
- O limiar tirado da validação melhora a validação (88,0% → 89,5%, 5 casos de 342, dentro do ruído) e restaura o prior do arquivo (40,4% vs 40,5% do v3.5), mas **não devolve o acerto perdido** na prova (90,9%, igual ao cru) nem na cega (90,4%, pior que o cru 92,8%). O excesso de literais na prova (203 vs 192) cai para 198 com o corte, mas o erro restante é de discriminação, não só de limiar.
- Validação: v3.5 e v3.6 foram ambos selecionados nela (época); a validação não é independente do treino de escolha de época, só do treino de pesos.

## Recomendação

Para o portão literal/figurado, manter o v3.5 (prova 92,2% e cega 95,2% contra 90,9% e 92,8% do v3.6 cru, e 90,9% e 90,4% do calibrado); usar o v3.6 só nas demais cabeças, e, se a página precisar do portão v3.6, aplicar `p_literal > 0,66` (`aluno/limiar_portao_v36.json`), que só corrige a taxa de literal do arquivo, não a acurácia.
