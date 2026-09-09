#!/bin/bash
# Lembrete único: revisar Consciousness Engine após 5 dias de dados reais
# Auto-deleta após execução

TELEGRAM_BOT_TOKEN=$(cat ~/.telegram-bot-token 2>/dev/null || echo "")
TELEGRAM_CHAT_ID=$(cat ~/.telegram-chat-id 2>/dev/null || echo "")

MESSAGE="🧠 *Consciousness Engine — Hora de Revisar*

Já se passaram 5 dias desde a implementação.

*Checklist:*
- Quantos episódios reais foram registrados?
- Quais heurísticas surgiram?
- O knowledge graph cresceu?
- Houve ignições no workspace global?

*Comando rápido:*
\`\`\`
~/consciousness/scripts/workspace.sh status
~/consciousness/scripts/reflect.sh --agent @dev
~/consciousness/scripts/reflect.sh --agent @traffic
\`\`\`

Abra o Claude Code e diga:
*\"Vamos revisar o Consciousness Engine — analisar dados reais e decidir se automatizamos\"*"

if [[ -n "$TELEGRAM_BOT_TOKEN" && -n "$TELEGRAM_CHAT_ID" ]]; then
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d chat_id="$TELEGRAM_CHAT_ID" \
    -d text="$MESSAGE" \
    -d parse_mode="Markdown" > /dev/null 2>&1
  echo "[$(date)] Lembrete Consciousness Engine enviado via Telegram"
else
  echo "[$(date)] AVISO: Token ou chat_id do Telegram não encontrados"
  echo "Mensagem: $MESSAGE"
fi

# Auto-remover do crontab após execução
crontab -l 2>/dev/null | grep -v "consciousness-reminder" | crontab -
echo "[$(date)] Cron de lembrete auto-removido"
