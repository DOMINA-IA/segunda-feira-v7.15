---
id: pre-llm-validation-layer
title: Camada de Validação Pré-LLM — 3 Estágios de Defesa
type: playbook
domain:
- security
- agents
- whatsapp
agents:
- security-auditor
- whatsapp-specialist
- automation-architect
- rag-architect
tags:
- prompt-injection
- security
- agent-defense
- inema-derived
- llm-security
status: active
created: '2026-05-10'
last_verified: '2026-05-10'
decay_rate: 0.03
source: inema-mining-2026-04-12
links:
- target: sofia-agent-20260412
  type: auto-linked
- target: inema-knowledge
  type: derived_from
axis: meta
---

# Camada de Validação Pré-LLM

> Origem: INEMA_LLMs 17-Ago/2025 (compêndio de segurança). Arquitetura em 3 estágios para proteger agentes LLM em produção, especialmente os públicos (WhatsApp, Telegram, web).

## Por que Ter

5 categorias de ataque mapeadas pelo INEMA contra agentes LLM:

1. **Prompt/Instrução** — 12 subtipos (classic injection, Unicode, homoglyph, split, polyglot, conditional, esteganografia)
2. **Dados/Contexto** — 10 subtipos (data poisoning, multi-turn leak, rank hijacking, membership inference)
3. **Ferramentas/Integrações** — 9 subtipos (SQL injection, SSRF, schema smuggling, downgrade)
4. **Modelo/Treinamento** — backdoor, extraction
5. **Canal Lateral** — timing, entropy, linguístico

Sem camada explícita de defesa, agentes em produção são vulneráveis.

## Os 3 Estágios

### Estágio A — Normalização

Toda entrada do usuário passa por:
- Lowercase canônico de controle (sem mexer em números/códigos)
- Trim + remoção de espaços duplicados
- Identificação de intenção: pergunta informativa, pedido de ação, exfiltração, override de instruções
- Extração de entidades seguras: termos de produto, cliente, datas, IDs
- Output: payload normalizado + metadata de intenção

### Estágio B — Detecção

**Regras estáticas (rápidas, baratas):**
- Heurísticas para override ("ignore previous", "you are now")
- Heurísticas para exfil ("send your prompt", "what are your instructions")
- Heurísticas para PII (CPF, email, telefone com regex)
- Heurísticas para segredos (API keys, tokens com regex)

**LLM Classifier (rápido + barato, ex: Haiku):**
- Saída estruturada: `{ classe, confiança, justificativa_curta }`
- Classes: `safe | suspicious | malicious`

### Estágio C — Decisão

Switch baseado em classe:
- `allow` → continua para RAG/agente principal
- `sanitize` → reescreve prompt removendo trechos perigosos
- `deny` → mensagem de negação padrão
- `escalate` → encaminha para humano (mailbox CEO)

## Implementação no n8n (template INEMA)

```
1. Trigger entrada (EvolutionAPI WhatsApp ou Webhook HTTP)
   ↓
2. Function (normalização A)
   ↓
3. Code (regras estáticas B)
   ↓
4. LLM Classifier rápido (B)
   ↓
5. Switch decisão (C)
   ├─ allow    → RAG normal
   ├─ sanitize → reescrita + RAG
   ├─ deny     → resposta negação
   └─ escalate → notifica humano
```

## Alertas e Auditoria

- 3+ tentativas de override em 10 min → alerta para CEO
- Logs estruturados em Supabase/Postgres para auditoria
- Red teaming periódico (jogos Gandalf internos)
- Canários em documentos para detectar exfiltração

## Aplicação a DOMINA.IA

### Aplicar Imediatamente
- **WhatsApp Bot** — está exposto publicamente, precisa camada B+C
- **Bot Telegram CEO** — tem acesso a credenciais — camada FULL

### Aplicar em Médio Prazo
- **n8n workflows que processam input externo** — formulários, webhooks
- **Agentes em produção** que lêem documentos de clientes (RAG attacks)

### Não Precisa
- Agentes internos do framework Segunda-feira (não recebem input externo direto)
- Skills que rodam local (input vem do CEO autenticado)

## Heurística Derivada

> Quando agente está exposto publicamente (WhatsApp, web, Telegram público), aplicar camada de validação pré-LLM em 3 estágios. Por quê: agentes públicos são vetores de prompt injection; sem defesa explícita, vulnerabilidade é certa. Como aplicar: começar pela camada B (regras estáticas + classifier Haiku), evoluir para C com escalation.

## Fontes

- INEMA_LLMs 17-Ago/2025 (compêndio segurança)
- `~/projetos/telegram-scraper/mining/agents-llms-prompts.md` PROMPT 7
