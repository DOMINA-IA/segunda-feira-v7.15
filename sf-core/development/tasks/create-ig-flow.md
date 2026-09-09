# create-ig-flow

## Purpose
Criar fluxo de automação Instagram no CLIENTE_EXEMPLO (trigger + nodes + edges no formato correto do DB).

---

## Task Definition

```yaml
task: create-ig-flow()
responsável: Traffic (Trig)
responsavel_type: Agente
atomic_layer: Organism

Entrada:
  - campo: nome
    tipo: string
    obrigatório: true
  - campo: keyword
    tipo: string
    obrigatório: true
  - campo: canais
    tipo: lista (dm, comment, story_reply)
    obrigatório: true
  - campo: tipo_resposta
    tipo: string (send_message | ai_conversation)
    obrigatório: true
  - campo: system_prompt
    tipo: string (se ai_conversation)
    obrigatório: false

Saída:
  - campo: flow_ids
    tipo: lista de UUIDs
    destino: banco PostgreSQL (tabela flows)
```

---

## FORMATO CORRETO DOS NODES (CRÍTICO)

Baseado no fluxo "IA Conversacional - Stories TESTE" que funciona:

```json
{
  "id": "trigger_1",
  "type": "trigger",
  "position": {"x": 400, "y": 50},
  "measured": {"width": 210, "height": 118},
  "data": {
    "label": "Story Reply: KEYWORD",
    "keywords": ["keyword", "Keyword", "KEYWORD"],
    "matchType": "contains",
    "triggerType": "story_reply",
    "replyComment": false,
    "replyText": ""
  }
}
```

### Node types (snake_case obrigatório):
- `trigger` (não triggerNode)
- `send_message` (não sendMessage)
- `add_tag` (não addTag)
- `ai_conversation` (não aiConversation)
- `condition`
- `delay`
- `randomizer`

### Edges (SEM sourceHandle):
```json
{"id": "e1", "source": "trigger_1", "target": "tag_lead"}
```

### Trigger config (match_type snake_case):
```json
{"type": "dm", "config": {"keywords": ["ficha"], "match_type": "contains"}}
```

## Execução

### 1. Criar script Node.js com o fluxo
### 2. Upload para VPS via SCP
### 3. Executar: `cd /opt/CLIENTE_EXEMPLO && node {script}.js && rm {script}.js`
### 4. Verificar no Flow Builder do CLIENTE_EXEMPLO

## Atenção
- Conversas AI ativas bloqueiam novos fluxos para o mesmo usuário
- Encerrar com: `UPDATE ai_conversations SET status = 'completed' WHERE status = 'active'`
- Keyword case: incluir variações (ficha, Ficha, FICHA)

---

## Metadata
```yaml
version: 1.0.0
tags: [instagram, flow, CLIENTE_EXEMPLO, automação]
updated_at: 2026-03-15
```
