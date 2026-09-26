#!/bin/bash
# Enquanto a coleta de comentários roda (pid 84560), passa o moinho a cada 30 min
# no que já chegou; quando ela termina, uma passada final e sai. Sem vigia eterno.
cd /Users/fitipe/Desktop/arte_c_joao_tta/escuta_planetaria/moinho
L=/tmp/moer_comentarios.log
while kill -0 84560 2>/dev/null; do
  echo "$(date '+%d/%m %H:%M') moinho (coleta ainda rodando)" >> $L
  python3 -u moinho.py --bert >> $L 2>&1
  sleep 1800
done
echo "$(date '+%d/%m %H:%M') coleta terminou — passada final" >> $L
python3 -u moinho.py --bert >> $L 2>&1
echo "$(date '+%d/%m %H:%M') ★ fim: comentários moídos" >> $L
