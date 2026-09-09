#!/bin/bash
# =============================================================================
# heuristic-promote.sh — Promoção formal de heurística a rule on-demand
# Parte da Camada 1: Memória Profunda (Consciousness Engine) — Sprint 3 Grupo B
#
# Heurística que já provou seu valor repetidas vezes (muitas validações, alta
# confidence, nunca contradita a ponto de virar "review") é candidata a virar
# rule formal do framework — mas isso é decisão do CEO, não do agente. Este
# script NÃO cria a rule: ele gera uma PROPOSTA em
# ~/consciousness/proposals/promote-{id}-{data}.md com a heurística, a
# evidência e um frontmatter sugerido para a futura rule on-demand.
#
# Critério de candidatura:
#   - times_validated >= 30
#   - confidence >= 0.85
#   - status != "review" (heurística sob suspeita não é promovida)
#   - ainda não promovida nem proposta: sem "promoted_to_rule" (campo usado
#     por promoções manuais anteriores, ver heuristics.jsonl) e sem
#     "promotion_proposed" (marcado por este script — evita propor de novo
#     toda semana a mesma heurística)
#   - não arquivada ("archived" ausente/false)
#
# Ao gerar uma proposta, marca "promotion_proposed": "<data>" na heurística
# (escrita atômica: temp + mv). Se houver notificação Telegram configurada
# (helper notify() de ~/autonomous/lib/common.sh, já usado pelo Autonomous
# Engine), envia UM aviso agregado (nunca um por heurística — evita spam).
#
# Uso: ./heuristic-promote.sh
# Recomendado: cron semanal (segunda 07:50 BRT, após heuristic-decay.sh —
# ver crontab)
# =============================================================================

set -euo pipefail

PROCEDURAL_FILE="$HOME/consciousness/memory/procedural/heuristics.jsonl"
PROPOSALS_DIR="$HOME/consciousness/proposals"
COMMON_LIB="$HOME/autonomous/lib/common.sh"

log() {
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $1"
}

if [[ ! -f "$PROCEDURAL_FILE" ]]; then
  log "ERRO: arquivo de heurísticas não encontrado em $PROCEDURAL_FILE"
  exit 1
fi

mkdir -p "$PROPOSALS_DIR"

log "=== PROMOÇÃO FORMAL DE HEURÍSTICAS INICIADA ==="

TODAY=$(date -u +"%Y-%m-%d")
NOW_TS=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
TMP_FILE="$(mktemp "${PROCEDURAL_FILE}.tmp.XXXXXX")"

