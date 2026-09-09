#!/bin/bash
# =============================================================================
# record-episode.sh — Registra episódio na memória episódica de um agente
# Parte da Camada 1: Memória Profunda (Consciousness Engine)
#
# Uso:
#   ./record-episode.sh --agent "@dev" --type "task_completed" \
#     --summary "Implementou RLS no módulo de pagamentos" \
#     --result "success" --valence 0.7 --intensity 0.5 \
#     --worked "Consultar @data-engineer antes salvou tempo" \
#     --failed "" \
#     --heuristic "Quando story envolve RLS, pré-consultar @data-engineer" \
#     [--story "3.2"] [--task "Implementar RLS"] [--duration 45] \
#     [--participants "@data-engineer,@qa"] \
#     [--heuristic-failed "heur_20260406030036_0a905cc9cc"] \
#     [--heuristic-applied "heur_20260414162141"]
#
# O episódio é gravado em ~/consciousness/memory/episodic/{agent}.jsonl
#
# --heuristic-applied {id} (15-Jul-2026 — evidência DECLARADA)
#   Declara que esta tarefa aplicou a heurística {id}. É a única evidência que
#   leva confidence acima de 0.85: o validador infere match por texto, mas texto
#   parecido não prova aplicação. Se o episódio termina em success, a heurística
#   sobe +0.08; se termina em failure, cai. Use quando o boot context injetou uma
#   heurística e você de fato agiu por ela.
#
# --heuristic-failed {id_ou_texto_parcial} (Sprint 3 Grupo B — contra-evidência)
#   Registra que uma heurística existente FALHOU nesta execução, ADITIVO ao
#   registro normal do episódio acima (não substitui --heuristic, que continua
#   servindo para heurísticas NOVAS extraídas do episódio). Localiza a
#   heurística em heuristics.jsonl por id exato; se não achar, cai para
#   substring (case-insensitive) no campo "heuristic". Incrementa
#   "times_failed", reduz "confidence" em 0.15 (piso 0.1) e grava
#   "last_failed". Se o texto bater em mais de uma heurística, nada é alterado
#   (evita enfraquecer a heurística errada) — seja mais específico.
# =============================================================================

set -euo pipefail

EPISODIC_DIR="$HOME/consciousness/memory/episodic"
PROCEDURAL_FILE="$HOME/consciousness/memory/procedural/heuristics.jsonl"

# Defaults
AGENT=""
TYPE="task_completed"
SUMMARY=""
RESULT="success"
VALENCE=0.0
INTENSITY=0.5
WORKED=""
FAILED=""
HEURISTIC=""
STORY=""
TASK=""
DURATION=0
PARTICIPANTS=""
METRICS="{}"
HEURISTIC_FAILED=""
HEURISTIC_APPLIED=""

# Parse argumentos
while [[ $# -gt 0 ]]; do
  case $1 in
    --agent) AGENT="$2"; shift 2;;
    --type) TYPE="$2"; shift 2;;
    --summary) SUMMARY="$2"; shift 2;;
    --result) RESULT="$2"; shift 2;;
    --valence) VALENCE="$2"; shift 2;;
    --intensity) INTENSITY="$2"; shift 2;;
    --worked) WORKED="$2"; shift 2;;
    --failed) FAILED="$2"; shift 2;;
    --heuristic) HEURISTIC="$2"; shift 2;;
    --story) STORY="$2"; shift 2;;
    --task) TASK="$2"; shift 2;;
    --duration) DURATION="$2"; shift 2;;
    --participants) PARTICIPANTS="$2"; shift 2;;
    --metrics) METRICS="$2"; shift 2;;
    --heuristic-failed) HEURISTIC_FAILED="$2"; shift 2;;
    --heuristic-applied) HEURISTIC_APPLIED="$2"; shift 2;;
    *) echo "Argumento desconhecido: $1"; exit 1;;
  esac
done

# Validação
if [[ -z "$AGENT" || -z "$SUMMARY" ]]; then
  echo "Erro: --agent e --summary são obrigatórios"
  echo "Uso: ./record-episode.sh --agent '@dev' --summary 'Descrição do evento'"
  exit 1
fi

# Limpar nome do agente (remover @)
AGENT_CLEAN="${AGENT#@}"

# Gerar ID e timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
DATE_COMPACT=$(date -u +"%Y%m%d%H%M%S")
EP_ID="ep_${AGENT_CLEAN}_${DATE_COMPACT}"

# Determinar label da valência
if (( $(echo "$VALENCE > 0.3" | bc -l) )); then
  VALENCE_LABEL="positive"
elif (( $(echo "$VALENCE < -0.3" | bc -l) )); then
  VALENCE_LABEL="negative"
else
  VALENCE_LABEL="neutral"
fi

# Converter participants para array JSON
if [[ -n "$PARTICIPANTS" ]]; then
  PARTICIPANTS_JSON=$(echo "$PARTICIPANTS" | tr ',' '\n' | sed 's/^/"/;s/$/"/' | tr '\n' ',' | sed 's/,$//')
  PARTICIPANTS_JSON="[$PARTICIPANTS_JSON]"
else
  PARTICIPANTS_JSON="[]"
fi

# Construir episódio JSON
EPISODE=$(cat <<EOF
{"id":"${EP_ID}","agent":"@${AGENT_CLEAN}","timestamp":"${TIMESTAMP}","type":"${TYPE}","summary":"${SUMMARY}","context":{"story_id":"${STORY}","task":"${TASK}","participants":${PARTICIPANTS_JSON},"duration_minutes":${DURATION}},"outcome":{"result":"${RESULT}","metrics":${METRICS}},"valence":{"score":${VALENCE},"label":"${VALENCE_LABEL}","intensity":${INTENSITY},"reason":"${WORKED}${FAILED:+ | Falha: $FAILED}"},"lessons":{"what_worked":"${WORKED}","what_failed":"${FAILED}","heuristic":"${HEURISTIC}","heuristic_applied":"${HEURISTIC_APPLIED}","heuristic_failed":"${HEURISTIC_FAILED}"},"consolidation_status":"raw"}
EOF
)

