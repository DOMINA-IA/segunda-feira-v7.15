#!/bin/bash
# =============================================================================
# consolidate.sh — Processo de consolidação ("sono") da memória
# Parte da Camada 1: Memória Profunda (Consciousness Engine)
#
# Analogia: Como o cérebro humano durante o sono, este processo:
# 1. Generaliza episódios repetidos → fatos semânticos
# 2. Extrai heurísticas de padrões → memória procedural
# 3. Fortalece conexões entre episódios relacionados
# 4. Arquiva episódios antigos irrelevantes
# 5. Detecta intenções prospectivas
#
# Uso: ./consolidate.sh [--dry-run] [--agent @dev] [--days 7]
# Recomendado: cron diário às 23:30 (após magic-docs-update)
# =============================================================================

set -euo pipefail

CONSCIOUSNESS_DIR="$HOME/consciousness"
EPISODIC_DIR="$CONSCIOUSNESS_DIR/memory/episodic"
SEMANTIC_FILE="$CONSCIOUSNESS_DIR/memory/semantic/knowledge-graph.json"
PROCEDURAL_FILE="$CONSCIOUSNESS_DIR/memory/procedural/heuristics.jsonl"
PROSPECTIVE_FILE="$CONSCIOUSNESS_DIR/memory/prospective/intentions.json"
CONSOLIDATION_DIR="$CONSCIOUSNESS_DIR/memory/consolidation"
LOG_FILE="$CONSOLIDATION_DIR/consolidation-$(date +%Y-%m-%d).log"
KG_GUARD_LOG="$HOME/logs/knowledge-graph-guard.log"

DRY_RUN=false
TARGET_AGENT=""
DAYS=7

# Parse argumentos
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=true; shift;;
    --agent) TARGET_AGENT="${2#@}"; shift 2;;
    --days) DAYS="$2"; shift 2;;
    *) shift;;
  esac
done

mkdir -p "$CONSOLIDATION_DIR"

log() {
  local msg="[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $1"
  echo "$msg"
  echo "$msg" >> "$LOG_FILE"
}

# ─── GUARD: snapshot + validação do knowledge-graph.json ───────────────────
# Protege contra corrupção do knowledge-graph.json (incidente 2026-05-22:
# arquivo truncado por 46 dias sem detecção). Idempotente: só cria/atualiza o
# snapshot de segurança quando o arquivo atual é JSON válido; nunca sobrescreve
# o snapshot com um estado corrompido.
mkdir -p "$HOME/logs"

kg_is_valid_json() {
  [[ -f "$SEMANTIC_FILE" ]] && python3 -c "import json; json.load(open('$SEMANTIC_FILE'))" 2>/dev/null
}

# Snapshot inicial (uma vez por execução) — só se o estado atual já é válido.
if kg_is_valid_json; then
  cp "$SEMANTIC_FILE" "${SEMANTIC_FILE}.bak"
fi

# Chamar DEPOIS de qualquer escrita em $SEMANTIC_FILE. Se o JSON resultante for
# inválido, restaura o snapshot anterior e loga o erro em $KG_GUARD_LOG (além
# do log de consolidação normal).
validate_kg_or_restore() {
  local step_name="$1"
  if kg_is_valid_json; then
    # Válido — atualiza o snapshot para servir de restore point da próxima escrita
    cp "$SEMANTIC_FILE" "${SEMANTIC_FILE}.bak"
    return 0
  fi

  local ts
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  log "  ERRO GUARD: knowledge-graph.json inválido após '${step_name}'"
  {
    echo "[$ts] GUARD: knowledge-graph.json inválido após '${step_name}'"
  } >> "$KG_GUARD_LOG"

  if [[ -f "${SEMANTIC_FILE}.bak" ]]; then
    cp "${SEMANTIC_FILE}.bak" "$SEMANTIC_FILE"
    log "  GUARD: versão anterior restaurada de ${SEMANTIC_FILE}.bak"
    echo "[$ts] GUARD: restaurado de ${SEMANTIC_FILE}.bak" >> "$KG_GUARD_LOG"
  else
    log "  GUARD: AVISO — nenhum snapshot disponível para restaurar"
    echo "[$ts] GUARD: nenhum snapshot disponível para restaurar" >> "$KG_GUARD_LOG"
  fi
  return 1
}

log "=== CONSOLIDAÇÃO INICIADA ==="
log "Modo: $(if $DRY_RUN; then echo 'DRY-RUN'; else echo 'PRODUÇÃO'; fi)"
log "Período: últimos ${DAYS} dias"
if [[ -n "$TARGET_AGENT" ]]; then
  log "Agente alvo: @${TARGET_AGENT}"
