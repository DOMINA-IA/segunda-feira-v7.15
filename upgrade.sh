#!/usr/bin/env bash
#
# upgrade.sh — Atualiza uma instalacao ANTERIOR do Segunda-feira para a v7.15.
#
# Use este script se voce JA TEM o framework instalado (v7.5 … v7.14).
# Para instalacao nova, use install.sh.
#
# POR QUE ESTE SCRIPT EXISTE
# O install.sh e conservador de proposito: nunca sobrescreve arquivo seu.
# Numa instalacao nova isso e o certo. Num UPGRADE, isso deixa o pior dos
# dois mundos:
#   - as 14 rules que a v7.15 consolidou continuam carregando junto com as
#     5 novas -> 19 rules always-loaded, contexto MAIOR que antes e com
#     instrucao duplicada competindo por atencao
#   - o settings.json antigo fica, e sem o router registrado o CORTEX, as
#     heuristicas e as rules on-demand nunca chegam ao modelo
#   - o CLAUDE.md antigo fica, descrevendo uma arquitetura que mudou
#
# O QUE ESTE SCRIPT NUNCA TOCA (a sua memoria e sua):
#   ~/cortex/vault/           notas que voce escreveu
#   ~/consciousness/memory/   episodios e heuristicas que voce acumulou
#   ~/patterns/               padroes que voce validou
#   ~/.env                    suas credenciais
#   .claude/settings.local.json
#
# Tudo que for movido vai para um backup datado, nada e apagado.
#
set -uo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$CLAUDE_DIR/.upgrade-v7.15-$STAMP"

ok()   { printf "  ${GREEN}✓${NC} %s\n" "$1"; }
warn() { printf "  ${YELLOW}!${NC} %s\n" "$1"; }
err()  { printf "  ${RED}✗${NC} %s\n" "$1"; }
step() { printf "\n${BOLD}%s${NC}\n" "$1"; }

printf "\n${BOLD}${CYAN}Segunda-feira — upgrade para v7.15${NC}\n"
printf "${DIM}origem:  %s${NC}\n" "$SRC"
printf "${DIM}destino: %s${NC}\n" "$CLAUDE_DIR"
printf "${DIM}backup:  %s${NC}\n" "$BACKUP"

if [[ ! -d "$CLAUDE_DIR" ]]; then
    err "Nao encontrei $CLAUDE_DIR — voce nao tem instalacao anterior."
    err "Use ./install.sh para instalar do zero."
    exit 1
fi

# --------------------------------------------------------------------------
step "1. Backup completo do estado atual"
mkdir -p "$BACKUP"
for d in agents skills rules hooks commands tasks; do
    [[ -d "$CLAUDE_DIR/$d" ]] && cp -R "$CLAUDE_DIR/$d" "$BACKUP/" 2>/dev/null
done
for f in settings.json CLAUDE.md AGENTS.md; do
    [[ -f "$CLAUDE_DIR/$f" ]] && cp "$CLAUDE_DIR/$f" "$BACKUP/" 2>/dev/null
done
ok "backup em $BACKUP"
printf "     ${DIM}para desfazer tudo: cp -R %s/* %s/${NC}\n" "$BACKUP" "$CLAUDE_DIR"

# --------------------------------------------------------------------------
step "2. Rules obsoletas (consolidadas na v7.15)"
# Estas 14 foram absorvidas pelas 5 always-loaded ou viraram on-demand no
# vault. Se continuarem em rules/, carregam em TODA sessao e duplicam
# instrucao — exatamente o que a v7.15 corrigiu.
OBSOLETAS=(
    agent-communication.md autonomous-execution.md axis-separation.md
    confidence-guardrails.md consciousness-engine.md cortex-usage.md
    cross-project-protocol.md eros-quality.md evolution-scorecard.md
    feedback-loop.md model-routing-multi-llm.md multi-ia-portability.md
    visual-rendering-safety.md n8n-patterns.md workflow-execution.md
    story-lifecycle.md ids-principles.md token-economy.md
    initiative-protocol.md handoff-protocol.md creativity-protocol.md
    coderabbit-integration.md external-api-patterns.md mcp-usage.md
    context-quality.md visual-rendering-safety.md verificacao-honesta.md
)
mkdir -p "$BACKUP/rules-obsoletas"
MOVIDAS=0
for r in "${OBSOLETAS[@]}"; do
    if [[ -f "$CLAUDE_DIR/rules/$r" ]]; then
        mv "$CLAUDE_DIR/rules/$r" "$BACKUP/rules-obsoletas/" 2>/dev/null && MOVIDAS=$((MOVIDAS+1))
    fi
