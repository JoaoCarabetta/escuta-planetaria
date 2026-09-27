# Página V3 — o que entra (lista viva)

## Dados (da anotação v3.5 / aluno novo)
- forma do texto: post · comentário · continuação (bit no pontos.bin + tag + filtro)
- tags clicáveis: carga, despertar, atribuição (palavra, origem, quem), figura
- datas (filtro/linha do tempo)
- cargas combinadas exibidas em PORCENTAGEM (ex.: estranha + prazerosa)
- conversa em torno do post (tabela `vinculos`), talvez
- cuidado.json continua valendo (bandeira + cuidado_manual)

## Navegação — pedidos do Fitipe (27/09)
1. **Zoom no desktop perde o alvo.** Hoje cada volta da roda gira o globo
   rumo ao ponto que está sob o cursor NAQUELE instante (`girarParaTela` em
   index.html ~l.661, chamado no `wheel` ~l.733). Como o globo gira, outro
   ponto passa a estar sob o cursor e vira o novo alvo — o zoom "escorrega".
   Conserto: no primeiro evento de roda de um gesto, guardar o ponto 3D
   (em coordenadas do globo) que está sob o cursor; os eventos seguintes
   giram rumo à projeção ATUAL desse ponto guardado. Soltar o alvo quando o
   mouse se mover (> ~6 px) ou após ~700 ms sem roda.
2. **Mobile: pinça dá zoom na PÁGINA inteira**, e os menus/busca crescem
   junto. O canvas tem `touch-action:none`, mas os painéis não, e o meta
   viewport não trava a escala (e o iOS ignora `user-scalable=no`).
   Conserto: `touch-action:none` no body/painéis (manipulation nos
   controles), bloquear `gesturestart`/`gesturechange` no iOS, e tratar a
   pinça sempre no canvas.
3. **Mobile: depois de desfazer o zoom da página, o globo fica cortado no
   canto superior esquerdo com faixas pretas.** O `medir()` (~l.378) lê
   `innerWidth/innerHeight` enquanto o viewport visual ainda está escalado.
   Conserto: medir por `visualViewport` (e ouvir `visualViewport.resize`),
   canvas em `100dvw/100dvh`, remedir ao voltar a escala 1.
4. **Mobile: a ficha do relato cobre a busca e os resultados.** Conserto:
   ficha como folha de baixo (bottom sheet) arrastável, ou esconder os
   resultados enquanto a ficha está aberta, com um "voltar aos resultados".
