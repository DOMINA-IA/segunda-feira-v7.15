---
id: n8n-patterns
title: n8n Patterns — Padrões Obrigatórios para Workflows em Produção
type: rule
domain:
- ops
triggers:
- n8n
- webhook
- evolution api
- automação
- automacao
- hitl
- polling
- workflow
- fluxo
- disparar
- automático
- automática
- automatico
- automatica
- automatizar
- robô
- robo
- bot
- follow-up
- sozinho
- gatilho
links:
- target: confidence-guardrails-full
  type: auto-linked
- target: cross-collaboration-mandate
  type: auto-linked
- target: .archived-initiative-protocol
  type: auto-linked
- target: initiative-protocol
  type: auto-linked
---

# n8n Patterns — Padrões Obrigatórios para Workflows em Produção

---
name: n8n-patterns
severity: SHOULD
aplica-se-a: "@automation-architect, @workflow-orchestrator, @whatsapp-specialist"
origem: "Absorção INEMA 2026-06-28"
axis: ops
---

> **Severidade:** SHOULD | **Aplica-se a:** @automation-architect, @workflow-orchestrator, @whatsapp-specialist
> **Origem:** Absorção INEMA 2026-06-28 — padrões extraídos de 597 workflows n8n + boas práticas de agentes n8n em produção

## Princípio

Workflow sem error handling = bomba-relógio. Workflow sem contexto temporal = alucinação garantida. Workflow que age sem aprovação = risco operacional.

**Regra de ouro:** "Nenhum workflow vai para produção sem: error handler, $now no system prompt, e HITL em ações irreversíveis."

---

## Absorção INEMA (2026-06-28)

### 1. Error-Driven Architecture — Error Workflow em Todo Workflow de Produção

Todo workflow em produção DEVE ter um **Error Workflow** configurado (campo "Error Workflow" nas configurações do workflow raiz).

O Error Workflow captura e decide o que fazer:

```
Trigger: Error Trigger
  ↓
Set node:
  workflowId: {{ $json.workflow.id }}
  failedNode: {{ $json.execution.lastNodeExecuted }}
  errorMessage: {{ $json.error.message }}
  executionId: {{ $json.execution.id }}
  ↓
Switch (por tipo de erro):
  - Rate limit → Wait 60s → Retry via Webhook
  - Auth error → Notificar @devops via Telegram
  - Data error → Salvar em log + Notificar CEO
  - Unknown → Notificar + parar
```

**Nunca deixar workflow em produção sem error handling.** Erro silencioso = dado perdido + CEO não sabe.

Referência de integração: conectar Error Workflow ao mailbox `~/broadcast/mailbox/ops.json` via script Bash no n8n para cruzar com o Nervous System.

---

### 2. `$fromAI()` + `$now` Obrigatórios em Nodes de IA

**`$fromAI("campo", "descrição")`** — usar para todos os parâmetros que o agente deve preencher dinamicamente. Evita hardcode de valores que o LLM deveria inferir:

```javascript
// Correto:
body: $fromAI("email_body", "Escreva o email de follow-up personalizado para o lead")

// Errado (hardcoded, não personalizável):
body: "Olá, temos uma proposta para você..."
```

**`$now.format('MMMM dd, yyyy hh:mm a')`** — incluir SEMPRE no system prompt de qualquer node de IA. Modelos não têm acesso ao horário atual; sem isso, alucinam datas e calculam prazos errados:

```javascript
// System prompt padrão:
`Você é um agente de ${agente}. Data e hora atual: ${$now.format('DD/MM/YYYY HH:mm')} (BRT).`
```

Regra: nenhum node AI Agent ou LLM Chain vai para produção sem `$now` no system prompt.

---

### 3. HITL via Telegram/Slack — Aprovação Antes de Ação Irreversível

Antes de qualquer ação que não pode ser desfeita em <5 minutos, o workflow DEVE perguntar ao responsável via Telegram (ou Slack se configurado).

Padrão de implementação no n8n:

