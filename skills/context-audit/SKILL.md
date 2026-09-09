---
name: context-audit
description: "Mede o custo em tokens do contexto sempre-carregado (rules, skills, CLAUDE.md) e propõe corte por ablação empírica. Use na revisão mensal do framework ou ao trocar de geração de modelo. NOT for: custo de API em runtime — é @cost-optimizer."
axis: meta
harnesses:
  claude-code: full
  codex: limited
  cursor: limited
provider-fallback:
  - anthropic/claude-sonnet-5
  - anthropic/claude-haiku-4-5
---

# /context-audit — Ablação do Contexto Sempre-Carregado

## Princípio

Boa parte das instruções de um framework existe para **compensar limitação de modelo antigo**.
Quando o modelo melhora, elas viram peso morto — e peso morto não é neutro: compete por atenção
com a instrução que ainda importa.

**Regra de ouro:** "Não adivinhe qual instrução é necessária. Remova, observe a falha real, e só
então recoloque."

> Origem: INEMA.CCODE 13-Ago-2026, tese de Boris Cherny. O próprio Claude Code removeu **mais de
> 80% do system prompt** ao migrar de geração de modelo. Cada geração deve ser tratada como
> diferente — prompt que funcionava há três meses pode atrapalhar hoje.

## Quando rodar

- **Sempre** que trocar a geração do modelo padrão (Opus 4.x → 5, Sonnet 4 → 5…)
- Revisão mensal do framework
- Quando o modelo passar a ignorar instrução que antes seguia
- Antes de adicionar rule/skill nova (mede se há espaço antes de gastar)

## Fase 1 — Medir (nunca cortar antes de medir)

```bash
# Custo fixo das descriptions de skill (entram em TODA sessão, usadas ou não)
for f in ~/.claude/skills/*/SKILL.md; do
  d=$(sed -n '/^description:/,/^[a-z-]*:/p' "$f" | head -20 | wc -c)
  echo "$((d/4)) $(basename $(dirname $f))"
done | sort -rn

# Custo das rules always-loaded
wc -w ~/.claude/rules/*.md ~/.claude/CLAUDE.md | sort -rn

# Uso REAL nos últimos 60 dias — a métrica que decide
grep -rlo "nome-da-skill" ~/.claude/projects/*/[0-9a-f]*.jsonl 2>/dev/null | wc -l
```

Regra de conversão: **~4 caracteres ≈ 1 token**. Uma description de 250 chars custa ~60 tokens
por sessão. Cinquenta delas custam ~3.000 tokens **antes de você digitar qualquer coisa**.

## Fase 2 — Classificar cada item

| Classe | Critério | Ação |
|---|---|---|
| **Núcleo** | Contexto de negócio, caminho de arquivo, credencial, autoridade de agente | **Nunca cortar** — o modelo não tem como descobrir sozinho |
| **Segurança** | Previne dano irreversível (push, produção, dado de cliente) | **Nunca cortar** — o custo do erro domina o custo do token |
| **Muleta** | Corrige comportamento que o modelo atual já acerta sozinho | **Candidato a corte** — teste por ablação |
| **Zumbi** | Zero invocação em 60 dias E não é segurança | **Cortar** — mover para `_inativas/` |

A distinção que mais importa: **contexto ≠ instrução**. "O CLIENTE_EXEMPLO roda em PM2 na VPS ${VPS_HOST}"
é contexto e deve ficar. "Sempre pense passo a passo antes de responder" é muleta de 2024.

## Fase 3 — Ablação (a parte empírica)

```bash
CLAUDE_CODE_SIMPLE=1 claude    # remove TODOS os system prompts, inclusive das tools
unset CLAUDE_CODE_SIMPLE        # volta ao normal
```

Recurso pouco documentado que a própria Anthropic usa como baseline de ablação.

**Protocolo:** rode a mesma tarefa real três vezes — com contexto completo, sem a rule suspeita,
e com `CLAUDE_CODE_SIMPLE=1`. Compare a saída. Se a versão sem a rule for igual ou melhor, a rule
era muleta.

Cuidado registrado no INEMA: sem contexto, a saída fica **mais criativa mas perde marca,
formatação e convenção**. Isso confirma a Fase 2 — corte muleta, preserve núcleo.

## Fase 3b — Chamadas headless: o maior ganho isolado

Uma sessão `claude -p` carrega, por padrão, todo o `settings.json`, MCPs e contexto do projeto —
mesmo quando a tarefa é uma classificação de três linhas. Medição do INEMA (01-Set-2026):

```bash
claude -p --setting-sources "" --strict-mcp-config "..."   # 150.000 → ~760 tokens
```

**Queda de ~99%.** `--setting-sources ""` corta a herança de settings; `--strict-mcp-config` impede
carregar servidores MCP que a tarefa não usa.

**Onde aplicar:** todo cron e script que chama `claude -p` para trabalho mecânico — classificar,
extrair campo, validar formato, resumir. Auditar com:

```bash
grep -rn "claude -p" ~/framework/scripts ~/autonomous ~/cortex/scripts 2>/dev/null | grep -v setting-sources
```

**Onde NÃO aplicar:** chamada que depende de MCP, de skill do projeto ou do `CLAUDE.md` para
acertar. Sem settings o agente perde contexto de negócio — o mesmo trade-off da Fase 3, agora
por chamada em vez de por sessão.

## Fase 4 — Recolocar só sob falha repetida

Não recoloque a instrução na primeira falha. Recoloque na **segunda ocorrência do mesmo padrão** —
uma falha é ruído, duas é padrão. E ao recolocar, escreva a regra descrevendo a falha observada,
não a intenção genérica.

## Saída obrigatória

1. Tabela: item / tokens / invocações em 60d / classe / recomendação
2. Custo fixo total, antes e depois
3. Lista de cortes **com comando de reversão** (`git -C ~/.claude show main:rules/`)
4. O que foi deliberadamente **preservado** e por quê

## Anti-patterns

- Cortar por tamanho em vez de por uso · rule de segurança tratada como muleta porque "nunca disparou"
  (ela nunca disparou **porque** está lá) · adicionar rule para um erro que aconteceu uma vez ·
  medir só o arquivo e esquecer que `description` de skill entra em toda sessão · confundir
  ablação com deleção — ablação é teste, tem volta.