# Garantir diretório existe
mkdir -p "$EPISODIC_DIR"

# Gravar episódio (append JSONL)
echo "$EPISODE" >> "${EPISODIC_DIR}/${AGENT_CLEAN}.jsonl"

# Se tem heurística, registrar também na memória procedural
if [[ -n "$HEURISTIC" ]]; then
  HEUR_ENTRY=$(cat <<EOF
{"id":"heur_${DATE_COMPACT}","source_episode":"${EP_ID}","agent":"@${AGENT_CLEAN}","heuristic":"${HEURISTIC}","confidence":0.5,"times_validated":1,"created":"${TIMESTAMP}","last_validated":"${TIMESTAMP}"}
EOF
)
  echo "$HEUR_ENTRY" >> "$PROCEDURAL_FILE"
  echo "  + Heurística registrada: ${HEURISTIC}"
fi

# ─── FEEDBACK DE HEURÍSTICA — loop fechado em 05-Set-2026 ──────────────────
# Até aqui só a contra-evidência atualizava a heurística. --heuristic-applied era
# gravado no episódio (lessons.heuristic_applied) e NUNCA tocava heuristics.jsonl:
# em 630 episódios o campo foi preenchido 1 vez, e mesmo essa não moveu nada.
# Resultado medido: times_failed=0 em TODAS as 1.034 e times_validated travado em 1
# para 1.029 — justamente o campo de que o gate de promoção dependia.
# A lógica agora vive em heuristic_feedback.py, testável fora do shell.
aplicar_feedback() {   # $1 = needle (id ou fragmento)  $2 = success|failure
  local needle="$1" outcome="$2" flag="$3" res
  [[ -z "$needle" ]] && return 0
  if [[ ! -f "$PROCEDURAL_FILE" ]]; then
    echo "  ! AVISO: heuristics.jsonl não encontrado — ${flag} ignorado"
    return 0
  fi
  res=$(python3 "$HOME/consciousness/scripts/heuristic_feedback.py" \
        "$PROCEDURAL_FILE" "$needle" "$outcome" "$TIMESTAMP" 2>/dev/null)
  case "$res" in
    OK:*)
      IFS=':' read -r _ H_ID H_OLD H_NEW H_CAMPO <<< "$res"
      local seta="✓"; [[ "$outcome" == "failure" ]] && seta="✗"
      echo "  ${seta} Heurística ${H_ID}: confidence ${H_OLD} → ${H_NEW} | ${H_CAMPO}"
      ;;
    AMBIGUOUS:*)
      echo "  ! AVISO: '${flag} ${needle}' bateu em mais de uma heurística — use o id. Candidatos: ${res#AMBIGUOUS:}"
      ;;
    NOT_FOUND)
      echo "  ! AVISO: nenhuma heurística encontrada para '${flag} ${needle}'"
      ;;
    *)
      echo "  ! ERRO ao processar ${flag} (saída: ${res:-vazia})"
      ;;
  esac
}

aplicar_feedback "$HEURISTIC_APPLIED" success "--heuristic-applied"
aplicar_feedback "$HEURISTIC_FAILED"  failure "--heuristic-failed"

echo "Episódio registrado: ${EP_ID}"
echo "  Agente: @${AGENT_CLEAN}"
echo "  Tipo: ${TYPE}"
echo "  Resultado: ${RESULT}"
echo "  Valência: ${VALENCE} (${VALENCE_LABEL}, intensidade ${INTENSITY})"
echo "  Arquivo: ${EPISODIC_DIR}/${AGENT_CLEAN}.jsonl"

# =============================================================================
# AUTO-REFRESH BRIEFINGS (Absorção #5 — inspirado em Devin Wiki)
# A cada 5 episódios novos por agente, regenera briefings automaticamente.
# Override: AUTO_REFRESH_THRESHOLD env var. Skip: AUTO_REFRESH_DISABLED=1.
# =============================================================================
if [[ "${AUTO_REFRESH_DISABLED:-0}" != "1" ]]; then
  THRESHOLD="${AUTO_REFRESH_THRESHOLD:-5}"
  COUNTER_DIR="$HOME/cortex/.briefing-counters"
  mkdir -p "$COUNTER_DIR"
  COUNTER_FILE="$COUNTER_DIR/${AGENT_CLEAN}.count"

  CURRENT_COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
  [[ "$CURRENT_COUNT" =~ ^[0-9]+$ ]] || CURRENT_COUNT=0
  CURRENT_COUNT=$((CURRENT_COUNT + 1))
  echo "$CURRENT_COUNT" > "$COUNTER_FILE"

  if [[ $CURRENT_COUNT -ge $THRESHOLD ]]; then
    echo "  🔄 Auto-refresh briefings disparado (${CURRENT_COUNT} episódios desde último refresh)"
    if python3 "$HOME/cortex/scripts/cortex_engine.py" build-briefings >/dev/null 2>&1; then
      echo "  ✅ Briefings regenerados — counter @${AGENT_CLEAN} resetado"
      echo 0 > "$COUNTER_FILE"
    else
      echo "  ⚠️  Falha ao regenerar briefings (counter mantido em ${CURRENT_COUNT})"
    fi
  fi
fi