```
[Trigger] → [Preparar ação] → [Telegram: "Aprovar?"]
                                      ↓
                         [Wait for Webhook: /aprovar ou /negar]
                                      ↓
              [Switch: aprovado → Executar | negado → Cancelar + Log]
```

**Ações que EXIGEM HITL:**
- Publicar post em rede social
- Pausar/ativar campanha Meta Ads
- Enviar mensagem de follow-up WhatsApp para lead
- Gerar e enviar proposta comercial
- Deletar dados ou arquivos
- Fazer deploy em produção

**Timeout:** se aprovação não chegar em 30 minutos, workflow registra no mailbox `~/broadcast/mailbox/ops.json` e cancela a ação.

Isso implementa a `autonomous-execution.md` no contexto n8n: risco médio/alto exige aprovação humana.

---

### 4. Arquitetura 2-Workflows — Coletor Separado do Gerador

Nunca misturar captura de dados com geração de output no mesmo workflow. Separar em dois:

**Workflow 1 — COLETOR** (captura + normaliza):
- Recebe dados brutos (webhook, form, API externa)
- Valida, limpa e normaliza
- Salva em banco/Google Sheets/Airtable
- Emite evento para o Gerador via webhook interno ou fila

**Workflow 2 — GERADOR** (decide + entrega):
- Lê dados normalizados do banco
- Aplica lógica de negócio (elegibilidade, personalização, routing)
- Gera output (mensagem WhatsApp, email, post, proposta)
- Executa ação com HITL se necessário

**Por que separar:**
- Debug mais fácil: isola onde o dado entrou errado vs onde a decisão foi errada
- Escala independente: Coletor pode rodar a cada 1 minuto; Gerador só quando há batch
- Retry seguro: se Gerador falha, não perde os dados brutos (já estão no banco)

---

### 5. Polling Pattern — APIs Assíncronas (VAPI, Runway, Gamma)

APIs de geração (vídeo, áudio, imagem, apresentação) são assíncronas: o `POST /create` retorna um `job_id`, não o resultado final. Nunca tentar pegar o resultado no mesmo request do create.

Padrão correto no n8n:

```
[POST /create] → [Guardar job_id] → [Wait 30s]
                                          ↓
                               [GET /status/{job_id}]
                                          ↓
                              [IF status == "done"]
                              ├── SIM → [GET /result] → Continuar
                              └── NÃO → [IF tentativas < 10]
                                         ├── SIM → [Wait 30s] → voltar ao GET
                                         └── NÃO → Error Workflow
```

**Configurações de timeout por API:**
| API | Wait inicial | Max tentativas | Intervalo |
|-----|-------------|----------------|-----------|
| VAPI (voz) | 10s | 20 | 10s |
| Runway (vídeo) | 60s | 15 | 30s |
| Gamma (apresentação) | 20s | 10 | 15s |
| HeyGen (avatar) | 30s | 20 | 20s |

Após 10 tentativas sem resultado, acionar o Error Workflow.

---

### 6. Think Tool Pattern — Bloco Mental Antes de Agir

Adicionar uma ferramenta "Think" ao agente n8n como passo de raciocínio interno ANTES de qualquer ação com consequência:

```javascript
// Tool: think
// Description: "Use antes de agir. Liste: (1) regras relevantes, (2) informações que você tem, (3) o que está faltando, (4) sua decisão justificada."
// Input schema: { thought: string }
// Implementação: retorna o thought sem efeito colateral (é só um espaço de raciocínio)
```

No system prompt do agente, instruir explicitamente:
```
Antes de usar qualquer ferramenta que execute uma ação (enviar mensagem, criar registro, pausar campanha), use a ferramenta "think" para:
1. Listar as regras que se aplicam a esta situação
2. Confirmar que você tem todos os dados necessários
3. Avaliar o risco da ação
4. Decidir se prossegue ou pede aprovação humana
```

Referência: https://www.anthropic.com/engineering/claude-think-tool

O "think" não consome output tokens extras — é um scratchpad que melhora consistência em 40-60% segundo testes Anthropic.

---

### 7. Hierarquia 3 Níveis — Ferramentas, Subagentes, Agente Principal

