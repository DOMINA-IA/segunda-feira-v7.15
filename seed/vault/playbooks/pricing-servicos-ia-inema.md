---
name: pricing-ia-consultoria-inema
type: playbook
axis: ops
tags: [pricing, consultoria, ofertas]
origem: Absorção INEMA 2026-06-28
agents: [offer-engineer]
created_at: 2026-06-28
links:
  - posicionamento-identidade-futuro
---

# Pricing de Serviços de IA (INEMA, validado)

Benchmark de precificação validado pelo INEMA para serviços de implementação e consultoria de IA. Aplicar diretamente nas montagens de stack de valor pelo @offer-engineer.

---

## Manutenção Mensal

**Faixa:** R$500–1.000/mês

**Por que nunca R$400 como "tudo incluído":** esse valor não cobre overhead real de suporte (tickets, ajustes contínuos), reuniões semanais, monitoramento de automações e eventuais correções de fluxo. Abaixo de R$500 é doação disfarçada de serviço — erosão de margem invisível que só aparece no final do trimestre.

**O que inclui no contrato mensal padrão:**
- SLA de resposta 48h
- Reunião semanal de acompanhamento (30–45min)
- Ajustes dentro do escopo predefinido (não é desenvolvimento novo)
- Relatório mensal de performance das automações

---

## Projetos Avulsos

**Fórmula:** `$150/hora × estimativa pessimista × markup de 1,1 a 1,4`

**Por que estimativa pessimista:** projetos de IA têm escopo que naturalmente expande conforme a implementação avança — integrações inesperadas, ajustes de prompt, retreinamento de modelos. A estimativa pessimista já é o piso; o markup cobre imprevistos e margem real.

**Faixas de markup por contexto:**
- 1,1 → projeto simples, escopo fechado, cliente experiente
- 1,2–1,3 → projeto médio, alguma ambiguidade, primeira entrega com cliente
- 1,4 → projeto complexo, escopo aberto, cliente sem experiência com IA

---

## Separação Obrigatória de Contratos

**NUNCA misturar assessoria mensal com projetos avulsos em um único contrato.**

| Modelo | Características | Faturamento |
|--------|----------------|-------------|
| **Assessoria mensal fixa** | SLA 48h, reunião semanal, escopo predefinido e fixo | Mensal recorrente, contrato por período (mínimo 3 meses) |
| **Projetos avulsos** | Escopo por entregável, precificado individualmente | Por projeto, contrato separado a cada novo escopo |

**Por que separar:** misturar os dois cria "tudo incluído" implícito. O cliente começa a tratar o contrato mensal como licença para solicitar projetos novos sem custo adicional. Resultado: escopo ilimitado + receita fixa + margem negativa ao final do mês.

---

## Consultoria de 15min — Porta de Entrada

**Canal:** Calendly público, slot de 15 minutos, sem barreiras de entrada (sem formulário longo, sem pré-qualificação pesada).

**Função:** diagnóstico rápido que demonstra autoridade antes do pitch formal. O lead chega "buscando ajuda" e sai sabendo que precisa de você.

**Padrão de conversão:**
- 4 slots de 15min preenchidos em um dia → ~$1.000 em propostas geradas
- Taxa de conversão do slot para proposta: 60–80% (lead já qualificado pelo simples ato de agendar)
- Ticket médio do projeto originado: R$ X.XXX–8.000 dependendo do escopo

**Protocolo do slot de 15min:**
1. Ouvir a dor em 5 minutos (não interromper)
2. Diagnosticar causa raiz + nomear o problema com precisão
3. Apresentar o escopo de solução em 3 minutos
4. Fechar com proposta ou próximo passo em 2 minutos
5. Nunca terminar o slot sem um "próximo passo" definido

---

## Anti-Patterns de Precificação

| Anti-pattern | Problema | Correção |
|-------------|---------|----------|
| "R$400/mês tudo incluído" | Margem negativa após 2ª reunião extra | R$500 mínimo, escopo escrito e fixo |
| Estimativa otimista em projetos | Promessa que não cabe no prazo | Sempre estimativa pessimista × markup |
| Contrato único para recorrente + projeto | Cliente trata projeto como incluso | Dois contratos, duas assinaturas |
| Consultoria gratuita sem limite | Drena tempo sem gerar projeto | Slot pago ou limitado (Calendly) |
| Desconto na primeira venda | Ancora expectativa de preço baixo | Desconto via bônus, nunca via redução de tabela |
