# Instruções para quem anota (v3.1)

Trabalhe no seu nível máximo de cuidado. Português brasileiro.
Diretório: `/Users/fitipe/Desktop/arte_c_joao_tta/escuta_planetaria`

## 1. Leia antes de julgar qualquer coisa
- `rubrica/rubrica-v3.1.md` — a rubrica inteira.
- `rubrica/decisoes-v3.1.md` — por que cada campo existe e de quem veio a
  decisão. Vários campos existem porque anotadores anteriores travaram sem eles.

## 2. Pegue a sua leva
Fatia disjunta: ninguém pega o mesmo texto que você.

    python3 rubrica/lote_v31.py pegar --agente=N --n=90 --fonte=FONTE

`--fonte=reanotar` são textos já julgados na rubrica v3 antiga, que você relê com
a v3.1. **Não consulte o julgamento antigo**: o objetivo é medir o que a rubrica
nova muda, e olhar o veredito velho contamina isso.
`--fonte=prova` são relatos sorteados uniformemente do arquivo.

## 3. Julgue

Regras que custaram caro e precisam ser respeitadas à risca:

- **`literal` não exige que o texto diga "dormi" ou "sonhei".** Reconhece-se pela
  impossibilidade da cena, pelo tempo verbal, pela ausência de intenção, pelo
  despertar mencionado.
- "meu sonho é X" é quase sempre `figurado` — mas "sonhei com X e se realizou"
  também é, e "tive um pesadelo" é literal. A preposição "com" costuma marcar o
  onírico e às vezes não marca.
- **`recorrente` exige que O SONHO se repita.** "sonhei que tava trabalhando de
  novo" é cena, não recorrência. Foi o falso positivo que cinco anotadores
  independentes acharam.
- **`lucido` é lucidez**, saber que se está sonhando — não vivacidade. "sonho
  muito lúcido" quase sempre quer dizer vívido; não marque.
- **`morto` é visita de quem já morreu.** Alguém morrendo dentro do sonho é
  `morte_no_sonho`. Par de calibração: "sonhei com meu pai e ele morreu tem 8
  anos" contra "sonhei que meu pai morreu".
- **`ironico` exige duas coisas juntas**: conteúdo que o próprio texto marca como
  ruim E um sinal de leveza (kkk, emoji de riso, exagero que estoura o registro,
  ressalva que desmente). **Nunca marque ironia só porque o desejo parece
  inconcebível** — isso é limite de quem lê, não propriedade do texto.
- **`carga` nunca é inferida.** Se o texto não diz o que se passou dentro do
  sonho, use `nao_dito`. Carga obrigatória fabrica dado.
- **`descartavel` exige justificativa escrita** na nota. Na dúvida, não descarte:
  o arquivo perde as bordas, que são o material.
- **`meta`, `copy_paste`, `falta_contexto` e `bandeira` são marcas**, não destinos
  — combinam com qualquer coisa do portão.
- **`falta_contexto`**: o texto responde a um fio, ou depende de uma imagem, que
  a coleta não guardou.

`confianca` é obrigatória: `alta` · `media` · `duvida`. Use `duvida` de verdade
quando for dúvida — a calibração dela é medida depois, e dúvida inflada estraga
tanto quanto confiança inflada. Escreva em `nota` o que travou.

## 4. Grave

    python3 rubrica/lote_v31.py gravar --agente=N < /caminho/do/seu.json

Chaves por objeto — `id` e `confianca` obrigatórias;
`literal, figurado, devaneio, obra, noticia, propaganda, descartavel, meta,
copy_paste, falta_contexto, bandeira` como 0 ou 1;
`figura, carga, tom, despertar, memoria, modo, presencas, atribuicao` como
listas; `nota` como texto.

## 5. Relatório final

Curto e específico: distribuição do portão, contagem de confiança e, sobretudo,
**o que a v3.1 ainda não comporta** — casos concretos, com id e citação, que
você teve de forçar num campo.

E o contrário também: se algum campo novo (`despertar`, `memoria`,
`falta_contexto`, `copy_paste`) se mostrou inútil ou confuso na prática, diga.
**Cortar campo é tão valioso quanto criar.**

Não altere nenhum arquivo do projeto além da gravação pelo script.
