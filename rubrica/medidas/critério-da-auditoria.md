# O critério da auditoria dos 2 mil — fixado antes de medir

*24/09/2026, antes de qualquer auditoria rodar. Está escrito aqui porque
critério decidido depois do resultado não é critério: é justificativa.*

O Fitipe autorizou treinar o BERTimbau enquanto dorme **se a auditoria passar
no teste**. Isto é o teste.

## O que se mede

Sessenta relatos sorteados do material de treino, relidos às cegas por dois
anotadores novos, que não veem o julgamento original nem o um do outro. Três
julgamentos por texto, como na amostra-prova.

## O que é passar

**Concordância no portão de 88% ou mais**, contada como igualdade exata dos
valores de portão entre os pares.

A régua vem da amostra-prova, onde três leituras cegas deram **93%**. O material
de treino vem das bolsas por palavra, que foram montadas para conter o caso
difícil — é esperado que concorde um pouco menos que um sorteio uniforme. Cinco
pontos de folga cobrem isso sem virar complacência.

**Abaixo de 88%, não treino.** Não porque o treino falharia, mas porque o
resultado não significaria nada: um classificador não pode ser mais consistente
que os julgamentos que o ensinaram, e treinar em material com um em cada oito
textos em disputa produziria um modelo que herda a disputa sem que a gente saiba
onde ela está.

Se falhar, o que faço em vez de treinar: separo os casos divergentes, vejo se a
divergência tem padrão — quase sempre tem, e quase sempre é um campo mal
definido, não um leitor desatento — e escrevo o aperto de definição
correspondente. Foi o que aconteceu com a ironia, com a falta de contexto e com
o `nao_dito`, três vezes seguidas nesta noite.

## O que NÃO é critério de passar

Não uso `carga`, `tom` nem `sonhador` como porteiros. O tom já foi medido em
**75%** na amostra-prova e a causa é conhecida (a rubrica define `leve` e não
define `seco`); reprovar o treino por isso seria reprovar por um defeito que já
está diagnosticado e cujo conserto é de definição, não de dados. Esses campos
entram com o teto medido ao lado, e o relatório do treino dirá para cada um o
que é honesto esperar.

## Registro de escopo

Se a auditoria passar, treino e deixo pronto: pesos, histórico por época, e a
medição contra os três conjuntos — validação, amostra-prova e os 70 do Fitipe,
cada um com a sua linha de base de classe majoritária.

O teste nos 5 mil textos e a auditoria da amostra desse teste vêm depois do
treino, como ele pediu, e com anotadores Opus.