# python faz a seleção de candidatos, escreve os .md de proposta e devolve
# (via stdout) a lista de propostas geradas para o bash logar/notificar.
RESULT=$(python3 - "$PROCEDURAL_FILE" "$TMP_FILE" "$PROPOSALS_DIR" "$TODAY" "$NOW_TS" <<'PY'
import json, re, sys
from pathlib import Path

procedural_path, tmp_path, proposals_dir, today, now_ts = sys.argv[1:6]
proposals_dir = Path(proposals_dir)

# Agentes conhecidos do eixo OPS (Segunda-feira CLAUDE.md — Axis Separation).
# Qualquer agente fora dessa lista é tratado como META por default, na mesma
# convenção usada pelo hook do CORTEX para notas sem "axis" declarado.
OPS_AGENTS = {
    'traffic', 'content', 'copywriter', 'creative-director', 'offer-engineer',
    'analyst', 'closer', 'sales', 'cs', 'sdr', 'cs-retention', 'events',
    'commercial', 'collector',
}

with open(procedural_path) as f:
    lines = [l.rstrip('\n') for l in f if l.strip()]

records = []
for l in lines:
    try:
        records.append(json.loads(l))
    except Exception:
        records.append(None)  # preserva linha bruta se já vier inválida

candidates = []
for idx, r in enumerate(records):
    if r is None:
        continue
    tv = r.get('times_validated', 0)
    conf = r.get('confidence', 0)
    trig = r.get('triggered_count', 0) or 0
    if not isinstance(tv, (int, float)) or not isinstance(conf, (int, float)):
        continue
    if not isinstance(trig, (int, float)):
        trig = 0
    # DOIS caminhos para virar candidata. O gate original usava só times_validated,
    # campo que apenas o heuristic_validator escreve — e ele vivia no consolidate.sh,
    # migrado para a VPS em 22-Mai-2026 enquanto heuristics.jsonl ficou no Mac.
    # Resultado medido em 04-Set: 1.029 de 1.034 travadas em tv=1, ZERO candidatas,
    # e assim permaneceria para sempre. triggered_count (escrito pelo injetor a cada
    # prompt, chega a 251) mede uso real e destrava a promoção sem inventar evidência.
    #   caminho A — evidência: o critério original, quando o loop voltar a produzir
    #   caminho B — uso real recorrente: recuperada >=50x pelo router
    por_evidencia = tv >= 30 and conf >= 0.85
    por_uso_real  = trig >= 50
    if not (por_evidencia or por_uso_real):
        continue
    r['_motivo_candidatura'] = 'evidencia' if por_evidencia else f'uso-real ({int(trig)}x)'
    if not r.get('heuristic', '').strip():
        continue   # registro sem texto não vira rule
    if r.get('status') == 'review':
        continue
    if r.get('archived'):
        continue
    if 'promoted_to_rule' in r or 'promotion_proposed' in r:
        continue
    candidates.append(idx)


def slugify(text, maxlen=60):
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return s[:maxlen].strip('-')


def derive_triggers(text, limit=8):
    """Deriva triggers a partir das palavras mais significativas da
    heurística (mesma heurística de extração usada em consolidate.sh Fase 2:
    palavras > 4 caracteres), removendo pontuação e duplicatas."""
    words = re.findall(r"[a-zà-ú0-9\-]+", text.lower())
    seen = []
    for w in words:
        w = w.strip('-')
        if len(w) > 4 and w not in seen:
            seen.append(w)
        if len(seen) >= limit:
            break
    return seen


generated = []
for idx in candidates:
    r = records[idx]
    hid = r.get('id', f'sem-id-{idx}')
    agent = r.get('agent', '@desconhecido')
    agent_clean = agent.lstrip('@')
    heuristic_text = r.get('heuristic', '')
    axis = 'ops' if agent_clean in OPS_AGENTS else 'meta'
    triggers = derive_triggers(heuristic_text)
    slug = slugify(heuristic_text) or slugify(hid)

    proposal_path = proposals_dir / f'promote-{hid}-{today}.md'

    triggers_yaml = '\n'.join(f'- {t}' for t in triggers) if triggers else '- (nenhum trigger derivado automaticamente — definir manualmente)'

    content = f'''# Proposta de Promoção de Heurística → Rule On-Demand

> Gerado automaticamente por `heuristic-promote.sh` em {today}. **Isto NÃO é uma rule ativa** — é uma proposta que precisa de aprovação do CEO antes de virar arquivo em `~/cortex/vault/rules/`.

## Heurística candidata

> {heuristic_text}

## Evidência

- **ID:** `{hid}`
- **Agente:** {agent}
- **times_validated:** {r.get('times_validated', 'N/A')}
- **confidence:** {r.get('confidence', 'N/A')}
- **Criada em:** {r.get('created', 'N/A')}
- **Última validação:** {r.get('last_validated', 'N/A')}
- **Episódio de origem:** {r.get('source_episode', 'N/A')}

## Proposta de rule on-demand

Frontmatter sugerido — **triggers derivados automaticamente das palavras-chave da heurística, revisar antes de publicar**:

```yaml
---
id: {slug}
title: "{heuristic_text[:80]}"
type: rule
domain:
- {agent_clean}
agents:
- {agent_clean}
triggers:
{triggers_yaml}
status: active
created: '{today}'
axis: {axis}
---
```

Corpo sugerido (expandir na aprovação, seguindo o formato das rules existentes em `~/cortex/vault/rules/`):

> {heuristic_text}

## Instrução de aprovação

1. Revisar a heurística e a evidência acima — confirmar que ainda faz sentido como regra permanente (não só um caso pontual).
2. **Se aprovar:** criar `~/cortex/vault/rules/{slug}.md` com o frontmatter acima (ajustando `triggers`/`domain`/`axis` conforme necessário) e o corpo da rule; depois, em `heuristics.jsonl`, adicionar em `{hid}` os campos `"promoted_to_rule": "{slug}.md#âncora"` e `"promoted_at": "{today}"`.
3. **Se rejeitar:** apagar este arquivo. A heurística permanece ativa no ciclo normal (não gera nova proposta automaticamente — `promotion_proposed` já fica marcado; para forçar nova proposta, remova esse campo manualmente).
'''

    proposal_path.write_text(content)
    r['promotion_proposed'] = today
    generated.append({'id': hid, 'agent': agent, 'file': str(proposal_path), 'times_validated': r.get('times_validated'), 'confidence': r.get('confidence')})

with open(tmp_path, 'w') as f:
    for r, original_line in zip(records, lines):
        f.write((json.dumps(r, ensure_ascii=False) if r is not None else original_line) + '\n')

print(json.dumps({'generated': generated, 'total_records': len(records), 'total_candidates': len(candidates)}, ensure_ascii=False))
PY
)