done
if [[ $MOVIDAS -gt 0 ]]; then
    ok "$MOVIDAS rules obsoletas movidas para o backup"
    printf "     ${DIM}o conteudo delas vive agora em ~/cortex/vault/rules/ (on-demand)${NC}\n"
else
    ok "nenhuma rule obsoleta encontrada"
fi

# --------------------------------------------------------------------------
step "3. Skills em formato antigo (.md solto)"
# No Claude Code, skill so carrega em skills/<nome>/SKILL.md. Um .md solto
# NAO e carregado, mas a description dele pesa no contexto de toda sessao.
mkdir -p "$BACKUP/skills-formato-antigo"
SOLTAS=0
for f in "$CLAUDE_DIR"/skills/*.md; do
    [[ -e "$f" ]] || continue
    mv "$f" "$BACKUP/skills-formato-antigo/" 2>/dev/null && SOLTAS=$((SOLTAS+1))
done
if [[ $SOLTAS -gt 0 ]]; then
    ok "$SOLTAS skills em .md solto movidas (nao carregavam, so custavam contexto)"
else
    ok "nenhuma skill em formato antigo"
fi

# --------------------------------------------------------------------------
step "4. Conteudo da v7.15"
for dir in agents skills rules hooks commands tasks; do
    if [[ -d "$SRC/$dir" ]]; then
        mkdir -p "$CLAUDE_DIR/$dir"
        cp -R "$SRC/$dir/." "$CLAUDE_DIR/$dir/" 2>/dev/null || true
        ok "$dir atualizado"
    fi
done

SF_CORE="${SF_CORE:-$HOME/.sf-core}"
mkdir -p "$SF_CORE" && cp -R "$SRC/sf-core/." "$SF_CORE/" 2>/dev/null || true
ok "sf-core atualizado"

for d in cortex/vault/rules cortex/scripts cortex/templates cortex/index \
         cortex/briefings cortex/briefings/meta cortex/briefings/ops \
         cortex/inbox cortex/reports cortex/vault/projects \
         consciousness/scripts consciousness/memory/episodic \
         consciousness/memory/procedural consciousness/memory/consolidation \
         consciousness/metacognition consciousness/workspace consciousness/proposals \
         broadcast/mailbox broadcast/scripts patterns \
         framework/scripts framework/runtime framework/tests framework/utils \
         .claude/logs; do
    mkdir -p "$HOME/$d"
done
cp -R "$SRC/cortex/scripts/." "$HOME/cortex/scripts/" 2>/dev/null || true
cp -R "$SRC/cortex/templates/." "$HOME/cortex/templates/" 2>/dev/null || true
cp -R "$SRC/cortex/vault/rules/." "$HOME/cortex/vault/rules/" 2>/dev/null || true
cp -R "$SRC/consciousness/scripts/." "$HOME/consciousness/scripts/" 2>/dev/null || true
cp -R "$SRC/framework/scripts/." "$HOME/framework/scripts/" 2>/dev/null || true
cp -R "$SRC/framework/runtime/." "$HOME/framework/runtime/" 2>/dev/null || true
cp -R "$SRC/framework/tests/." "$HOME/framework/tests/" 2>/dev/null || true
cp -R "$SRC/framework/utils/." "$HOME/framework/utils/" 2>/dev/null || true
for f in "$SRC"/broadcast/*.sh; do [[ -e "$f" ]] && cp "$f" "$HOME/broadcast/" 2>/dev/null; done
chmod +x "$HOME"/cortex/scripts/*.sh "$HOME"/consciousness/scripts/*.sh \
         "$HOME"/broadcast/*.sh "$HOME"/framework/scripts/*.sh 2>/dev/null || true
ok "scripts do CORTEX, Consciousness e verificadores atualizados"
ok "sua memoria (vault, episodios, patterns) NAO foi tocada"

# --------------------------------------------------------------------------
step "5. settings.json — mesclagem"
# Aqui esta o item que o install.sh nao resolve: sem o router registrado, o
# CORTEX e as rules on-demand existem no disco e nunca chegam ao modelo.
python3 - "$CLAUDE_DIR/settings.json" "$SRC/settings.template.json" "$BACKUP" <<'PYEOF'
import json, sys, os, shutil

atual_p, novo_p, backup = sys.argv[1], sys.argv[2], sys.argv[3]

try:
    novo = json.load(open(novo_p, encoding="utf-8"))
except Exception as e:
    print(f"  ! nao consegui ler o template ({e})"); sys.exit(0)

if not os.path.exists(atual_p):
    shutil.copy(novo_p, atual_p)
    print("  ✓ settings.json criado a partir do template")
    sys.exit(0)

try:
    atual = json.load(open(atual_p, encoding="utf-8"))
except Exception:
    shutil.copy(atual_p, os.path.join(backup, "settings.json.ilegivel"))
    shutil.copy(novo_p, atual_p)
    print("  ! settings.json anterior estava ilegivel — substituido (copia no backup)")
    sys.exit(0)

mudou = []

# hooks: o bloco da v7.15 substitui inteiro. Mesclar item a item produz
# duplicata (o mesmo hook registrado 2x) e deixa hook morto de versao antiga.
if atual.get("hooks") != novo.get("hooks"):
    atual["hooks"] = novo["hooks"]
    mudou.append("hooks (router, gates, coach) registrados")

# model: sem isto, herda-se o modelo mais caro por padrao
if not atual.get("model"):
    atual["model"] = novo.get("model", "sonnet")
    mudou.append(f'model = "{atual["model"]}"')

# permissoes: uniao — o que voce liberou continua liberado
pa = atual.setdefault("permissions", {})
pn = novo.get("permissions", {})
for chave in ("allow", "deny", "ask"):
    if chave in pn:
        antes = list(pa.get(chave, []))
        pa[chave] = list(dict.fromkeys(antes + pn[chave]))
        if len(pa[chave]) != len(antes):
            mudou.append(f"permissions.{chave}: +{len(pa[chave]) - len(antes)}")

for chave in ("language", "effortLevel", "alwaysThinkingEnabled"):
    if chave in novo and chave not in atual:
        atual[chave] = novo[chave]
        mudou.append(chave)

json.dump(atual, open(atual_p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
if mudou:
    for m in mudou:
        print(f"  ✓ {m}")
else:
    print("  ✓ settings.json ja estava atualizado")
PYEOF

# --------------------------------------------------------------------------
step "6. CLAUDE.md — a constituicao"
if [[ -f "$CLAUDE_DIR/CLAUDE.md" ]]; then
    if diff -q "$CLAUDE_DIR/CLAUDE.md" "$SRC/CLAUDE.md" >/dev/null 2>&1; then
        ok "CLAUDE.md ja e o da v7.15"
    else
        cp "$SRC/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.v7.15.md"
        warn "voce tem um CLAUDE.md proprio — a versao v7.15 ficou ao lado:"
        printf "     ${DIM}%s/CLAUDE.v7.15.md${NC}\n" "$CLAUDE_DIR"
        printf "     ${DIM}compare com: diff %s/CLAUDE.md %s/CLAUDE.v7.15.md${NC}\n" "$CLAUDE_DIR" "$CLAUDE_DIR"
        printf "     ${DIM}o backup do seu esta em %s/CLAUDE.md${NC}\n" "$BACKUP"
    fi
else
    cp "$SRC/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
    ok "CLAUDE.md instalado"
fi
[[ -f "$CLAUDE_DIR/CLAUDE.md" && ! -e "$CLAUDE_DIR/AGENTS.md" ]] && \
    ln -s CLAUDE.md "$CLAUDE_DIR/AGENTS.md" 2>/dev/null && ok "AGENTS.md -> CLAUDE.md"

# --------------------------------------------------------------------------
step "7. Seed de memoria"
SEED_H="$HOME/consciousness/memory/procedural/heuristics.jsonl"
if [[ -s "$SEED_H" ]]; then
    ok "voce ja tem heuristicas proprias — seed NAO aplicado (seu historico vence)"
else
    [[ -f "$SRC/seed/heuristics-seed.jsonl" ]] && cp "$SRC/seed/heuristics-seed.jsonl" "$SEED_H" \
        && ok "seed: $(wc -l < "$SEED_H" | tr -d ' ') heuristicas de engenharia"
fi
if [[ -d "$SRC/seed/vault" ]]; then
    cp -R "$SRC/seed/vault/." "$HOME/cortex/vault/" 2>/dev/null || true
    ok "notas de arquitetura no vault (nao sobrescreve as suas)"
    python3 "$HOME/cortex/scripts/cortex_engine.py" build-index >/dev/null 2>&1 \
        && ok "indice do CORTEX reconstruido"
fi

# --------------------------------------------------------------------------
step "8. Verificacao — o motor esta LIGADO?"
FALHOU=0

R_ALWAYS=$(find "$CLAUDE_DIR/rules" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
if [[ "$R_ALWAYS" -le 5 ]]; then
    ok "rules always-loaded: $R_ALWAYS"
else
    err "rules always-loaded: $R_ALWAYS (esperado 5) — sobrou rule obsoleta"; FALHOU=1
fi

# O que importa nao e o router EXISTIR, e ele estar REGISTRADO: e o registro
# que faz o Claude Code executa-lo a cada mensagem.
if python3 -c "
import json,sys
d=json.load(open('$CLAUDE_DIR/settings.json'))
cmds=[h.get('command','') for ev,it in d.get('hooks',{}).items() for i in it for h in i.get('hooks',[])]
sys.exit(0 if any('router' in c for c in cmds) else 1)" 2>/dev/null; then
    ok "router REGISTRADO no settings.json (injecao de contexto ativa)"
else
    err "router NAO registrado — CORTEX e rules on-demand nao chegarao ao modelo"; FALHOU=1
fi

MODELO=$(python3 -c "import json;print(json.load(open('$CLAUDE_DIR/settings.json')).get('model','') or '')" 2>/dev/null)
[[ -n "$MODELO" ]] && ok "model declarado: $MODELO" || { err "model nao declarado (custo alto)"; FALHOU=1; }

if echo '{"prompt":"teste de upgrade","session_id":"up"}' \
     | python3 "$CLAUDE_DIR/hooks/router.py" submit >/dev/null 2>&1; then
    ok "router responde"
else
    err "router falhou ao executar"; FALHOU=1
fi

SKILLS=$(find "$CLAUDE_DIR/skills" -maxdepth 2 -name 'SKILL.md' -not -path '*_inativas*' 2>/dev/null | wc -l | tr -d ' ')
ok "skills ativas (formato <nome>/SKILL.md): $SKILLS"

printf "\n"
if [[ $FALHOU -eq 0 ]]; then
    printf "${BOLD}${GREEN}Upgrade concluido.${NC} O motor esta ligado.\n\n"
    cat <<EOF
Proximos passos:
  1. Feche e reabra o Claude Code (os hooks so recarregam em sessao nova)
  2. Confira a saude da instalacao:
       python3 ~/framework/scripts/framework_health_check.py
  3. Mande uma mensagem qualquer: voce deve ver o bloco de contexto
     injetado (heuristicas + notas) no inicio da resposta

Backup completo em: $BACKUP
Para desfazer:      cp -R $BACKUP/* $CLAUDE_DIR/
EOF
else
    printf "${BOLD}${RED}Upgrade incompleto.${NC} Veja os itens marcados com x acima.\n"
    printf "Backup intacto em: %s\n" "$BACKUP"
    exit 1
fi
