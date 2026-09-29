# Afeto v2 — retreino só em literais

*28/09/2026. `aluno/afeto_v2.pt` (época 6 de 8) × `aluno/aluno_v36.pt` (afeto v1).
Só as cabeças de afeto, nos textos cujo GABARITO diz `literal` (a decisão
literal × não-literal é do portão e não entra aqui). `L = 0,5`. Números
completos: `aluno/avaliacao_afeto_v2.md` / `.json`.*

## Treino

Mesmas fontes do v3.6 (final_v35 + afeto15k sem a_27 + 90% do raros_enxuto),
só literais: **11.019 de 13.177** (final_v35 1.929 · afeto15k 7.024 ·
raros_enxuto 2.066; 1.193 são literal + fala_do_sonhar). Portão e bandeira ficam
no modelo com peso 0 na perda. Época decidida pela média do F1 de carga +
despertar + origem nos 212 literais da validação do final_v35 (semente 2015):
0,746 · 0,806 · 0,806 · 0,802 · 0,821 · **0,825** · 0,819 · 0,820. ~9 min/época.

Contagens de treino: carga sem_afeto_dito 6.566 · prazerosa 1.772 · aflitiva
1.689 · estranha 1.046 · mista 153; despertar acordou_mal 955 · decepção 746 ·
acordou_bem 611 · desorientado 442 · alívio 285 · neutro 186; origem nao_diz 777
· a_si 373 · entidade_religiosa 301 · espírito_próprio 179 · morto 120 · outra
100 · universo_destino 55; conteúdo narrado 9.320 / só_mencionado 1.592;
tem_atrib 1.664 sim. **figura: só 26 exemplos** (literal E figurado).

## Regra dos três números

Modelo · chute constante · teto entre anotadores. Teto só existe para o portão
(93%); para estas cabeças ninguém mediu, então o chute constante é a única linha
de base (coluna abaixo).

## Acerto exato por cabeça (literais do gabarito)

| conjunto / cabeça | n | v3.6 | afeto_v2 | chute |
|---|---|---|---|---|
| prova · carga | 192 | 82,8% | **85,4%** | 80,7% |
| prova · despertar | 192 | 84,4% | **88,0%** | 82,3% |
| prova · origem | 35 | 40,0% | **51,4%** | 34,3% |
| prova · conteúdo | 192 | 97,9% | 97,9% | 94,8% |
| prova · tem_atrib | 192 | 89,6% | 88,5% | 81,8% |
| raros · carga | 221 | 72,4% | 72,9% | 42,1% |
| raros · despertar | 222 | 68,9% | **73,9%** | 43,2% |
| raros · origem | 44 | 38,6% | 38,6% | 18,2% |
| raros · conteúdo | 219 | 91,3% | 91,8% | 76,3% |
| raros · tem_atrib | 222 | 92,3% | 91,9% | 80,2% |
| final_v35 (decidiu a época) · carga | 212 | 80,7% | 82,1% | 57,5% |
| final_v35 · despertar | 212 | 77,8% | **83,0%** | 55,7% |
| final_v35 · origem | 71 | **78,9%** | 76,1% | 56,3% |

## Classes raras (F1; n entre parênteses)

| classe | prova | raros (263) | final_v35 |
|---|---|---|---|
| alívio (despertar) | n=0 | 81,0 → **85,0** (19) | 100 → 100 (1) |
| acordou_bem | 57,1 → 57,1 (2) | 84,0 → **87,2** (44) | 85,7 → 87,2 (19) |
| desorientado | 83,3 → 83,3 (6) | 76,1 → **83,9** (31) | 59,3 → **70,0** (11) |
| mista (carga) | 50,0 → 50,0 (1) | 45,5 → 42,1 (9) | n=0 |
| morto (origem) | n=0 | 70,0 → 70,6 (9) | n=0 |
| espírito próprio | 100 → 100 (2) | 64,0 → 55,6 (9) | n=0 |

Onde v3.6 já tinha aprendido a classe rara, o v2 não perde (alívio, morto,
acordou_bem sobem ou empatam); em mista e espírito próprio há queda de 3 a 8
pontos com n de 9. Perdas mais claras: `acordou_mal` na prova (60,0 → 43,5, n=17),
`acordou_neutro` na final (70,0 → 47,1, n=10), `a_si` nos raros (44,4 → 20,0, n=7).

## Figura: o v2 não serve

O v2 só viu 26 exemplos de figura (literal E figurado). Em todo figurado do
gabarito na prova (n=100), figura exato cai de **86,0% (v3.6) para 61,0%**, abaixo
do chute constante (68,0%); `intensificador` F1 80,0 → 0,0. Figura é do domínio
figurado; fica no v3.6.

## Ressalvas

- Diferenças de 2 a 4 pontos na prova valem 4 a 7 casos de 192; origem (n=35 e 44)
  é ruído. O sinal que se repete nos três conjuntos é **despertar** (+3,6, +5,0,
  +5,2 pontos). Carga sobe pouco (+2,6, +0,5, +1,4).
- A validação do final_v35 decidiu a época do v2 (o v3.6 também foi escolhido nela);
  prova e raros nunca decidiram nada.

## Recomendação

Trocar da página o afeto pelo v2 para **despertar** e, se quiser, carga, conteúdo
e atribuição/origem (ganho pequeno, sem perda robusta), mantendo `figura` no v3.6 e o portão no
portao_v1 — o ganho real é modesto (despertar +4 a +5 pontos, o resto dentro do
ruído), então só vale a inferência nos ~205 mil literais se o despertar for
central para a página.

## Se for trocar: o que mudar em `planeta-v3/gerar.py` (NÃO foi mudado)

Hoje: `FROM relatos r JOIN predicoes_v36 b …` (linha ~425), lendo `b.p_carga,
b.p_conteudo, b.p_despertar, b.p_figura, b.p_tem_atrib, b.p_origem`. Passo a passo:

1. Inferir o `afeto_v2.pt` só nos relatos que o portão marca literal (~205 mil dos
   505 mil) numa tabela nova `predicoes_afeto_v2` (mesmo esquema de `predicoes_v36`,
   via cópia de `inferir_v36.py` apontando para o `.pt` novo e filtrando pelo
   portão de `predicoes_portao`, com o limiar 0,66 de `limiar_portao_v36.json` para
   os que só têm v3.6).
2. `LEFT JOIN predicoes_afeto_v2 c ON c.relato_id = r.id` e ler
   `COALESCE(c.p_carga, b.p_carga)` etc. para carga, conteúdo, despertar, tem_atrib,
   origem; **`b.p_figura` fica do v3.6**.
3. Trocar `predicoes_v35`/`predicoes_v36` por `predicoes_portao`/`predicoes_afeto`
   é só cosmético (as views são idênticas).

## Arquivos

- `aluno/dados_afeto.py`, `aluno/treinar_afeto.py`, `aluno/avaliar_afeto_v2.py`
- `aluno/afeto_v2.pt`, `aluno/afeto_v2_historico.json`, `/tmp/treino_afeto_v2.log`
- `aluno/avaliacao_afeto_v2.md` / `.json`
- Nomes: `aluno/MODELOS.md`, views `predicoes_portao`/`predicoes_afeto`, links
  `aluno/portao_v1.pt`/`afeto_v1.pt`
