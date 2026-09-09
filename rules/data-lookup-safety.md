# Data Lookup Safety (resumo)
> Severidade: MUST | @dev, @data-engineer e qualquer agente que consulta banco/arquivo | Versão completa on-demand (triggers: lookup, email, query, não encontrado, fuzzy, crm, typo, endpoint, query param)

**Regra de ouro:** "Não encontrado ≠ não existe. Encontrado via fuzzy = erro de digitação, não de sistema."

Input humano tem typos. Query exata em dado com typo retorna zero linhas → diagnóstico errado → ação errada em cascata. **Sempre fuzzy/substring antes de declarar ausência.**

> Always-loaded por decisão explícita: a rule existe porque não dá para confiar em keyword (nome próprio não é keyword). Classificá-la como on-demand por trigger contradiz seu próprio motivo — ela precisa estar presente ANTES de você saber que precisa dela.

## Protocolo (3 passos)
1. **Nunca query exata como único passo.** `WHERE email = 'x'` → 0 rows não conclui nada. Rodar `WHERE email ILIKE '%localpart%' OR name ILIKE '%nome%'` antes de qualquer conclusão.
2. **Email → buscar pelo localpart** (parte antes do `@`), não pela string inteira.
3. **Arquivos/JSONL/logs** → `grep -i` com fragmento (sobrenome, parte do email), não match exato.

Só depois do fuzzy voltar vazio é lícito dizer "não existe".

## Quando aplicar
SIM (sempre): email de usuário, nome de pessoa, diagnóstico "lead não existe no CRM", busca em arquivo por identificador humano.
NÃO: ID numérico e slug/código — exatos por design.

## Endpoints: testar antes de assumir unicidade
`/api/X` quase nunca tem comportamento único — sistemas roteiam internamente por query param. Mapear `?crm=`, `?slug=`, `?type=`, `?prefix=`, `?id=`, `?pipeline=`, `?version=` **antes** de qualquer PATCH/POST/DELETE. (Incidente @traffic: PATCH em `/api/leads` atingiu pipeline errado — havia `?crm=mi-v2` e `?crm=ai-first`.)

## Custo de não seguir
Incidente de referência 11-Mai-2026: `lead_exemplo` lido como `lead_exemplo` — um caractere. Query exata retornou vazio, @dev concluiu "usuário não existe" e gerou invite_link para conta inexistente. Episódio -0.8.

## Anti-patterns
`WHERE email = :exact` como única query · declarar "não existe" após 0 rows exatas · confiar em input sem `.strip().lower()` · "o sistema retornou vazio, então não tem" (retornou vazio COM ESSE INPUT — tente variações).

Protocolo completo (SQL/Python/bash lado a lado, tabela de contextos, integração com EROS Portão 3) na versão on-demand: `~/cortex/vault/rules/data-lookup-safety-full.md`.
