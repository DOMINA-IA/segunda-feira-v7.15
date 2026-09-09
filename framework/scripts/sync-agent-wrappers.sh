#!/usr/bin/env bash
# sync-agent-wrappers.sh — Sincroniza wrappers de ativação conversacional
# (~/.claude/commands/segunda-feira/agents/*.md) a partir das fontes canônicas
# (~/.claude/agents/{meta,ops}/*.md) para agentes de dupla camada.
#
# Dupla camada = wrapper termina com o rodapé:
#   <!-- DERIVADO de <path-canonico> em <YYYY-MM-DD> [(sha256:<hash>)] — NÃO editar aqui; editar a fonte canônica e re-sincronizar -->
# O script detecta dinamicamente QUAIS wrappers têm esse rodapé — não há lista
# hardcoded de agentes. Wrappers sem rodapé (camada única) são ignorados.
#
# Uso:
#   sync-agent-wrappers.sh --check                 # reporta divergências; exit 1 se houver (uso em health check)
#   sync-agent-wrappers.sh --sync                   # regenera todos os wrappers de dupla camada
#   sync-agent-wrappers.sh --sync <nome-do-agente>   # regenera só um (ex.: dev, analyst, video-producer)
#
# --sync preserva:
#   1. O frontmatter próprio do wrapper (bloco entre os dois primeiros '---')
#   2. O rodapé DERIVADO (path canônico preservado, data e hash sha256 atualizados)
# O corpo é substituído pelo corpo do canônico (removendo o frontmatter próprio
# do canônico e qualquer comentário HTML "<!-- RECONCILIAÇÃO..." que só faz
# sentido na fonte, não na cópia derivada).
set -euo pipefail

WRAPPERS_DIR="$HOME/.claude/commands/segunda-feira/agents"

usage() {
  echo "Uso: $(basename "$0") --check | --sync [nome-do-agente]" >&2
  exit 2
}

if [[ $# -eq 0 ]]; then
  usage
fi

MODE=""
case "$1" in
  --check) MODE="check" ;;
  --sync)  MODE="sync" ;;
  *) usage ;;
esac
shift
TARGET="${1:-}"

if [[ ! -d "$WRAPPERS_DIR" ]]; then
  echo "ERRO: diretório de wrappers não encontrado: $WRAPPERS_DIR" >&2
  exit 2
fi

# ── extrai "path|data|hash" do rodapé DERIVADO de um wrapper ────────────────
# return 1 se o wrapper não tiver rodapé DERIVADO (camada única).
extract_footer() {
  local wrapper="$1" line path date hash
  line=$(grep -m1 -- "DERIVADO de" "$wrapper" || true)
  if [[ -z "$line" ]]; then
    return 1
  fi
  path=$(printf '%s\n' "$line" | sed -E 's/.*DERIVADO de ([^[:space:]]+) em.*/\1/')
  date=$(printf '%s\n' "$line" | sed -E 's/.*em ([0-9]{4}-[0-9]{2}-[0-9]{2}).*/\1/')
  hash=$(printf '%s\n' "$line" | sed -E 's/.*sha256:([0-9a-f]+).*/\1/')
  if [[ "$hash" == "$line" ]]; then
    hash=""
  fi
  printf '%s|%s|%s\n' "$path" "$date" "$hash"
  return 0
}

# ── checa um wrapper. Ecoa "AGENTE|motivo" no stdout. ────────────────────────
# return: 0=OK, 1=DIVERGENTE, 2=SKIP (camada única)
check_one() {
  local wrapper="$1" agent footer canonical_path sync_date stored_hash
  agent=$(basename "$wrapper" .md)

  if ! footer=$(extract_footer "$wrapper"); then
    return 2
  fi

  IFS='|' read -r canonical_path sync_date stored_hash <<< "$footer"

  if [[ ! -f "$canonical_path" ]]; then
    printf '%s|canônico ausente: %s\n' "$agent" "$canonical_path"
    return 1
  fi

  local wrapper_mtime canonical_mtime
  wrapper_mtime=$(stat -f %m "$wrapper")
  canonical_mtime=$(stat -f %m "$canonical_path")

  if [[ -n "$stored_hash" ]]; then
    local current_hash
    current_hash=$(shasum -a 256 "$canonical_path" | awk '{print $1}')
    if [[ "$current_hash" == "$stored_hash" ]]; then
      printf '%s|hash sha256 confere (sincronizado em %s)\n' "$agent" "$sync_date"
      return 0
    else
      printf '%s|conteúdo do canônico mudou desde a sincronização de %s (hash difere) — rode --sync %s\n' "$agent" "$sync_date" "$agent"
      return 1
    fi
  fi

  # rodapé legado sem hash — cai para comparação por mtime
  if (( canonical_mtime > wrapper_mtime )); then
    printf '%s|canônico modificado após o wrapper (mtime canônico > wrapper), sem hash no rodapé — rode --sync %s\n' "$agent" "$agent"
    return 1
  else
    printf '%s|mtime consistente (wrapper >= canônico), sincronizado em %s — rodapé legado sem hash\n' "$agent" "$sync_date"
    return 0
  fi
}

