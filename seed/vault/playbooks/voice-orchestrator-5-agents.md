---
id: voice-orchestrator-5-agents
title: Agente de Voz Orquestrador — Arquitetura 5 Agentes Modular
type: playbook
domain:
- voice-ai
- agents
- whatsapp
agents:
- voice-ai-specialist
- automation-architect
- whatsapp-specialist
- architect
tags:
- voice-ai
- multi-agent
- orchestration
- inema-derived
- voice-orchestrator
status: active
created: '2026-05-10'
last_verified: '2026-05-10'
decay_rate: 0.03
source: inema-delta-2026-05-10
links:
- target: inema-knowledge
  type: derived_from
- target: pre-llm-validation-layer
  type: relates_to
- target: pre-llm-validation-layer
  type: related
axis: meta
---

# Agente de Voz Orquestrador — 5 Agentes

> Origem: INEMA_AGENTES 06-Mai-2026. Discussão de arquitetura para atendimento de voz que NÃO depende de solução premium única (ElevenLabs all-in). Modular, econômico, escalável.

## Princípio

Um "agente de voz único e mágico" é caro e travado. Quebrar em 5 agentes especializados:
- Cada um com função clara
- Pode trocar provedor de cada camada sem refazer tudo
- Custo cai 5-10x vs solução all-in (ElevenLabs)
- Voz só quando vale a pena (decidido pelo orquestrador)

## A Arquitetura

```
                    ┌─────────────────────────┐
                    │  1. AGENTE ORQUESTRADOR │
                    │  (cérebro principal)    │
                    └──────────┬──────────────┘
                               │
        ┌──────────────────────┼─────────────────────┐
        │                      │                     │
        ▼                      ▼                     ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ 2. STT/Entrada│ │ 3. SDR/Atendimento│ │ 4. Ferramentas   │
│ voz → texto   │ │ pensar + decidir   │ │ APIs/CRM/agenda  │
└──────────────┘  └──────────────────┘  └──────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ 5. TTS/Saída     │
                    │ texto → voz      │
                    └──────────────────┘
```

## Os 5 Agentes em Detalhe

### 1. Orquestrador
- **Função:** decide quem age, em que canal (texto/voz), se transfere para humano
- **Não fala nem ouve:** só coordena
- **Provedor:** Claude Code ou GPT-5 (raciocínio)
- **Input:** evento (mensagem, ligação, formulário)
- **Output:** roteamento + decisões

### 2. STT (Speech to Text) — Entrada
- **Função:** transcrever voz do cliente
- **Provedores:** Whisper (local, grátis), Deepgram (cloud, premium), Parakeet (NVIDIA, GPU local)
- **Hack:** word_timestamps habilitado para fallback de pontuação
- **Latência meta:** <500ms

### 3. SDR / Atendimento
- **Função:** cérebro da conversa, decide o que responder
- **Provedor:** Claude Sonnet 4.6 ou GPT-5-mini (custo/qualidade)
- **Skills:** consultar agenda, CRM, base de conhecimento
- **Tom:** profissional, consultivo, direto, acolhedor (calibrado para mentoria)
- **Anti-padrão:** não inventar preços, prazos, promessas

### 4. Ferramentas / Integrações
- **Função:** executar ações que o SDR pede
- **Stack:** n8n workflows + APIs diretas (Calendar, CRM, Stripe, etc)
- **Auditável:** cada chamada vira execution log
- **Recursos:** agendar, criar lead, enviar proposta, abrir chamado

### 5. TTS (Text to Speech) — Saída
- **Função:** sintetizar voz da resposta
- **Provedores:** ElevenLabs (premium), MiniMax 2.8 (custo médio, emoção), Gemini TTS (grátis)
- **Decisão de qualidade:** Orquestrador decide se vale TTS premium ou ASCII
- **Hack:** cachear vozes recorrentes (saudação, despedida, confirmações)

## Decisão Crítica do Orquestrador

```
Cliente envia: "Quanto custa?"

Orquestrador analisa:
  - Lead já qualificado? (contexto memória)
  - Hora pico ou madrugada? (afeta TTS premium)
  - Lead pago vs grátis? (alocar voz boa para pago)
  - Responder por TEXTO ou VOZ?

Se TEXTO: SDR responde direto via WhatsApp/Telegram
Se VOZ: SDR escreve resposta → TTS → ENVIA áudio
```

## Aplicação a DOMINA.IA

### Caso 1 — Bot WhatsApp Atual
Hoje WhatsApp Bot é monolítico (Claude AI no CLIENTE_EXEMPLO). Migrar para arquitetura 5-agentes resolve:
- Custo escalável (texto barato, voz só quando vale)
- Trocar TTS sem refatorar bot
- Adicionar canal voz (LiveKit) sem rewrite

### Caso 2 — Atendimento AI FIRST (futuro)
Lead entra no funil → Orquestrador qualifica → se hot → liga via VAPI → SDR conversa → agenda discovery do ${CEO_NAME}

### Caso 3 — Atendimento Cliente Mentoria
Aluno do Programa AI FIRST manda dúvida no WhatsApp → Orquestrador roteia → SDR consulta knowledge base do programa → responde no canal mais eficiente

## ROI Estimado

| Stack | Custo/mês 100 leads | Qualidade |
|-------|--------------------|-----------|
| ElevenLabs all-in | ~R$ X.XXX | Alta |
| 5 agentes (Whisper+Sonnet+MiniMax) | ~R$200 | Média-alta (com cache) |
| 5 agentes (Whisper+Sonnet+Gemini) | ~R$80 | Média |

Economia: ~85% para volume médio.

## Heurística Derivada

> Quando montar atendimento de voz, NUNCA usar solução premium all-in. Decompor em 5 camadas independentes (Orquestrador, STT, SDR, Ferramentas, TTS). Por quê: custo 5-10x menor + flexibilidade para trocar provedor por camada. Como aplicar: começar pelo Orquestrador (decide canal); evoluir camada por camada conforme volume justificar.

## Stack Recomendada para Piloto DOMINA

| Camada | Provedor | Custo | Razão |
|--------|---------|-------|-------|
| Orquestrador | Claude Sonnet 4.6 | ~R$50/100 leads | Raciocínio + custo |
| STT | Whisper local | R$0 | Já temos pipeline |
| SDR | Claude Sonnet 4.6 | (compartilhado) | Coerência de tom |
| Ferramentas | n8n existente | R$0 | Reuso |
| TTS | MiniMax 2.8 | ~R$40/100 leads | Emoção + custo |

Total: ~R$90/100 leads com voz qualificada.

## Fontes

- INEMA_AGENTES 06-Mai-2026 (4 mensagens longas com arquitetura completa)
- `~/projetos/telegram-scraper/output/INEMA_AGENTES/messages.md`