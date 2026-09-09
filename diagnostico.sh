#!/usr/bin/env bash
#
# diagnostico.sh — Compara a SUA instalacao com a v7.15 e mostra o que
# adotar, em ordem de IMPACTO REAL. Nao altera nada: so lê e relata.
#
# Para quem customizou o framework e quer adotar seletivamente, em vez de
# sobrescrever tudo com upgrade.sh.
#
# A ordem importa mais que a lista. A intuicao diz que "mais potente" e
# mais agentes e mais skills; medindo, e o contrario: o que muda o
# funcionamento e o MOTOR, e ele e pequeno. Da para copiar os 38 agentes
# novos e continuar sem framework nenhum, se o router nao estiver
# registrado — o CORTEX e as heuristicas ficam no disco sem chegar ao
# modelo. Por isso este relatorio e ordenado por impacto, nao por volume.
#
# Uso:  bash diagnostico.sh
#
set -uo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"

t1() { printf "\n${BOLD}${CYAN}%s${NC}\n" "$1"; }
crit() { printf "  ${RED}●${NC} ${BOLD}%s${NC}\n" "$1"; }
alto() { printf "  ${YELLOW}●${NC} %s\n" "$1"; }
ok()   { printf "  ${GREEN}●${NC} %s\n" "$1"; }
det()  { printf "     ${DIM}%s${NC}\n" "$1"; }

printf "\n${BOLD}Diagnostico — a sua instalacao vs. a v7.15${NC}\n"
printf "${DIM}sua instalacao: %s${NC}\n" "$CLAUDE_DIR"
printf "${DIM}pacote v7.15:   %s${NC}\n" "$SRC"
printf "${DIM}nada sera alterado — este script so lê${NC}\n"

if [[ ! -d "$CLAUDE_DIR" ]]; then
    printf "\n${RED}Nao encontrei %s.${NC} Use ./install.sh (instalacao nova).\n" "$CLAUDE_DIR"
    exit 1
fi

ACOES=""
add_acao() { ACOES="${ACOES}$1\n"; }

# ===========================================================================
t1 "NIVEL 1 — o motor (sem isto, o resto nao roda)"
# ===========================================================================

# --- router registrado ---
ROUTER_REG=0
if [[ -f "$CLAUDE_DIR/settings.json" ]]; then
    python3 -c "
import json,sys
d=json.load(open('$CLAUDE_DIR/settings.json'))
c=[h.get('command','') for e,i in d.get('hooks',{}).items() for x in i for h in x.get('hooks',[])]
sys.exit(0 if any('router' in y for y in c) else 1)" 2>/dev/null && ROUTER_REG=1
fi
if [[ $ROUTER_REG -eq 1 ]]; then
    ok "router REGISTRADO — o contexto chega ao modelo a cada mensagem"
else
    crit "router NAO registrado  ← MAIOR IMPACTO DA LISTA"
    det "Sem ele, o CORTEX, as heuristicas e as 35 rules on-demand existem"
    det "no disco e NUNCA chegam ao modelo. Voce tem os arquivos e nao tem"
    det "o framework: cada sessao comeca do zero."
    det "Adotar: copiar hooks/router.py + registrar em settings.json"
    add_acao "1. [MOTOR] registrar router.py no settings.json (UserPromptSubmit + Stop)"
fi