# ── regenera um wrapper a partir do canônico ─────────────────────────────────
# return: 0=sincronizado, 1=erro, 2=skip (camada única)
sync_one() {
  local wrapper="$1" agent footer canonical_path
  agent=$(basename "$wrapper" .md)

  if ! footer=$(extract_footer "$wrapper"); then
    printf '%s|sem rodapé DERIVADO — camada única, nada a sincronizar\n' "$agent"
    return 2
  fi

  local sync_date stored_hash
  IFS='|' read -r canonical_path sync_date stored_hash <<< "$footer"

  if [[ ! -f "$canonical_path" ]]; then
    printf '%s|ERRO: canônico ausente: %s — sync abortado\n' "$agent" "$canonical_path"
    return 1
  fi

  # 1. Frontmatter próprio do wrapper (bloco entre os dois primeiros '---')
  local frontmatter
  frontmatter=$(awk '
    NR==1 && $0=="---" { infm=1; print; next }
    infm==1 && $0=="---" { print; exit }
    infm==1 { print }
  ' "$wrapper")

  if [[ -z "$frontmatter" ]]; then
    printf '%s|ERRO: wrapper sem bloco frontmatter "---" — sync abortado\n' "$agent"
    return 1
  fi

  # 2. Corpo do canônico: remove o frontmatter próprio do canônico (se houver)
  #    e qualquer linha de comentário "<!-- RECONCILIAÇÃO..." (nota exclusiva
  #    da fonte, não faz sentido na cópia derivada).
  local canonical_body
  canonical_body=$(awk '
    NR==1 && $0=="---" { infm=1; next }
    infm==1 && $0=="---" { infm=0; next }
    infm==1 { next }
    { print }
  ' "$canonical_path" | sed '/^<!-- RECONCILIA/d' | sed '/./,$!d')

  # 3. Novo rodapé DERIVADO, path canônico preservado, data e hash atualizados
  local today hash footer_line
  today=$(date +%Y-%m-%d)
  hash=$(shasum -a 256 "$canonical_path" | awk '{print $1}')
  footer_line="<!-- DERIVADO de $canonical_path em $today (sha256:$hash) — NÃO editar aqui; editar a fonte canônica e re-sincronizar -->"

  local tmpfile
  tmpfile=$(mktemp "${TMPDIR:-/tmp}/sync-agent-wrapper.XXXXXX")
  {
    printf '%s\n' "$frontmatter"
    echo
    printf '%s\n' "$canonical_body"
    echo
    printf '%s\n' "$footer_line"
  } > "$tmpfile"

  mv "$tmpfile" "$wrapper"
  printf '%s|regenerado a partir de %s (sha256:%s)\n' "$agent" "$canonical_path" "${hash:0:12}..."
  return 0
}

# ── coleta a lista de wrappers a processar ──────────────────────────────────
wrappers=()
if [[ -n "$TARGET" ]]; then
  candidate="$WRAPPERS_DIR/$TARGET.md"
  if [[ ! -f "$candidate" ]]; then
    echo "ERRO: wrapper não encontrado para agente '$TARGET': $candidate" >&2
    exit 2
  fi
  wrappers=("$candidate")
else
  while IFS= read -r -d '' f; do
    wrappers+=("$f")
  done < <(find "$WRAPPERS_DIR" -maxdepth 1 -name '*.md' -print0 | sort -z)
fi

processed=0
divergent=0

if [[ "$MODE" == "check" ]]; then
  echo "═══ sync-agent-wrappers --check ═══"
  for w in "${wrappers[@]}"; do
    if line=$(check_one "$w"); then
      rc=0
    else
      rc=$?
    fi
    if [[ $rc -eq 2 ]]; then
      if [[ -n "$TARGET" ]]; then
        echo "ℹ️  $(basename "$w" .md): camada única (sem rodapé DERIVADO) — nada a verificar"
      fi
      continue
    fi
    processed=$((processed + 1))
    agent="${line%%|*}"
    reason="${line#*|}"
    if [[ $rc -eq 0 ]]; then
      echo "✅ $agent: $reason"
    else
      echo "⚠️  $agent: $reason"
      divergent=$((divergent + 1))
    fi
  done
  echo ""
  echo "$processed wrapper(s) de dupla camada verificados | $divergent divergência(s)"
  if [[ $divergent -gt 0 ]]; then
    exit 1
  fi
  exit 0

else
  echo "═══ sync-agent-wrappers --sync ═══"
  for w in "${wrappers[@]}"; do
    if line=$(sync_one "$w"); then
      rc=0
    else
      rc=$?
    fi
    if [[ $rc -eq 2 ]]; then
      if [[ -n "$TARGET" ]]; then
        echo "ℹ️  $(basename "$w" .md): camada única (sem rodapé DERIVADO) — nada a sincronizar"
      fi
      continue
    fi
    processed=$((processed + 1))
    agent="${line%%|*}"
    reason="${line#*|}"
    if [[ $rc -eq 0 ]]; then
      echo "✅ $agent: $reason"
    else
      echo "❌ $agent: $reason"
      divergent=$((divergent + 1))
    fi
  done
  echo ""
  echo "$processed wrapper(s) sincronizados | $divergent erro(s)"
  if [[ $divergent -gt 0 ]]; then
    exit 1
  fi
  exit 0
fi
