#!/usr/bin/env bash
#
# install.sh — Instalador do framework Segunda-feira v7.15
#
# Instala a partir DESTE diretorio (o clone local), nao de um repo remoto
# hardcoded: assim a versao instalada e sempre a que voce inspecionou.
#
# Nunca sobrescreve arquivo seu sem backup. Se ja existir settings.json ou
# CLAUDE.md, deixa a versao do framework ao lado para voce mesclar.
#
set -uo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
SF_CORE="${SF_CORE:-$HOME/.sf-core}"
VERSION="7.15"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$CLAUDE_DIR/.segunda-feira-backup-$STAMP"

ok()   { printf "  ${GREEN}✓${NC} %s\n" "$1"; }
warn() { printf "  ${YELLOW}!${NC} %s\n" "$1"; }
err()  { printf "  ${RED}✗${NC} %s\n" "$1"; }
step() { printf "\n${BOLD}%s${NC}\n" "$1"; }

printf "\n${BOLD}${CYAN}Segunda-feira v%s${NC} — instalacao\n" "$VERSION"
printf "${DIM}origem: %s${NC}\n" "$SRC"
printf "${DIM}destino: %s${NC}\n" "$CLAUDE_DIR"

# --------------------------------------------------------------------------
step "1. Pre-requisitos"
MISSING=0
for bin in python3 git; do
    if command -v "$bin" >/dev/null 2>&1; then
        ok "$bin encontrado"
    else
        err "$bin nao encontrado — instale antes de continuar"; MISSING=1
    fi
done
[[ $MISSING -eq 1 ]] && exit 1

PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)
ok "python $PYV"

# --------------------------------------------------------------------------
step "2. Backup do que ja existe"
mkdir -p "$CLAUDE_DIR"
BACKED=0
for dir in agents skills rules hooks commands tasks; do
    if [[ -d "$CLAUDE_DIR/$dir" ]]; then
        mkdir -p "$BACKUP_DIR"
        cp -R "$CLAUDE_DIR/$dir" "$BACKUP_DIR/" 2>/dev/null && BACKED=1
    fi
done
if [[ $BACKED -eq 1 ]]; then
    ok "backup em $BACKUP_DIR"
else
    ok "instalacao limpa (nada a preservar)"
fi

# --------------------------------------------------------------------------
step "3. Camada de controle -> ~/.claude"
for dir in agents skills rules hooks commands tasks; do
    if [[ -d "$SRC/$dir" ]]; then
        mkdir -p "$CLAUDE_DIR/$dir"
        cp -R "$SRC/$dir/." "$CLAUDE_DIR/$dir/" 2>/dev/null || true
        N=$(find "$SRC/$dir" -type f 2>/dev/null | wc -l | tr -d ' ')
        ok "$dir ($N arquivos)"
    fi
done

# --------------------------------------------------------------------------
step "4. Nucleo SDC -> ~/.sf-core"
mkdir -p "$SF_CORE"
cp -R "$SRC/sf-core/." "$SF_CORE/" 2>/dev/null || true
N=$(find "$SRC/sf-core" -type f 2>/dev/null | wc -l | tr -d ' ')
ok "sf-core ($N arquivos: tasks, workflows, squads)"

# --------------------------------------------------------------------------
step "5. Sistemas de memoria (estrutura vazia)"
# O motor entra; a memoria e sua e comeca zerada.
#
# ATENCAO: esta lista foi levantada varrendo o que os scripts ESCREVEM
# (grep dos paths em consciousness/, cortex/, broadcast/, hooks/).
# Um diretorio faltando aqui nao da erro na instalacao — quebra depois,
# na primeira tarefa real. Foi o que aconteceu com memory/procedural/:
# record-episode.sh falhava ao gravar a primeira heuristica.
for d in cortex/vault/rules cortex/vault/projects cortex/scripts cortex/templates \
         cortex/index cortex/briefings cortex/briefings/meta cortex/briefings/ops \
         cortex/inbox cortex/reports \
         consciousness/scripts consciousness/memory/episodic \
         consciousness/memory/procedural consciousness/memory/consolidation \
         consciousness/metacognition consciousness/workspace consciousness/proposals \
         broadcast/mailbox broadcast/scripts \
         patterns framework/scripts framework/runtime \
         .claude/logs; do
    mkdir -p "$HOME/$d"
done

# Arquivos-semente que os scripts esperam poder abrir em modo append.
: > "$HOME/consciousness/memory/procedural/heuristics.jsonl" 2>/dev/null || true
[[ ! -s "$HOME/consciousness/memory/procedural/heuristics.jsonl" ]] || true
for seed in "$HOME/consciousness/workspace/proposals.json" \
            "$HOME/consciousness/memory/.feedback-tracker.json"; do
    [[ -f "$seed" ]] || echo '{}' > "$seed"
