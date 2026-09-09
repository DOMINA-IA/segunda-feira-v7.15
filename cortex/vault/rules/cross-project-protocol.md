# Cross-Project Protocol — Cruzamento Obrigatório de Padrões

> **Severidade:** SHOULD | **Aplica-se a:** Todos os agentes que executam tarefas
> **Origem:** Absorvido de Deus Sistêmico (Abr/2026) + Adaptado para Segunda-feira v7.1

## Princípio

Antes de executar qualquer tarefa não-trivial, o agente verifica se existe lição de outro contexto que se aplica. Isso previne erros já cometidos e transfere soluções validadas.

**Regra de ouro:** "A lição do projeto A se aplica aqui?"

---

## Protocolo

### Antes de executar tarefa significativa:

1. Consultar CORTEX: `python3 ~/cortex/scripts/cortex_engine.py query "termo da tarefa"`
2. Verificar heurísticas: `grep "termo" ~/consciousness/memory/procedural/heuristics.jsonl`
3. Se encontrar match: aplicar a lição e registrar micro-sinal

### Micro-sinal (inline, 1 linha):

```
[Cruzamento: lição de {contexto anterior} aplicada — {o que fez diferente}]
```

### Quando é obrigatório:

| Situação | Cruzamento obrigatório? |
|----------|------------------------|
| Story development | SIM — consultar heurísticas antes |
| Campanha/criativo novo | SIM — consultar feedback loop + patterns |
| Bug fix em área já problemática | SIM — verificar erros anteriores |
| Tarefa técnica trivial (lint, format) | NÃO |
| Resposta conversacional | NÃO |

## Onde buscar padrões

Hierarquia (mesma do cortex-usage.md):
1. CORTEX query (1 call)
2. Heurísticas procedurais
3. Feedback loop results
4. Patterns (ângulos, hooks, formatos)

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| Consultar sem aplicar | Cruzamento decorativo não previne nada |
| Consultar tudo para tudo | Overhead desnecessário em tarefas triviais |
| Ignorar heurística com confidence alta | Se já está validada, USE |
| Cruzamento genérico ("padrões aplicados") | Especificar QUAL lição e COMO aplicou |

## Integração

| Componente | Relação |
|-----------|---------|
| `cortex-usage.md` | Hierarquia de consulta (CORTEX primeiro) |
| `consciousness-engine.md` | Heurísticas como fonte de cruzamento |
| `feedback-loop.md` | Resultados reais como fonte de cruzamento |
