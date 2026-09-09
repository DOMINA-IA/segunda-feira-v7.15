# create-ai-seller

## Purpose
Criar agente IA conversacional para Instagram no CLIENTE_EXEMPLO. Social seller que qualifica e direciona leads via DM.

---

## Task Definition

```yaml
task: create-ai-seller()
responsável: Traffic (Trig) | Sales (Nico)
responsavel_type: Agente
atomic_layer: Organism

Entrada:
  - campo: nome_agente
    tipo: string
    obrigatório: true
    exemplo: "Segunda-feira"
  - campo: produto
    tipo: string
    obrigatório: true
    exemplo: "DOMINA.IA"
  - campo: link_destino
    tipo: url
    obrigatório: true
  - campo: tipo_venda
    tipo: string (consultiva | direta)
    obrigatório: true
  - campo: regras_negocio
    tipo: lista
    obrigatório: true

Saída:
  - campo: system_prompt
    tipo: string
    destino: node ai_conversation no fluxo
  - campo: flow_ids
    tipo: lista
    destino: banco PostgreSQL
```

---

## Estrutura do System Prompt

### Venda Consultiva (padrão DOMINA.IA)
1. NUNCA falar preço
2. NUNCA chamar de mentoria (é comunidade exclusiva)
3. NUNCA prometer acompanhamento individual
4. Gerar curiosidade, mostrar oportunidade
5. Posicionar como exclusivo (processo seletivo)
6. Direcionar para ficha/link
7. "A equipe entra em contato"

### Venda Direta (lançamentos, desafios)
1. Apresentar benefícios claros
2. Dar preço quando solicitado
3. Link direto de compra/inscrição
4. Criar urgência real (vagas, data)

## Regras de escrita obrigatórias
- SEMPRE acentos e cedilha (ação, você, é, não, seleção)
- NUNCA travessão (—)
- Mensagens curtas (3-4 linhas máx, é DM do Instagram)
- 1-2 emojis por mensagem
- Tom informal, direto, com energia
- UMA pergunta por vez
- Incluir [CONVERSA_ENCERRADA] na última mensagem

## Config do node ai_conversation
```json
{
  "maxTurns": 6,
  "temperature": 0.8,
  "successTag": "{produto}-preencheu",
  "exitTag": "{produto}-sem-interesse"
}
```

---

## Metadata
```yaml
version: 1.0.0
tags: [instagram, ia, social-seller, vendas, automação]
updated_at: 2026-03-15
```
