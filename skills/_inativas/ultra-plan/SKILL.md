---
name: ultra-plan
description: "Guia de uso do Ultra Plan do Claude Code — processa o planejamento na nuvem da Anthropic, gerando planos mais rápidos, estruturados e com link compartilhável. Use quando for planejar um projeto novo do zero ou uma refatoração grande em um repositório conectado ao Git. NOT for: bug fix simples ou projeto sem Git — planeje localmente."
---

# Ultra Plan — Planejamento em Nuvem no Claude Code

Recurso do Claude Code que transfere o planejamento para a nuvem da Anthropic. Gera planos mais rápidos, mais estruturados e com link revisável na web.

---

## O que é

O Ultra Plan processa seu pedido de planejamento na nuvem em vez de localmente, resultando em:
- **Velocidade**: Significativamente mais rápido que planejamento local
- **Qualidade**: Planos mais detalhados e estruturados
- **Compartilhamento**: Link web para revisar e compartilhar com equipe
- **Multiagente**: Pode usar múltiplos modelos em paralelo

## Como Usar

```
/ultra plan [descrição detalhada do projeto]
```

### Exemplo Básico
```
/ultra plan Criar um dashboard de métricas de Meta Ads com Next.js + Supabase. 
Deve mostrar CPL, ROAS, investimento por campanha. 
Dados vêm do script ~/projetos/utm-manager/meta_ads.py.
Estilo visual: dark mode, JARVIS-like.
```

### Exemplo Detalhado (melhores resultados)
```
/ultra plan

## Projeto: Sistema de Follow-up Automatizado
## Stack: N8N + Claude API + WhatsApp (Evolution API) + PostgreSQL
## Objetivo: Lead entra pelo formulário → IA qualifica → sequência de 4 mensagens (D1, D3, D7, D14) → encaminha para closer se interesse detectado

## Requisitos:
1. Webhook que recebe lead do formulário (nome, email, telefone, interesse)
2. IA classifica urgência (hot/warm/cold) baseado no interesse declarado
3. Sequência personalizada por classificação
4. Dashboard simples para ver status dos leads
5. Integração com CRM existente (Supabase)

## Constraints:
- N8N self-hosted na VPS
- Máximo R$0,10 por lead processado (custo de API)
- WhatsApp via Evolution API (já configurado)
- Respeitar horário comercial (8h-18h)
```

## Dicas para Melhores Resultados

1. **Seja específico**: Quanto mais contexto, melhor o plano
2. **Declare a stack**: Mencionar tecnologias que já usa
3. **Liste constraints**: Orçamento, performance, limitações técnicas
4. **Defina o output**: O que o plano deve entregar (código, arquitetura, tasks)

## Requisitos

- **Git**: Projeto precisa estar conectado a um repositório Git online
- **Internet**: Precisa de conexão para processar na nuvem
- **Tamanho**: Pode ter problemas em projetos muito grandes (muitos arquivos)

## Quando Usar vs Não Usar

| Situação | Ultra Plan? | Alternativa |
|----------|------------|-------------|
| Projeto novo do zero | SIM | — |
| Refatoração grande | SIM | — |
| Bug fix simples | NÃO | Resolver direto |
| Projeto sem Git | NÃO | Planejamento local |
| Projeto gigante (10K+ arquivos) | TALVEZ | Planejar em partes |
| Precisa compartilhar plano | SIM | — |

## Outros Comandos Úteis (pouco conhecidos)

```
/powerup        # Guia rápido de aprendizado integrado
/insights       # Relatório HTML dos últimos 30 dias de uso
/cost           # Ver custo da sessão atual
/context        # Ver uso de contexto atual
/compact        # Comprimir contexto manualmente
```

### Otimização de Tokens — 3 Tiers (INEMA)

**T1 (Básico)**:
- `/clear` entre tarefas independentes
- Desconectar MCPs não usados na sessão
- Agrupar pedidos relacionados em uma mensagem
- Usar `/context` e `/cost` para monitorar

**T2 (Intermediário)**:
- Usar `/compact` antes de atingir 40% do contexto
- Preferir edits cirúrgicos a reescritas completas
- Estruturar pedidos com contexto mínimo necessário

**T3 (Avançado)**:
- PT-BR usa 20% mais tokens — considerar em sessões longas
- Init (CLAUDE.md) consome ~30% — planejar budget restante
- Para tarefas mecânicas: delegar para Haiku (model routing)
