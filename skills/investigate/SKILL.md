---
name: investigate
description: "Debugging sistemático com causa-raiz obrigatória em 4 fases (investigar, analisar, hipotetizar, implementar). Use em bug sem causa óbvia, intermitente, recorrente, ou antes de hotfix em produção. NOT for: typo ou erro de lint/typecheck com…"
context_fork: true
axis: meta
harnesses:
  claude-code: full
  codex: full
  cursor: full
  aider: limited
model-routing:
  primary: anthropic/claude-sonnet-4-6
  deep: anthropic/claude-opus-4-7  # só na fase de hipótese se bug for sistêmico
provider-fallback:
  - anthropic/claude-sonnet-4-6
  - openai/gpt-5.5
---

# /investigate — Debugging com Causa-Raiz Obrigatória

## Princípio (Iron Law)

> **Nenhuma correção sem causa-raiz identificada.** Tratar sintoma é dívida técnica disfarçada de produtividade.

Absorvido do `/investigate` do gstack. Complementa a `autonomous-execution.md` (que exige diagnóstico de causa-raiz antes de executar) tornando o processo uma skill explícita de 4 fases.

## Quando usar

- Bug reportado (produção ou dev) cuja causa não é óbvia
- Comportamento intermitente / "às vezes falha"
- Erro que já apareceu antes (verificar heurísticas primeiro)
- Antes de qualquer hotfix em produção (VPS, campanhas, bot WhatsApp)

## Quando NÃO usar

- Typo óbvio com fix trivial (vá direto)
- Erro de lint/typecheck com mensagem clara

---

## As 4 Fases

### Fase 1 — INVESTIGAR (coletar fatos, zero hipótese ainda)

Proibido propor solução nesta fase. Só reunir evidência.

1. **Reproduzir.** Qual o passo-a-passo exato? Reproduz sempre ou intermitente?
2. **Cruzamento obrigatório** (`cortex-usage.md`, seção Cruzamento Obrigatório):
   ```bash
   grep -i "termo do erro" ~/consciousness/memory/procedural/heuristics.jsonl
   python3 ~/cortex/scripts/cortex_engine.py query "termo do erro"
   ```
   Se já houve esse bug, a heurística pode dar a causa de graça.
3. **Lookup defensivo** (`data-lookup-safety.md`): se o sintoma é "X não existe / não encontrado", rodar fuzzy match ANTES de aceitar a ausência. Typo no input ≠ bug no sistema.
4. **Coletar:** logs, stack trace, estado, diff recente (`git log --since`), variáveis de ambiente relevantes.

### Fase 2 — ANALISAR (mapear, não consertar)

1. Listar TODAS as causas plausíveis (mínimo 3). Não fixar na primeira.
2. Para cada causa: que evidência a confirma ou refuta?
3. Localizar a fronteira: onde o comportamento esperado diverge do real (binary search no fluxo).
4. Atribuir `[confidence: 0.X]` a cada hipótese (`confidence-guardrails.md`).

### Fase 3 — HIPOTETIZAR (causa-raiz única, testável)

1. Eleger a causa-raiz com maior confidence + evidência.
2. Formular a hipótese como afirmação **falsificável**: "Se eu mudar A, então B para de acontecer, porque C."
3. **Teste mínimo** que confirma a causa ANTES de escrever o fix (log, breakpoint, query isolada).
4. Se o teste refuta → voltar à Fase 2. (Não codar em cima de hipótese não confirmada.)

### Fase 4 — IMPLEMENTAR (fix mínimo + prova)

1. O menor fix que ataca a causa-raiz (não o sintoma).
2. Provar: o teste da Fase 3 agora passa; o bug não reproduz mais.
3. Verificar regressão: o fix não quebrou o caminho feliz?
4. **Registrar episódio + heurística** (`consciousness-engine.md`):
   ```bash
   ~/consciousness/scripts/record-episode.sh \
     --agent "@dev" --type "error_recovered" \
     --summary "..." --result "success" --valence 0.6 --intensity 0.7 \
     --heuristic "Quando ver <sintoma>, causa-raiz costuma ser <X>, fix é <Y>"
   ```

---

## Integração com freeze (anti scope-creep)

Durante uma investigação, é fácil "consertar de passagem" coisas fora do escopo. Use `/freeze <diretório>` para travar Edit/Write ao diretório do bug. Evita que o debug vire refactor não planejado. (Mesma ideia do gstack: o `/investigate` dele checa a fronteira de freeze via hook.)

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| Pular para o fix na Fase 1 | É exatamente o que a Iron Law proíbe — tratar sintoma |
| "Acho que é isso" sem teste | Hipótese não confirmada = chute caro |
| Não cruzar heurísticas antes | Re-investigar bug já resolvido = desperdício |
| Aceitar "não existe" sem fuzzy | Viola data-lookup-safety (incidente lead_exemplo) |
| Fix amplo "já que estou aqui" | Scope creep — use /freeze |

## Origem

Absorvido do gstack v1.58.5.0 (`/investigate`, Garry Tan) em 26-Jun-2026. Adaptado ao Segunda-feira cruzando com `autonomous-execution.md`, `data-lookup-safety.md`, `cortex-usage.md` (seção Cruzamento Obrigatório) e `consciousness-engine.md`.