Estrutura recomendada para workflows com IA complexa:

**Nível 1 — Ferramentas (Tools):**
- Funções simples e determinísticas
- Ex: `buscar_lead`, `formatar_mensagem`, `calcular_desconto`
- Implementadas como Function Call nodes no n8n
- Não chamam LLM

**Nível 2 — Agent Tools (Subagentes):**
- Agentes especializados com contexto próprio
- Ex: `agente_qualificador`, `agente_copywriter`, `agente_precificador`
- Conectados via `ai_tool` node ou webhook interno
- Cada um tem seu system prompt e ferramentas do Nível 1

**Nível 3 — Agente Principal (Orquestrador):**
- Recebe objetivo de alto nível do usuário/trigger
- Decide quais subagentes do Nível 2 acionar e em que ordem
- Tem acesso aos resultados de todos os subagentes
- Entrega resultado final ao usuário

**Conexão no n8n:** usar `ai_languageModel` para o LLM base de cada agente e `ai_tool` para conectar ferramentas e subagentes ao agente principal.

Esta hierarquia implementa o padrão multi-agente do Segunda-feira dentro do contexto n8n, mantendo separação de responsabilidades.

---

### 8. n8n MCP Server — Claude Code Cria Workflows via API

Claude Code pode criar, editar e listar workflows n8n diretamente via MCP:

```bash
# Instalar n8n MCP server
npm install -g n8n-mcp

# Configurar em ~/.claude/settings.json:
# {
#   "mcpServers": {
#     "n8n": {
#       "command": "n8n-mcp",
#       "env": { "N8N_BASE_URL": "http://localhost:5678", "N8N_API_KEY": "..." }
#     }
#   }
# }
```

Repositório: https://github.com/n8n-io/n8n-mcp

Complemento — n8n Skills (exemplos prontos para uso com Claude Code):
https://github.com/n8n-io/n8n-skills

**Capacidades via MCP:**
- Criar workflow a partir de descrição em linguagem natural
- Editar nodes específicos sem abrir o editor visual
- Listar e buscar workflows existentes
- Executar workflow via API e capturar output

**Quando usar:** ao criar automação nova para um cliente, usar MCP para gerar o esqueleto do workflow; depois refinar no editor visual para lógica de HITL e error handling.

---

## Anti-Patterns

| Anti-Pattern | Risco | Correção |
|-------------|-------|----------|
| Workflow sem Error Workflow | Erro silencioso, dado perdido | Sempre configurar Error Workflow antes de produção |
| Hardcode de parâmetros no node AI | Não personalizável, quebra com mudança de contexto | Usar `$fromAI()` para todos os campos dinâmicos |
| LLM sem `$now` no system prompt | Alucinação de datas e prazos | Sempre injetar `$now.format(...)` |
| PATCH/DELETE sem aprovação humana | Ação irreversível sem controle | Adicionar HITL com Telegram + timeout |
| GET no mesmo request do POST assíncrono | Retorna "pending" sempre, nunca pega resultado | Implementar Polling Pattern com Wait |
| Workflow único que coleta + processa + entrega | Debug impossível, sem retry seguro | Separar em Coletor e Gerador |
| Agente sem Think Tool em ações de risco | Decisão impulsiva sem checar regras | Adicionar ferramenta "think" + instruir no system prompt |
| Tudo em um único agente plano | Contexto explode, perda de especialização | Hierarquia 3 níveis com subagentes |

---

## Integração com Outras Rules

| Rule | Como interage |
|------|---------------|
| `autonomous-execution.md` | HITL no n8n implementa a matriz confidence×risco para agentes automáticos |
| `credentials-handling.md` | API keys n8n em `.env` (chmod 600), nunca hardcoded no workflow |
| `feedback-loop.md` | Resultados de workflows (CPL, leads gerados) alimentam `~/feedback-loop/results.json` |
| `consciousness-engine.md` | Workflows críticos registram episódio via Bash node ao completar |
| `axis-separation.md` | Workflows de campanha/conteúdo são OPS; workflows de infra/monitoring são META |