done

cp -R "$SRC/cortex/scripts/." "$HOME/cortex/scripts/" 2>/dev/null || true
cp -R "$SRC/cortex/templates/." "$HOME/cortex/templates/" 2>/dev/null || true
cp -R "$SRC/cortex/vault/rules/." "$HOME/cortex/vault/rules/" 2>/dev/null || true
cp -R "$SRC/consciousness/scripts/." "$HOME/consciousness/scripts/" 2>/dev/null || true
cp -R "$SRC/framework/scripts/." "$HOME/framework/scripts/" 2>/dev/null || true
cp -R "$SRC/framework/runtime/." "$HOME/framework/runtime/" 2>/dev/null || true
mkdir -p "$HOME/framework/tests" "$HOME/framework/utils"
cp -R "$SRC/framework/tests/." "$HOME/framework/tests/" 2>/dev/null || true
cp -R "$SRC/framework/utils/." "$HOME/framework/utils/" 2>/dev/null || true
[[ -f "$SRC/broadcast/signals.json" ]] && [[ ! -f "$HOME/broadcast/signals.json" ]] \
    && cp "$SRC/broadcast/signals.json" "$HOME/broadcast/signals.json"
for f in "$SRC"/broadcast/*.sh; do
    [[ -e "$f" ]] && cp "$f" "$HOME/broadcast/" 2>/dev/null || true
done
for f in "$SRC"/patterns/*.md; do
    base=$(basename "$f")
    [[ -e "$f" ]] && [[ ! -f "$HOME/patterns/$base" ]] && cp "$f" "$HOME/patterns/"
done
chmod +x "$HOME"/cortex/scripts/*.sh "$HOME"/consciousness/scripts/*.sh \
         "$HOME"/broadcast/*.sh "$HOME"/framework/scripts/*.sh 2>/dev/null || true
ok "cortex, consciousness, broadcast, patterns"

# --- Seed: licoes de engenharia para o loop nao comecar mudo -----------------
# Confianca reiniciada de proposito (ver seed/README.md): foi validado em outro
# ambiente, nao no seu. So NAO semeia se ja houver historico — nunca sobrescreve
# aprendizado existente.
SEED_H="$HOME/consciousness/memory/procedural/heuristics.jsonl"
if [[ -f "$SRC/seed/heuristics-seed.jsonl" ]]; then
    if [[ -s "$SEED_H" ]]; then
        warn "já existem heurísticas — seed NÃO aplicado (seu histórico vence)"
    else
        cp "$SRC/seed/heuristics-seed.jsonl" "$SEED_H"
        N=$(wc -l < "$SEED_H" | tr -d ' ')
        ok "seed: $N heurísticas de engenharia (confiança 0.5, a validar no seu uso)"
    fi
fi
if [[ -d "$SRC/seed/vault" ]]; then
    cp -R "$SRC/seed/vault/." "$HOME/cortex/vault/" 2>/dev/null || true
    N=$(find "$SRC/seed/vault" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
    ok "seed: $N notas de arquitetura no vault"
    # indexa para o router poder recuperá-las por busca
    python3 "$HOME/cortex/scripts/cortex_engine.py" build-index >/dev/null 2>&1 \
        && ok "índice do CORTEX construído" \
        || warn "rode 'python3 ~/cortex/scripts/cortex_engine.py build-index' depois"
fi

# --------------------------------------------------------------------------
step "6. Configuracao"
if [[ -f "$SRC/settings.template.json" ]]; then
    if [[ -f "$CLAUDE_DIR/settings.json" ]]; then
        cp "$SRC/settings.template.json" "$CLAUDE_DIR/settings.segunda-feira.json"
        warn "settings.json ja existe — template salvo como settings.segunda-feira.json"
        warn "  mescle a mao (permissoes + registro dos hooks)"
    else
        cp "$SRC/settings.template.json" "$CLAUDE_DIR/settings.json"
        ok "settings.json criado (permissoes + hooks registrados)"
    fi
fi

if [[ -f "$SRC/CLAUDE.md" ]]; then
    if [[ -f "$CLAUDE_DIR/CLAUDE.md" ]]; then
        cp "$SRC/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.segunda-feira.md"
        warn "CLAUDE.md ja existe — constituicao salva como CLAUDE.segunda-feira.md"
    else
        cp "$SRC/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
        ok "CLAUDE.md (constituicao) instalado"
    fi
fi

# AGENTS.md: convencao multi-harness (Codex, Cursor, Aider)
if [[ -f "$CLAUDE_DIR/CLAUDE.md" ]] && [[ ! -e "$CLAUDE_DIR/AGENTS.md" ]]; then
    ln -s CLAUDE.md "$CLAUDE_DIR/AGENTS.md" 2>/dev/null \
        && ok "AGENTS.md -> CLAUDE.md (compatibilidade multi-IA)"
fi

if [[ -f "$SRC/.env.example" ]] && [[ ! -f "$HOME/.env" ]]; then
    cp "$SRC/.env.example" "$HOME/.env"
    chmod 600 "$HOME/.env"
    ok ".env criado a partir do exemplo (chmod 600) — preencha o que for usar"
elif [[ -f "$HOME/.env" ]]; then
    warn ".env ja existe — nao foi tocado"
fi

# --------------------------------------------------------------------------
step "7. Dependencias Python"
if [[ -f "$SRC/requirements.txt" ]]; then
    if python3 -m pip install --quiet -r "$SRC/requirements.txt" 2>/dev/null; then
        ok "dependencias instaladas"
    else
        warn "falha ao instalar deps — rode: pip3 install -r requirements.txt"
    fi
fi

# --------------------------------------------------------------------------
step "8. Verificacao — contagem"
A=$(find "$CLAUDE_DIR/agents" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
S=$(find "$CLAUDE_DIR/skills" -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ')
R=$(find "$CLAUDE_DIR/rules" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
H=$(find "$CLAUDE_DIR/hooks" -maxdepth 1 -name '*.py' 2>/dev/null | wc -l | tr -d ' ')
printf "  agentes: %s | skills: %s | rules: %s | hooks: %s\n" "$A" "$S" "$R" "$H"

if [[ "$A" -gt 0 && "$R" -gt 0 ]]; then
    ok "arquivos no lugar"
else
    err "algo nao copiou — confira as permissoes de $CLAUDE_DIR"
    exit 1
fi

# --------------------------------------------------------------------------
step "9. Verificacao — o motor RODA?"
# Contar arquivo nao prova nada: o que quebra o aluno e o script que falha
# na primeira tarefa real. Aqui exercitamos o loop de fato.
FUNC_OK=1

# (a) router: e ele que injeta briefing, CORTEX, heuristicas e rules on-demand
if echo '{"prompt":"teste de instalacao","session_id":"install"}' \
     | python3 "$CLAUDE_DIR/hooks/router.py" submit >/dev/null 2>&1; then
    ok "router responde (injecao de contexto ativa)"
else
    err "router falhou — o CORTEX e as rules on-demand nao chegarao ao modelo"; FUNC_OK=0
fi

# (b) memoria episodica: grava e le de volta
EP_BEFORE=$(cat "$HOME/consciousness/memory/episodic/"*.jsonl 2>/dev/null | wc -l | tr -d ' ')
if bash "$HOME/consciousness/scripts/record-episode.sh" --agent "@dev" \
        --type "task_completed" --summary "smoke test da instalacao" \
        --result "success" --valence 0.3 --intensity 0.3 >/dev/null 2>&1; then
    EP_AFTER=$(cat "$HOME/consciousness/memory/episodic/"*.jsonl 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$EP_AFTER" -gt "$EP_BEFORE" ]]; then
        ok "memoria episodica grava (o loop de aprendizado fecha)"
    else
        err "record-episode rodou mas nao gravou"; FUNC_OK=0
    fi
else
    err "record-episode falhou — nenhum aprendizado sera acumulado"; FUNC_OK=0
fi

# (c) CORTEX: engine responde
if python3 "$HOME/cortex/scripts/cortex_engine.py" health >/dev/null 2>&1; then
    ok "CORTEX engine responde"
else
    warn "CORTEX engine nao respondeu — rode 'cortex_engine.py build-index' depois"
fi

if [[ $FUNC_OK -eq 1 ]]; then
    ok "motor funcional"
else
    err "instalacao incompleta: os arquivos estao la, mas o motor nao roda"
    exit 1
fi

# --------------------------------------------------------------------------
printf "\n${BOLD}${GREEN}Pronto.${NC} Segunda-feira v%s instalado.\n\n" "$VERSION"
cat <<'EOF'
Proximos passos:

  1. Preencha ~/.env com o que for usar (chmod 600 ja aplicado)
  2. Rode o health check — ele confronta a documentacao com a maquina:

       python3 ~/framework/scripts/framework_health_check.py

  3. Abra o Claude Code e experimente:

       @dev          ativa o agente de desenvolvimento
       *help         lista os comandos do agente ativo
       /plan-first   plano antes de tarefa multi-arquivo

O vault do CORTEX e a memoria episodica comecam VAZIOS de proposito.
O framework aprende com os seus dados — o valor aparece por volta da
terceira sessao, quando a memoria comeca a devolver o que voce ensinou.

Para desinstalar:  bash uninstall.sh
EOF
