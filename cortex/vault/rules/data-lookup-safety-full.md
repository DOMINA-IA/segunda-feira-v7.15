---
id: data-lookup-safety-full
title: Data Lookup Safety — Busca Defensiva (completo)
type: rule
domain:
- dev
agents:
- dev
- data-engineer
tags:
- lookup
- fuzzy-match
- query
- crm
triggers:
- lookup
- email
- query
- não encontrado
- fuzzy
- crm
- busca defensiva
- typo
- usuário não existe
status: active
created: '2026-05-24'
last_verified: '2026-07-07'
decay_rate: 0.01
on_demand: true
axis: meta
links:
- target: heuristic-dev-quando-um-sistema-tem-so-o-caminho-da-excecao-implementado
  type: auto-linked
- target: crm-operado-por-agente-de-ia-10-padroes-arquiteturais
  type: auto-linked
- target: clienteexemplo-migra-o-da-agenda-do-CLIENTE_EXEMPLO-418-eventos
  type: auto-linked
- target: dashboard-data-freshness-toda-tabela-operacional-precisa-de-updated-at
  type: related
- target: external-api-patterns
  type: related
---

# Data Lookup Safety — Busca Defensiva Antes de Declarar "Não Encontrado"

> **Severidade:** MUST | **Aplica-se a:** @dev, @data-engineer, e qualquer agente que executa queries em bancos de dados ou arquivos
> **Origem:** Incidente 11-Mai-2026 — @dev criou invite_link errado para `lead_exemplo` quando email real era `lead_exemplo`. Typo no input humano não foi detectado porque a query usou match exato. Promovido de heurística (@dev, conf 0.95, 12 validações) a rule em 24-Mai-2026.

## Princípio

Input humano tem typos. Query exata em dado com typo retorna "não encontrado" — diagnóstico errado, ação errada. **Sempre fazer fuzzy/substring match antes de declarar ausência.**

**Regra de ouro:** "Não encontrado != não existe. Encontrado via fuzzy = erro de digitação, não de sistema."

---

## Protocolo Obrigatório — Lookup por Nome ou Email

### Passo 1 — Nunca query exata como único passo

```sql
-- ❌ Errado: query exata como único passo
SELECT * FROM users WHERE email = 'usuario@example.com';
-- Resultado: 0 rows → diagnóstico "usuário não existe" → ERRADO

-- ✅ Correto: fuzzy match primeiro
SELECT * FROM users
WHERE email ILIKE '%otasantana%'
   OR email ILIKE '%santana82%';
-- Resultado: usuario@example.com → TYPO DETECTADO
```

### Passo 2 — Substring do localpart para email

```python
# Extrair localpart (parte antes do @) e buscar por substring
localpart = email.split('@')[0]
results = db.query(
    "SELECT * FROM users WHERE email ILIKE %s OR name ILIKE %s",
    (f"%{localpart}%", f"%{name_input}%")
)
if not results:
    # Só agora declarar "não encontrado"
    return "usuário não existe"
```

### Passo 3 — Em arquivos JSONL / logs

```bash
# Busca exata → sem resultado → NÃO concluir "não existe"
grep "usuario@example.com" arquivo.jsonl

# Busca fuzzy com localpart
grep -i "parte-do-email" arquivo.jsonl
grep -i "sobrenome" arquivo.jsonl
```

---

## Quando Aplicar

| Contexto | Aplicar? |
|----------|---------|
| Query por email de usuário | **SIM — sempre** |
| Query por nome de pessoa | **SIM — sempre** |
| Query por ID numérico | NÃO — IDs são exatos por design |
| Query por slug/código | NÃO — slugs são determinísticos |
| Busca em CORTEX por termo | SIM (CORTEX já faz FTS por padrão) |
| Diagnóstico "lead não existe no CRM" | **SIM — verificar fuzzy antes** |

---

## Custo de Não Seguir

| Consequência | Exemplo real |
|-------------|-------------|
| Diagnóstico errado | "usuário não existe" quando é typo |
| Ação errada em cascade | invite_link gerado para conta inexistente |
| Retrabalho + vergonha | CEO confronta com evidência do erro |
| Perda de confiança no sistema | "o agente disse que não existe, mas estava lá" |

Incidente referência: `lead_exemplo` vs `lead_exemplo` (11-Mai-2026) — um caractere de diferença.

---

## Anti-Patterns

| Anti-pattern | Correção |
|-------------|----------|
| `WHERE email = :exact` como única query | Adicionar `OR email ILIKE '%:localpart%'` |
| Declarar "registro não existe" após 0 rows exatas | Rodar fuzzy antes de concluir |
| Confiar em input do usuário sem normalizar | `.strip().lower()` antes de qualquer lookup |
| "O sistema retornou vazio, então não tem" | Sistema retornou vazio COM ESSE INPUT — tente variações |

---

## Endpoints: Testar Antes de Assumir Unicidade

> **Origem:** Heurística @traffic, 10 validações. Incidente: assumiu que `/api/leads` era único — havia `/api/leads?crm=mi-v2`, `/api/leads?crm=ai-first` etc. PATCH atingiu pipeline errado.

**Antes de assumir que `/api/X` tem comportamento único, testar com query params variados:**

```bash
# Descobrir variações de comportamento do endpoint
curl -s "https://api.exemplo.com/api/leads" | jq .total
curl -s "https://api.exemplo.com/api/leads?crm=mi-v2" | jq .total
curl -s "https://api.exemplo.com/api/leads?crm=ai-first" | jq .total
curl -s "https://api.exemplo.com/api/leads?type=organic" | jq .total
curl -s "https://api.exemplo.com/api/leads?prefix=RJ" | jq .total
```

**Params a sempre testar:** `?crm=`, `?slug=`, `?type=`, `?prefix=`, `?id=`, `?pipeline=`, `?version=`

**Regra:** sistemas modernos usam o mesmo endpoint base com params para roteamento interno. "Um endpoint" quase sempre significa "múltiplos comportamentos via params". Mapear ANTES de qualquer PATCH/POST/DELETE.

---

## Integração com outras rules

| Rule | Como interage |
|------|---------------|
| `eros-quality.md` | Portão 3 (Execução): query sem fuzzy fallback = E4 (dados incorretos potenciais) |
| `cortex-usage.md` (seção Cruzamento Obrigatório) | Heurística validada 12x — cruzamento obrigatório antes de qualquer diagnóstico de "não existe" |
| `consciousness-engine.md` | Incidente 11-Mai gerou episódio -0.8; heurística foi extraída e validada em múltiplas sessões |