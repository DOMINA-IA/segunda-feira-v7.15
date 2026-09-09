---
name: freeze
description: "Trava Edit/Write a um diretório específico para impedir scope-creep durante trabalho focado (acompanha o hook freeze.py). Use durante /investigate (trava no diretório do bug), em hotfix de produção (garante que só o arquivo-alvo muda), ou em refactor focado."
axis: meta
harnesses:
  claude-code: full
  codex: limited
  cursor: none
  aider: none
model-routing:
  primary: local  # operação determinística (escreve/remove arquivo de estado)
---

# /freeze — Travar Edições a um Diretório

## O que faz

Restringe `Write`/`Edit`/`MultiEdit` a um único diretório. Qualquer tentativa de
editar fora dele é **bloqueada** pelo hook `freeze.py` (PreToolUse). Inerte quando
desligado — zero impacto no fluxo normal.

Absorvido do `/freeze` do gstack (Garry Tan). Cruza com `autonomous-execution.md`
(contém o raio de ação do agente autônomo) e com `/investigate` (impede que debug
vire refactor).

## Uso

| Comando | Efeito |
|---------|--------|
| `/freeze <diretório>` | Ativa: só edita dentro de `<diretório>` |
| `/freeze .` | Trava no diretório de trabalho atual |
| `/freeze off` | Desativa a trava |
| `/freeze status` | Mostra o estado atual |

## Implementação (o agente executa)

**Ativar:**
```bash
DIR="${1:-.}"; ABS=$(cd "$DIR" 2>/dev/null && pwd)
mkdir -p ~/.claude/.session-state
python3 - "$ABS" <<'PY'
import json, sys, time, os
abs_path = sys.argv[1]
state = {"path": abs_path, "session": os.environ.get("CLAUDE_SESSION_ID","manual"), "set_at": int(time.time())}
open(os.path.expanduser("~/.claude/.session-state/freeze.json"),"w").write(json.dumps(state))
print(f"🧊 FREEZE ativo — edições restritas a: {abs_path}/")
PY
```

**Desativar:**
```bash
rm -f ~/.claude/.session-state/freeze.json && echo "🔥 FREEZE desligado — edições liberadas."
```

**Status:**
```bash
cat ~/.claude/.session-state/freeze.json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'🧊 ativo em: {d[\"path\"]}/')" 2>/dev/null || echo "🔥 sem freeze ativo"
```

## Quando usar

- Durante `/investigate` — trava no diretório do bug, impede fix de passagem
- Hotfix em produção — garante que só o arquivo-alvo muda
- Refactor focado — evita "já que estou aqui, ajusto isso também"

## Nota de segurança

O hook usa match por prefixo **com barra final** (`/foo/` não libera `/foobar/`).
A trava é por arquivo de estado global — lembre de `/freeze off` ao terminar, ou
ela persiste entre sessões. (O `careful.py` continua ativo independentemente.)

## Origem

Absorvido do gstack v1.58.5.0 em 26-Jun-2026. Hook: `~/.claude/hooks/freeze.py`.
