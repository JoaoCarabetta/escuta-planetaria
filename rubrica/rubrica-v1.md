# Rubrica de Triagem v1 — RASCUNHO para revisão (Fitipe + João)

**Uso:** mesmo julgamento em três camadas — Ollama (camada 1), Claude API (camada 2, faixa
ambígua), humano (auditoria). A versão congelada vira o prompt literal; toda mudança
incrementa a versão (`rubrica-v1`, `v1.1`...) e fica registrada em `julgamentos.versao`.

## Saída obrigatória (JSON, nada além dele)

```json
{"categoria": 1, "confianca": 0.85, "tem_relato_onirico": true, "idioma": "pt"}
```

- `categoria`: 1-7 (abaixo)
- `confianca`: 0-1 — abaixo de **0.7** o caso sobe para a camada seguinte
- `tem_relato_onirico`: existe narrativa de sonho dormido no texto? (independente da categoria)
- `idioma`: código ISO do texto

## As 7 categorias

**1 · Relato onírico** — narra um sonho que aconteceu dormindo. Inclui sonho lúcido narrado,
pesadelo *narrado com predominância de relato*, sonho recorrente, paralisia/falso despertar,
sonho premonitório, relato de segunda mão ("meu primo sonhou que...").
> "Sonhei que estava numa casa que era e não era a da minha avó" · "I dreamt I was being chased"

**2 · Desejo/aspiração** — sonho acordado: futuro desejado, meta, anseio. Inclui desejo
negado ("nunca foi meu sonho ser designer"), desejo de fuga ("meu sonho é nunca mais ver meus
parentes"), desejo realizado-e-esvaziado ("comprei meu videogame dos sonhos e me sinto vazio").
> "Meu maior sonho é ter minha casa própria" · "sempre sonhei em cursar Medicina"

**3 · Pesadelo/angústia** — sofrimento como centro do texto: pesadelo relatado com ênfase no
sofrimento, OU desabafo/angústia onde "sonho/sonhei" aparece de passagem. O subcampo
`tem_relato_onirico` separa os dois casos (true = pesadelo narrado; false = angústia sem sonho).
> "Ando tendo pesadelos que me perturbam terrivelmente" (true) · "Eu nunca sonhei com ele
> [após a morte do pai]" (false — a ausência do sonho como dor)

**4 · Idiomático/uso próprio** — a palavra "sonho" em sentido que não é relato nem aspiração:
flerte ("sonhei com você 😏" sem narrativa), expressões ("dream team", "namorada dos sonhos"),
citação de letra, piada, **o doce de padaria** (sentido culinário PT — categoria do João),
aforismos soltos.
> "Average lucid dream experience: [meme]" · "sonho de valsa"

**5 · Ruído comercial/spam** — publicidade, SEO de dicionário de sonhos ("Sonhar com cobra,
o que significa | Significado dos Sonhos"), promoção de produto/canal/livro, scam.
A camada 0 pega a maioria; o que vazar cai aqui.

**6 · Indecidível** — fronteira genuína e irredutível, geralmente entre 1 e 2 (o poético que
é sonho E desejo ao mesmo tempo). Usar com parcimônia — é categoria de honestidade, não de
preguiça. Confiança baixa NÃO é motivo para 6; 6 é quando nenhuma leitura domina.
> "hoje sonhei com você não queria mais ir embora queria voar com você"

**7 · Meta-discussão** — fala SOBRE sonhar sem relatar nem desejar: técnicas de sonho lúcido,
suplementos, apps, perguntas ("quanto dura um sonho?"), teoria própria, convites ("comentem
seus sonhos"), fenômenos de memória onírica.
> "how do i lucid dream with adhd?" · "É como se eu estivesse sendo apagado mentalmente
> no meio do pensamento [sobre lembrar/esquecer sonhos]"

## Regras de fronteira (dos 491 do piloto)

1. Desabafo longo que **contém** narrativa de sonho dormido → categoria pelo CENTRO do texto;
   `tem_relato_onirico: true` preserva o relato para o arquivo.
2. "Sempre sonhei em/com [futuro]" → **2**, mesmo dentro de desabafo triste.
3. Pesadelo narrado: predominou a narrativa → **1**; predominou o sofrimento/insônia → **3**.
   Nos dois casos `tem_relato_onirico: true`.
4. Sonho erótico, sonho com ex, sonho de luto ("ele me visitou em sonho") → **1**.
5. Experiências liminares (paralisia, falso despertar, hipnagogia) narradas → **1**.
6. Pergunta meta COM relato dentro ("tive esse sonho [narra]; o que significa?") → **1**.
7. Texto vazio + mídia → não julgar sem extração multimodal (voltar para extração).
8. "[deleted]", só-link, SEO → deveria ter caído na camada 0; se chegar, **5** ou **4**.
9. Doce de padaria, receita, "sonho recheado" → **4** (nunca 5, a menos que seja anúncio).
10. Sonho de terceiro relatado ("minha mãe sempre sonhou que eu...") → categoria do sentido
    (desejo da mãe = **2**), anotando baixa confiança se ambíguo.

## Prompt (template a congelar após revisão)

```
Você é o triador do arquivo Escuta Planetária, que cataloga relatos públicos de sonhos
(dormindo) e de desejos (acordado). Leia o texto e classifique numa das 7 categorias:

1 relato onírico — narra sonho dormido (inclui lúcido, recorrente, paralisia, premonitório)
2 desejo/aspiração — sonho acordado: futuro desejado, meta, anseio (inclui desejo negado)
3 pesadelo/angústia — sofrimento como centro (pesadelo narrado OU desabafo sem sonho)
4 idiomático/uso próprio — flerte, expressão, meme, doce de padaria, citação
5 ruído comercial — publicidade, SEO "significado dos sonhos", promoção, spam
6 indecidível — fronteira genuína irredutível (raro; não é "estou em dúvida")
7 meta-discussão — fala sobre sonhar sem relatar: técnica, app, pergunta, teoria

Responda APENAS o JSON:
{"categoria": N, "confianca": 0.0-1.0, "tem_relato_onirico": true/false, "idioma": "xx"}

tem_relato_onirico = existe narrativa de sonho dormido no texto, qualquer categoria.
confianca < 0.7 significa que você quer que um juiz mais forte revise.

TEXTO:
<<<{texto}>>>
```

## Validação antes de congelar

1. Fitipe + João revisam este rascunho (especialmente as regras de fronteira e o lugar do doce).
2. Ollama (llama3.1:8b) julga os 491 do piloto com o prompt → grava em `julgamentos`.
3. Relatório de concordância vs triagem manual (global, por categoria, matriz de confusão).
4. Meta mínima sugerida: ~85% de concordância nas categorias 1/2/5 (as que dominam o volume);
   fronteiras 3/6/7 podem divergir mais — é onde a camada 2 existe.