fi

# ─── FASE 1: INVENTÁRIO ─────────────────────────────────────────────
log ""
log "--- Fase 1: Inventário de episódios ---"

TOTAL_EPISODES=0
TOTAL_RAW=0
AGENTS_WITH_EPISODES=()

for EPISODE_FILE in "$EPISODIC_DIR"/*.jsonl; do
  [[ -f "$EPISODE_FILE" ]] || continue
  AGENT_NAME=$(basename "$EPISODE_FILE" .jsonl)

  # Filtrar por agente se especificado
  if [[ -n "$TARGET_AGENT" && "$AGENT_NAME" != "$TARGET_AGENT" ]]; then
    continue
  fi

  COUNT=$(wc -l < "$EPISODE_FILE" | tr -d ' ')
  RAW_COUNT=$(grep -c '"consolidation_status":"raw"' "$EPISODE_FILE" || true)
  RAW_COUNT=${RAW_COUNT:-0}
  RAW_COUNT=$(echo "$RAW_COUNT" | tr -d '[:space:]')

  TOTAL_EPISODES=$((TOTAL_EPISODES + COUNT))
  TOTAL_RAW=$((TOTAL_RAW + RAW_COUNT))
  AGENTS_WITH_EPISODES+=("$AGENT_NAME")

  log "  @${AGENT_NAME}: ${COUNT} episódios (${RAW_COUNT} não processados)"
done

log "Total: ${TOTAL_EPISODES} episódios, ${TOTAL_RAW} não processados"

if [[ $TOTAL_RAW -eq 0 ]]; then
  log "Nenhum episódio novo para consolidar. Encerrando."
  exit 0
fi

# ─── FASE 2: EXTRAÇÃO DE PADRÕES ────────────────────────────────────
log ""
log "--- Fase 2: Extração de padrões recorrentes ---"

PATTERNS_FOUND=0

for AGENT_NAME in "${AGENTS_WITH_EPISODES[@]}"; do
  EPISODE_FILE="$EPISODIC_DIR/${AGENT_NAME}.jsonl"

  # Extrair heurísticas não vazias de episódios raw
  HEURISTICS=$(grep '"consolidation_status":"raw"' "$EPISODE_FILE" | \
    python3 -c "
import sys, json
seen = {}
for line in sys.stdin:
    try:
        ep = json.loads(line.strip())
        h = ep.get('lessons', {}).get('heuristic', '')
        if h and h not in seen:
            seen[h] = {
                'agent': ep.get('agent', ''),
                'type': ep.get('type', ''),
                'result': ep.get('outcome', {}).get('result', ''),
                'valence': ep.get('valence', {}).get('score', 0)
            }
    except: pass
for h, meta in seen.items():
    print(json.dumps({'heuristic': h, 'meta': meta}))
" 2>/dev/null || true)

  if [[ -n "$HEURISTICS" ]]; then
    HEUR_COUNT=$(echo "$HEURISTICS" | wc -l | tr -d ' ')
    log "  @${AGENT_NAME}: ${HEUR_COUNT} heurísticas extraídas"
    PATTERNS_FOUND=$((PATTERNS_FOUND + HEUR_COUNT))
  fi

  # Detectar episódios negativos recorrentes (mesmo tipo de falha)
  RECURRING_FAILURES=$(grep '"consolidation_status":"raw"' "$EPISODE_FILE" | \
    python3 -c "
import sys, json
from collections import Counter
failures = []
for line in sys.stdin:
    try:
        ep = json.loads(line.strip())
        if ep.get('outcome', {}).get('result') == 'failure':
            task = ep.get('context', {}).get('task', 'unknown')
            failures.append(task)
    except: pass
recurring = {k: v for k, v in Counter(failures).items() if v >= 2}
for task, count in recurring.items():
    print(f'ALERTA: @${AGENT_NAME} falhou {count}x em \"{task}\"')
" 2>/dev/null || true)

  if [[ -n "$RECURRING_FAILURES" ]]; then
    log "$RECURRING_FAILURES"
  fi
done

log "Padrões encontrados: ${PATTERNS_FOUND}"

# ─── FASE 2.5: VALIDAÇÃO DE HEURÍSTICAS ─────────────────────────────
log ""
log "--- Fase 2.5: Validação de heurísticas existentes ---"

# Cruza heurísticas existentes com episódios recentes para ajustar confidence
if [[ -f "$PROCEDURAL_FILE" ]]; then
  VALIDATED_COUNT=0
  DEPRECATED_COUNT=0

  if ! $DRY_RUN; then
    # Validação por evidência discriminativa (15-Jul-2026).
    # O bloco anterior extraía as 5 primeiras palavras >4 chars da heurística e
    # contava substring no json.dumps() do episódio inteiro. Como "quando" e
    # "sempre" têm 6 caracteres e abrem quase toda heurística em português,
    # qualquer episódio do agente validava qualquer heurística dele: 89,5% do
    # pool acabou em confidence >=0.9 sem uma única confirmação real.
    # A lógica agora vive em heuristic_validator.py — testável fora do shell.
    read -r V D < <(python3 "$HOME/consciousness/scripts/heuristic_validator.py" --consolidate "$DAYS" 2>/dev/null) || true
    VALIDATED_COUNT=${V:-0}
    DEPRECATED_COUNT=${D:-0}
  fi

  log "  Heurísticas validadas/ajustadas: ${VALIDATED_COUNT}"
  log "  Heurísticas depreciadas (conf<0.3): ${DEPRECATED_COUNT}"
else
  log "  Arquivo de heurísticas não encontrado"
fi

# ─── FASE 3: CONSOLIDAÇÃO SEMÂNTICA ─────────────────────────────────
log ""
log "--- Fase 3: Consolidação semântica ---"

# Extrair fatos de episódios com alta confiança (valência alta + sucesso)
FACTS_EXTRACTED=0

for AGENT_NAME in "${AGENTS_WITH_EPISODES[@]}"; do
  EPISODE_FILE="$EPISODIC_DIR/${AGENT_NAME}.jsonl"

  NEW_FACTS=$(grep '"consolidation_status":"raw"' "$EPISODE_FILE" | \
    python3 -c "
import sys, json
for line in sys.stdin:
    try:
        ep = json.loads(line.strip())
        result = ep.get('outcome', {}).get('result', '')
        valence = ep.get('valence', {}).get('score', 0)
        worked = ep.get('lessons', {}).get('what_worked', '')
        # Fatos de alta confiança: sucesso + valência positiva + lição clara
        if result == 'success' and valence > 0.3 and worked:
            fact = {
                'id': 'fact_' + ep['id'],
                'source': ep['id'],
                'agent': ep.get('agent', ''),
                'statement': worked,
                'confidence': min(0.5 + abs(valence) * 0.3, 0.95),
                'validated_count': 1,
                'created': ep.get('timestamp', ''),
                'category': ep.get('type', 'general')
            }
            print(json.dumps(fact))
    except: pass
" 2>/dev/null || true)

  if [[ -n "$NEW_FACTS" ]]; then
    FACT_COUNT=$(echo "$NEW_FACTS" | wc -l | tr -d ' ')
    FACTS_EXTRACTED=$((FACTS_EXTRACTED + FACT_COUNT))
    log "  @${AGENT_NAME}: ${FACT_COUNT} fatos extraídos"

    if ! $DRY_RUN; then
      # Adicionar fatos ao knowledge graph
      python3 -c "
import json, sys

kg_path = '$SEMANTIC_FILE'
with open(kg_path, 'r') as f:
    kg = json.load(f)

new_facts_text = '''$(echo "$NEW_FACTS")'''
for line in new_facts_text.strip().split('\n'):
    if line:
        try:
            fact = json.loads(line)
            # Evitar duplicatas
            existing_ids = {f['id'] for f in kg['facts']}
            if fact['id'] not in existing_ids:
                kg['facts'].append(fact)
        except: pass

kg['_last_consolidation'] = '$(date -u +"%Y-%m-%dT%H:%M:%SZ")'

with open(kg_path, 'w') as f:
    json.dump(kg, f, indent=2, ensure_ascii=False)
" 2>/dev/null || log "  AVISO: Falha ao gravar knowledge graph"
      validate_kg_or_restore "Fase 3 (fatos — @${AGENT_NAME})"
    fi
  fi
done

log "Fatos extraídos: ${FACTS_EXTRACTED}"

# ─── FASE 3.5: RELAÇÕES ENTRE FATOS ─────────────────────────────────
log ""
log "--- Fase 3.5: Construção de relações no knowledge graph ---"

RELATIONS_CREATED=0

if ! $DRY_RUN && [[ -f "$SEMANTIC_FILE" ]]; then
  RELATIONS_CREATED=$(python3 -c "
import json, re
from datetime import datetime, timezone

kg_path = '$SEMANTIC_FILE'
with open(kg_path) as f:
    kg = json.load(f)

facts = kg.get('facts', [])
existing_rels = set()
for r in kg.get('relationships', []):
    existing_rels.add((r.get('source'), r.get('target')))

def extract_entities(text):
    \"\"\"Extrai entidades mencionáveis de um texto.\"\"\"
    entities = set()
    text_lower = text.lower()
    # Agentes
    agents = re.findall(r'@\w+', text)
    entities.update(a.lower() for a in agents)
    # Keywords de negócio (domínios)
    domains = ['campanha', 'cpl', 'lead', 'criativo', 'angulo', 'ângulo',
               'oferta', 'funil', 'conteudo', 'conteúdo', 'tráfego', 'trafego',
               'meta ads', 'instagram', 'reels', 'whatsapp', 'desafio',
               'rls', 'deploy', 'api', 'webhook', 'sync', 'jsonl', 'feedback']
    for d in domains:
        if d in text_lower:
            entities.add(d)
    return entities

new_relations = []
for i, fact_a in enumerate(facts):
    ents_a = extract_entities(fact_a.get('statement', ''))
    for j, fact_b in enumerate(facts):
        if j <= i:
            continue
        if (fact_a['id'], fact_b['id']) in existing_rels:
            continue
        ents_b = extract_entities(fact_b.get('statement', ''))
        shared = ents_a & ents_b
        if len(shared) >= 1:
            # Determinar tipo de relação
            val_a = fact_a.get('confidence', 0.5)
            val_b = fact_b.get('confidence', 0.5)
            if fact_a.get('agent') == fact_b.get('agent'):
                rel_type = 'same_agent_learning'
            elif shared & {'campanha', 'cpl', 'lead', 'criativo', 'tráfego', 'trafego', 'meta ads'}:
                rel_type = 'campaign_related'
            elif shared & {'conteudo', 'conteúdo', 'angulo', 'ângulo', 'reels', 'instagram'}:
                rel_type = 'content_related'
            else:
                rel_type = 'supports'

            new_relations.append({
                'id': f'rel_{fact_a[\"id\"]}_{fact_b[\"id\"]}',
                'source': fact_a['id'],
                'target': fact_b['id'],
                'type': rel_type,
                'shared_entities': list(shared),
                'strength': min(val_a, val_b),
                'created': datetime.now(timezone.utc).isoformat() + 'Z'
            })

if new_relations:
    if 'relationships' not in kg:
        kg['relationships'] = []
    kg['relationships'].extend(new_relations)
    kg['_last_consolidation'] = datetime.now(timezone.utc).isoformat() + 'Z'
    with open(kg_path, 'w') as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)

print(len(new_relations))
" 2>/dev/null || echo 0)

  log "  Relações criadas: ${RELATIONS_CREATED}"
  if [[ "$RELATIONS_CREATED" -gt 0 ]]; then
    validate_kg_or_restore "Fase 3.5 (relações)"
  fi
else
  log "  [DRY-RUN ou knowledge graph ausente] Relações não criadas"
fi

# ─── FASE 4: MARCAR COMO PROCESSADOS ────────────────────────────────
log ""
log "--- Fase 4: Marcando episódios como processados ---"

if ! $DRY_RUN; then
  for AGENT_NAME in "${AGENTS_WITH_EPISODES[@]}"; do
    EPISODE_FILE="$EPISODIC_DIR/${AGENT_NAME}.jsonl"

    if [[ -f "$EPISODE_FILE" ]]; then
      # Marcar raw → processed
      sed -i.bak 's/"consolidation_status":"raw"/"consolidation_status":"processed"/g' "$EPISODE_FILE"
      rm -f "${EPISODE_FILE}.bak"
      log "  @${AGENT_NAME}: episódios marcados como processados"
    fi
  done
else
  log "  [DRY-RUN] Nenhuma alteração feita"
fi

# ─── FASE 4.5: EXPORTAR FATOS → CORTEX VAULT ────────────────────────
log ""
log "--- Fase 4.5: Exportar fatos de alta confiança para CORTEX vault ---"

CORTEX_VAULT="$HOME/cortex/vault"
FACTS_EXPORTED=0

if ! $DRY_RUN && [[ -f "$SEMANTIC_FILE" ]]; then
  FACTS_EXPORTED=$(python3 -c "
import json, os, re
from datetime import datetime, timezone
from pathlib import Path

kg_path = '$SEMANTIC_FILE'
vault_dir = Path('$CORTEX_VAULT')
tracker_path = Path('$CONSOLIDATION_DIR') / '.exported-facts.json'

with open(kg_path) as f:
    kg = json.load(f)

# Carregar tracker de fatos já exportados
exported_ids = set()
if tracker_path.exists():
    with open(tracker_path) as f:
        try:
            exported_ids = set(json.load(f).get('exported', []))
        except:
            pass

facts = kg.get('facts', [])
new_exports = 0

for fact in facts:
    fid = fact.get('id', '')
    confidence = fact.get('confidence', 0)
    statement = fact.get('statement', '')
    agent = fact.get('agent', '@unknown')
    category = fact.get('category', 'general')

    # Só exportar fatos com confiança >= 0.7 e não exportados
    if confidence < 0.7 or fid in exported_ids or not statement:
        continue

    # Gerar slug para o arquivo
    agent_clean = agent.replace('@', '')
    slug_base = re.sub(r'[^a-z0-9]+', '-', statement[:60].lower()).strip('-')
    slug = f'consciousness-{agent_clean}-{slug_base}'
    note_path = vault_dir / 'consciousness' / f'{slug}.md'

    # Garantir diretório
    note_path.parent.mkdir(parents=True, exist_ok=True)

    # Determinar domínio e tags
    domain = agent_clean
    tags = [category, 'consciousness-export', 'auto-generated']

    # Criar nota CORTEX
    today = datetime.now().strftime('%Y-%m-%d')
    content = f'''---
title: \"{statement[:80]}\"
type: feedback
domain:
  - {domain}
agents:
  - '{agent}'
tags:
  - {' '.join(f'\\n  - '.join('' for _ in range(0)))}{'\\n  - '.join(tags)}
freshness_score: 0.9
verified: true
created: {today}
last_verified: {today}
links:
  - target: consciousness-facts
    type: generated_from
---

# {statement[:80]}

**Origem:** Consciousness Engine (consolidação automática)
**Confiança:** {confidence:.2f}
**Agente:** {agent}
**Categoria:** {category}
**Data:** {fact.get('created', 'N/A')[:10]}

## Fato

{statement}

## Contexto

Extraído automaticamente do episódio {fact.get('source', 'N/A')} durante a consolidação noturna.
Validado {fact.get('validated_count', 1)}x pelo processo de consolidação.
'''

    note_path.write_text(content)
    exported_ids.add(fid)
    new_exports += 1

# Salvar tracker
with open(tracker_path, 'w') as f:
    json.dump({'exported': list(exported_ids), 'last_export': datetime.now(timezone.utc).isoformat()}, f, indent=2)

print(new_exports)
" 2>/dev/null || echo 0)

  log "  Fatos exportados para CORTEX vault: ${FACTS_EXPORTED}"
else
  log "  [DRY-RUN ou knowledge graph ausente] Exportação não realizada"
fi

# ─── FASE 5: RELATÓRIO ──────────────────────────────────────────────
log ""
log "=== CONSOLIDAÇÃO COMPLETA ==="
log "Resumo:"
log "  Agentes processados: ${#AGENTS_WITH_EPISODES[@]}"
log "  Episódios analisados: ${TOTAL_RAW}"
log "  Padrões extraídos: ${PATTERNS_FOUND}"
log "  Fatos consolidados: ${FACTS_EXTRACTED}"
log "  Log: ${LOG_FILE}"

# Emitir sinal de consolidação completa
if ! $DRY_RUN && [[ -f "$HOME/broadcast/signals.json" ]]; then
  python3 -c "
import json
from datetime import datetime

sig_path = '$HOME/broadcast/signals.json'
with open(sig_path, 'r') as f:
    signals = json.load(f)

new_signal = {
    'id': 'sig_consolidation_$(date +%Y%m%d)',
    'type': 'CONSOLIDATION_COMPLETE',
    'from': '@consciousness',
    'data': {
        'episodes_processed': $TOTAL_RAW,
        'patterns_found': $PATTERNS_FOUND,
        'facts_extracted': $FACTS_EXTRACTED,
        'agents': $(python3 -c "import json; print(json.dumps([a for a in '${AGENTS_WITH_EPISODES[*]}'.split()]))" 2>/dev/null || echo '[]')
    },
    'confidence': 0.95,
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'consumed_by': [],
    'ttl_days': 3
}

if isinstance(signals, list):
    signals.append(new_signal)
elif isinstance(signals, dict):
    signals.setdefault('active_signals', []).append(new_signal)

with open(sig_path, 'w') as f:
    json.dump(signals, f, indent=2, ensure_ascii=False)
" 2>/dev/null && log "Sinal CONSOLIDATION_COMPLETE emitido" || true
fi
