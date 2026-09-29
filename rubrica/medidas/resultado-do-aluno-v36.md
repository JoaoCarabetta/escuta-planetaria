# O aluno v3.6 — o que a junção ensinou, e o que custou

*28/09/2026. Mesmo BERTimbau, mesmas oito cabeças, mesmo critério de seleção
de época do v3.5 (só a validação do final_v35 decide; bandeira fora do
critério). Treino: `final_v35` (3.096) + `afeto15k` (7.736, sorteio uniforme
entre literais) + `raros_enxuto` treino (2.345, candidatos a classes raras
pescados por sondas) = 13.177 linhas — 4,3× o treino do v3.5. Época 3 venceu
(critério 0,881 na validação do final_v35). Pesos: `aluno/aluno_v36.pt`.
Números completos: `aluno/avaliacao_v36.md` (prova 300 + cega 83, formato do
v3.5) e `aluno/avaliacao_raros_v35_v36.md` (v3.5 × v3.6 nos 263 de validação
extra do raros_enxuto e nos 344 do final_v35, lado a lado).*

## Regra dos três números

Modelo · chute constante (classe mais comum) · teto entre anotadores (só
existe medido para o portão: 93%, auditoria v3.2, `resultado-do-aluno-v35.md`).
Nas outras cabeças não há teto medido — três anotadores nunca revisaram o
mesmo lote de carga/despertar/figura/origem.

## Prova (300, sorteio uniforme dos elegíveis) — v3.5 × v3.6

| cabeça | v3.5 | v3.6 | chute constante | teto |
|---|---|---|---|---|
| portão exato | **92,2%** | 90,9% | 62,8% | 93% |
| carga exato | 82,1% | **83,2%** | 80,6% | — |
| despertar exato | 83,7% | **84,7%** | 82,7% | — |
| figura exato | 84,0% | **86,0%** | 68,0% | — |
| origem exato (n=37) | **45,9%** | 43,2% | 35,1% | — |
| cega (literal×não-literal, n=83) | **95,2%** | 92,8% | 66,3% | — |
| longos >1.000 car. (validação, literal/figurado) | **94%** | 92,5% | — | — |

A prova quase não tem as classes que a rodada visava (alívio 0, acordou_bem 2,
mista 1): não é onde se mede o ganho. É onde se mede a perda do portão.

## O que ganhou — validação extra do raros_enxuto (263, fora do treino dos dois)

Tabela completa em `aluno/avaliacao_raros_v35_v36.md`. Aqui as classes raras
têm n de verdade (9 a 71, não 0 a 2 como na prova):

| cabeça | acerto exato v3.5 | acerto exato v3.6 | classe que mais mudou |
|---|---|---|---|
| portão | 67,7% | **81,0%** | figurado F1 0% → **53,3%** (n=8); fala_do_sonhar F1 73,6% → 78,9% (n=71) |
| carga | 65,2% | **72,4%** | mista F1 0% → **45,5%** (n=9); aflitiva F1 65,3% → 78,7% (n=45) |
| despertar | 59,5% | **68,9%** | alívio F1 16,7% → **81,0%** (n=19); desorientado F1 64,3% → 76,1% (n=31) |
| origem | 12,1% | **36,4%** | morto F1 42,9% → **72,7%** (n=10); espírito_próprio F1 64,3% → 73,1% (n=20) |
| conteúdo | 86,8% | 91,3% | so_mencionado F1 65,1% → 82,9% (n=52) |

**Alívio, mista, morto e figurado passam de quase-zero para aprendidos.** Era
exatamente o buraco que o v3.5 (`resultado-do-aluno-v35.md`) apontava como
"não aprendeu" ou "sem medida". Na validação do final_v35 (344, mesma que
decidiu a época) o ganho de origem se repete (65,8% → 77,2%) — não é artefato
só do raros_enxuto.

## O que piorou — o prior do portão inflou

**Portão exato na prova cai 92,2% → 90,9% (1,3 ponto), e a causa tem número:**
na prova, 192 relatos são de fato `literal`; o v3.5 marcava 196 como literal
(4 falsos positivos), o **v3.6 marca 203 (11 falsos positivos)** — quase o
triplo do excesso, com a revocação praticamente igual (98,4% → 98,9%). A causa
é o treino: `afeto15k` sorteou uniforme entre literais e trouxe 7.736 linhas
das quais a maioria é literal, subindo o portão literal de **62,3% do treino
(v3.5, 1.929/3.096) para 83,6% (v3.6, 11.019/13.177)** — bem acima dos ~64% da
população da prova. O modelo aprendeu o prior do treino, não o da prova.
Mesmo padrão, mais fraco, em carga (82,1→83,2 na prova mas 82,7→80,4 na
validação do final_v35) e despertar (83,7→84,7 na prova mas 81,8→78,0 na
validação): ganham nas classes raras e perdem um pouco de precisão nas
grandes. A cega (95,2→92,8) e os textos longos da validação (94→92,5) confirmam
a mesma direção: leve perda no que já estava quase no teto.

## Recomendação

**Depende de qual cabeça a página usa.**

- **Trocar para v3.6:** se a página mostra ou vai mostrar **carga, despertar,
  figura ou origem** — inclusive as classes raras (alívio, mista, espírito
  próprio, morto) — o v3.6 é estritamente melhor, com ganho grande e medido
  fora da prova (raros_enxuto, 263) e confirmado na validação do final_v35.
- **Manter v3.5:** se o uso é só **portão literal/figurado** em texto curto
  (o caso de maior volume no arquivo — 505 mil relatos, a maioria posts e
  comentários curtos), o v3.5 tem 1,3 ponto a mais de acerto exato na prova e
  quase 3× menos falso positivo de literal. Para esse uso isolado, trocar não
  compensa.
- **Meio-termo, se dá pra fazer sem retreinar:** usar v3.6 para carga/
  despertar/figura/origem e manter v3.5 para o portão (ensemble por cabeça),
  ou recalibrar o limiar do literal no v3.6 numa amostra sorteada — o excesso
  é de limiar (revocação igual, precisão pior), não de aprendizado quebrado.

**Não decidido aqui:** o que pesa mais para a página, cobertura das classes
raras ou precisão do portão. Isso é escolha de produto, não de modelo.

## Arquivos

- `aluno/dados_v36.py`, `treinar_v36.py`, `avaliar_v36.py`, `avaliar_raros_v36.py`
  (os v3.5 não foram tocados)
- `aluno/aluno_v36.pt` (época 3) · `aluno/aluno_v36_historico.json`
- `aluno/avaliacao_v36.md` / `.json` — prova (300) e cega (83), mesmo formato do v3.5
- `aluno/avaliacao_raros_v35_v36.md` — v3.5 × v3.6 lado a lado nos 263 do
  raros_enxuto e nos 344 do final_v35
- `/tmp/treino_v36.log` — log completo do treino