# --- model declarado ---
MODELO=""
[[ -f "$CLAUDE_DIR/settings.json" ]] && MODELO=$(python3 -c "
import json;print(json.load(open('$CLAUDE_DIR/settings.json')).get('model','') or '')" 2>/dev/null)
if [[ -n "$MODELO" ]]; then
    ok "model declarado: $MODELO"
else
    crit "model NAO declarado — voce roda no modelo mais caro por padrao"
    det 'Adotar: uma linha em settings.json → "model": "sonnet"'
    det "Trabalho mecanico (editar, rodar comando, refatorar) roda bem em"
    det "sonnet; use /model opus pontualmente. A diferenca em uma semana de"
    det "uso intenso e de uma ordem de grandeza na fatura."
    add_acao "2. [CUSTO] declarar \"model\": \"sonnet\" no settings.json"
fi

# ===========================================================================
t1 "NIVEL 2 — contexto (o que voce paga em toda sessao)"
# ===========================================================================

R_SUA=$(find "$CLAUDE_DIR/rules" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
R_NOVA=$(find "$SRC/rules" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
PAL_SUA=$(cat "$CLAUDE_DIR"/rules/*.md 2>/dev/null | wc -w | tr -d ' ')
PAL_NOVA=$(cat "$SRC"/rules/*.md 2>/dev/null | wc -w | tr -d ' ')
if [[ "$R_SUA" -gt "$((R_NOVA + 1))" ]]; then
    alto "rules always-loaded: voce tem $R_SUA, a v7.15 tem $R_NOVA"
    det "~$PAL_SUA palavras carregadas em TODA sessao, contra ~$PAL_NOVA"
    det "A v7.15 consolidou 11 rules em 5. As outras viraram on-demand:"
    det "carregam so quando o assunto aparece, via triggers no frontmatter."
    det "Nao se perde cobertura — muda quando cada uma entra."
    det "Adotar: substituir rules/ pelas 5 + copiar cortex/vault/rules/ (35)"
    add_acao "3. [CONTEXTO] trocar as $R_SUA rules pelas 5 consolidadas + 35 on-demand no vault"
else
    ok "rules always-loaded: $R_SUA (~$PAL_SUA palavras)"
fi

SOLTAS=$(ls "$CLAUDE_DIR"/skills/*.md 2>/dev/null | wc -l | tr -d ' ')
ATIVAS=$(find "$CLAUDE_DIR/skills" -maxdepth 2 -name 'SKILL.md' -not -path '*_inativas*' 2>/dev/null | wc -l | tr -d ' ')
if [[ "$SOLTAS" -gt 0 ]]; then
    alto "$SOLTAS skills em .md solto — NAO carregam, mas custam contexto"
    det "No Claude Code, skill so e carregada em skills/<nome>/SKILL.md."
    det "Um .md solto nunca e invocado, mas a description dele entra no"
    det "contexto de toda sessao. Voce paga e nao recebe a funcao."
    det "Adotar: mover os .md soltos para fora de skills/"
    add_acao "4. [CONTEXTO] tirar as $SOLTAS skills em .md solto (custo sem retorno)"
else
    ok "skills no formato correto: $ATIVAS ativas"
fi

# ===========================================================================
t1 "NIVEL 3 — memoria (o que faz melhorar com o uso)"
# ===========================================================================

H_SUA=0
HP="$HOME/consciousness/memory/procedural/heuristics.jsonl"
[[ -f "$HP" ]] && H_SUA=$(wc -l < "$HP" | tr -d ' ')
H_SEED=$(wc -l < "$SRC/seed/heuristics-seed.jsonl" 2>/dev/null | tr -d ' ' || echo 0)
if [[ "$H_SUA" -eq 0 ]]; then
    alto "voce tem 0 heuristicas — o loop comeca mudo"
    det "O seed traz $H_SEED licoes de engenharia (deploy, cache, timezone,"
    det "migracao, testes) com confianca 0.5, a validar no seu uso."
    det "Adotar: copiar seed/heuristics-seed.jsonl para o caminho acima"
    add_acao "5. [MEMORIA] semear $H_SEED heuristicas (so porque voce tem 0)"
else
    ok "voce tem $H_SUA heuristicas proprias — NAO semeie por cima"
    det "O seed e para quem comeca do zero. As suas valem mais: foram"
    det "validadas no seu contexto. Se quiser complementar, adicione so as"
    det "que nao colidem — nunca substitua o arquivo."
fi

V_SUA=$(find "$HOME/cortex/vault" -name '*.md' -not -path '*/rules/*' 2>/dev/null | wc -l | tr -d ' ')
V_SEED=$(find "$SRC/seed/vault" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
ok "notas no seu vault: $V_SUA | o seed traz $V_SEED de arquitetura"
[[ "$V_SUA" -lt 10 ]] && add_acao "6. [MEMORIA] copiar seed/vault/ ($V_SEED notas de arquitetura) + build-index"

# ===========================================================================
t1 "NIVEL 4 — o que e NOVO no catalogo (impacto incremental)"
# ===========================================================================

novos_em() {  # $1 = subdir, $2 = padrao
    local n=0
    while IFS= read -r f; do
        local rel="${f#$SRC/$1/}"
        [[ -e "$CLAUDE_DIR/$1/$rel" ]] || n=$((n+1))
    done < <(find "$SRC/$1" -name "$2" 2>/dev/null)
    echo "$n"
}
A_NOVOS=$(novos_em agents '*.md')
S_NOVAS=$(novos_em skills 'SKILL.md')
C_NOVOS=$(novos_em commands '*.md')
H_NOVOS=$(novos_em hooks '*.py')
ok "agentes que voce nao tem: $A_NOVOS"
ok "skills que voce nao tem:  $S_NOVAS"
ok "commands que voce nao tem: $C_NOVOS"
ok "hooks que voce nao tem:   $H_NOVOS"
det "Estes sao os itens de MENOR impacto da lista — copiar todos sem"
det "resolver os niveis 1 e 2 aumenta o custo sem ligar o motor."
[[ "$H_NOVOS" -gt 0 ]] && add_acao "7. [CATALOGO] copiar os $H_NOVOS hooks novos (e REGISTRAR os que quiser usar)"

# ===========================================================================
t1 "SEU — o que existe so na sua instalacao (nao perca)"
# ===========================================================================
# conta e lista em passos separados: misturar det() com o echo do retorno
# fazia o numero sair no meio da listagem
seus_em() {
    local n=0
    while IFS= read -r f; do
        local rel="${f#$CLAUDE_DIR/$1/}"
        [[ -e "$SRC/$1/$rel" ]] || n=$((n+1))
    done < <(find "$CLAUDE_DIR/$1" -name "$2" 2>/dev/null)
    echo "$n"
}
lista_seus() {
    local n=0
    while IFS= read -r f; do
        local rel="${f#$CLAUDE_DIR/$1/}"
        [[ -e "$SRC/$1/$rel" ]] || { n=$((n+1)); [[ $n -le 5 ]] && det "$1/$rel"; }
    done < <(find "$CLAUDE_DIR/$1" -name "$2" 2>/dev/null)
    [[ $n -gt 5 ]] && det "... e mais $((n-5))"
    return 0
}
SA=$(seus_em agents '*.md'); SS=$(seus_em skills 'SKILL.md'); SC=$(seus_em commands '*.md')
printf "  ${GREEN}●${NC} agentes seus: %s | skills suas: %s | commands seus: %s\n" "$SA" "$SS" "$SC"
if [[ $((SA + SS + SC)) -gt 0 ]]; then
    det "itens que a v7.15 nao tem — provavelmente seus:"
    lista_seus agents '*.md'; lista_seus skills 'SKILL.md'; lista_seus commands '*.md'
    det "Qualquer adocao seletiva deve preservar estes."
fi
if [[ -f "$CLAUDE_DIR/CLAUDE.md" ]] && ! diff -q "$CLAUDE_DIR/CLAUDE.md" "$SRC/CLAUDE.md" >/dev/null 2>&1; then
    LS=$(wc -l < "$CLAUDE_DIR/CLAUDE.md" | tr -d ' '); LN=$(wc -l < "$SRC/CLAUDE.md" | tr -d ' ')
    printf "  ${GREEN}●${NC} seu CLAUDE.md difere do da v7.15 (%s linhas vs %s)\n" "$LS" "$LN"
    det "Compare com: diff $CLAUDE_DIR/CLAUDE.md $SRC/CLAUDE.md"
    det "A v7.15 tem uma secao nova ('Como o contexto chega ate o modelo')"
    det "que explica o router — vale ler mesmo que voce mantenha o seu."
fi

# ===========================================================================
printf "\n${BOLD}${CYAN}O QUE FAZER, EM ORDEM DE IMPACTO${NC}\n"
if [[ -z "$ACOES" ]]; then
    printf "  ${GREEN}Sua instalacao ja tem o essencial da v7.15.${NC}\n"
    printf "  Resta so o catalogo incremental (nivel 4), se voce quiser.\n"
else
    printf "%b" "$ACOES" | sed 's/^/  /'
    printf "\n  ${DIM}Os itens 1 e 2 sozinhos valem mais que todo o resto somado.${NC}\n"
    printf "  ${DIM}Se quiser tudo de uma vez, com backup: bash upgrade.sh${NC}\n"
fi
printf "\n"
