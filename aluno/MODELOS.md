# Modelos do Escuta Planetária — quem é quem

Dois especialistas sobre o mesmo BERTimbau (`modelo_v35.AlunoV35`, oito cabeças,
janelas de 254 tokens). Decisão do Fitipe, 28/09/2026.

## portao_v1 — o portão

- Pesos: `portao_v1.pt` → link para `aluno_v35.pt` (aluno v3.5).
- Origem: treino em `final_v35` (3.096 anotações Opus), `treinar_v35.py`.
- Na página: decide **o que o relato é** — literal, figurado, fala_do_sonhar,
  devaneio, obra, noticia, propaganda, descartavel — e a bandeira.
- Predições: tabela `predicoes_v35` (505.320 linhas); view `predicoes_portao` (idêntica).
- Números: prova 92,2% (teto entre anotadores 93%), cega 95,2%.
  `rubrica/medidas/resultado-do-aluno-v35.md`.

## afeto_v1 — o afeto

- Pesos: `afeto_v1.pt` → link para `aluno_v36.pt` (aluno v3.6).
- Origem: `final_v35` + `afeto15k` (sem o lote a_27) + 90% do `raros_enxuto`,
  13.177 linhas, `treinar_v36.py`. Ensinou alívio, mista, morto, espírito próprio.
- Na página: decide **o que o relato sente** — carga, conteúdo, despertar,
  figura, tem_atrib, origem.
- Predições: tabela `predicoes_v36` (509.060 linhas); view `predicoes_afeto` (idêntica).
- Seu portão (e bandeira) NÃO é usado: piorou por prior inflado (83,6% de literais
  no treino contra ~64% na população). `rubrica/medidas/resultado-do-aluno-v36.md`,
  `rubrica/medidas/portao_v35_v36_calibrado.md`.

## Regra

**O afeto só vale onde o portão diz `literal`.** Carga, conteúdo, despertar,
origem de um relato que o portão não marcou literal não são mostrados nem contados.
(figura vale sob `figurado`, mas é dita pelo portão da mesma forma.)

## Nomes: nada foi renomeado

`aluno_v35.pt`, `aluno_v36.pt`, `predicoes_v35` e `predicoes_v36` continuam
existindo — `planeta-v3/gerar.py` e outros scripts os leem. `portao_v1.pt`,
`afeto_v1.pt`, `predicoes_portao` e `predicoes_afeto` são apelidos (link simbólico
e VIEW), não cópias.

## Próximas versões

- Próximo portão: **portao_v2** (pesos `portao_v2.pt`, tabela `predicoes_portao_v2`).
- Próximo afeto: **afeto_v2** (pesos `afeto_v2.pt`, tabela `predicoes_afeto_v2`).
  Treinado (retreino só em literais: `dados_afeto.py`, `treinar_afeto.py`; `afeto_v2.pt`
  existe), medido em `rubrica/medidas/resultado-do-afeto-v2.md`. Ainda não há
  predições gravadas nem uso na página; `figura` continua do afeto_v1.