# total_candidates == total_records processados sem erro fatal → grava
mv "$TMP_FILE" "$PROCEDURAL_FILE"

N_GENERATED=$(python3 -c "import json,sys; print(len(json.loads(sys.argv[1])['generated']))" "$RESULT")
TOTAL_RECORDS=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['total_records'])" "$RESULT")

log "Heurísticas avaliadas: ${TOTAL_RECORDS}"
log "Novas propostas de promoção geradas: ${N_GENERATED}"

if [[ "$N_GENERATED" -gt 0 ]]; then
  python3 -c "
import json, sys
data = json.loads(sys.argv[1])
for item in data['generated']:
    print(f\"  - {item['id']} (@{item['agent'].lstrip('@')}, times_validated={item['times_validated']}, confidence={item['confidence']}) -> {item['file']}\")
" "$RESULT"

  # ─── NOTIFICAÇÃO AGREGADA (Telegram, se configurado) ──────────────────
  # Reusa o mecanismo já existente do Autonomous Engine (notify() em
  # ~/autonomous/lib/common.sh → enfileira em notifications/pending/,
  # dispatcher.sh entrega). UM aviso agregado, nunca um por heurística.
  if [[ -f "$COMMON_LIB" ]]; then
    # shellcheck source=/dev/null
    source "$COMMON_LIB"
    if declare -f notify >/dev/null 2>&1; then
      NOTIFY_BODY="${N_GENERATED} heurística(s) atingiram o critério de promoção formal (times_validated>=30, confidence>=0.85) e geraram proposta em ~/consciousness/proposals/. Revisar e aprovar/rejeitar manualmente."
      notify "info" "Consciousness: ${N_GENERATED} propostas de promoção de heurística" "$NOTIFY_BODY"
      log "Notificação agregada enfileirada (Telegram, via autonomous/notifications/pending/)"
    else
      log "AVISO: $COMMON_LIB não expõe notify() — notificação pulada"
    fi
  else
    log "Notificação Telegram não configurada ($COMMON_LIB ausente) — propostas ficam apenas em $PROPOSALS_DIR"
  fi
else
  log "Nenhuma heurística nova atingiu o critério de promoção nesta execução"
fi

log "=== PROMOÇÃO FORMAL DE HEURÍSTICAS CONCLUÍDA ==="
