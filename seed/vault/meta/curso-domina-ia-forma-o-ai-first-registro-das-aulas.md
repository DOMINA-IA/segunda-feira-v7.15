---
id: curso-domina-ia-forma-o-ai-first-registro-das-aulas
title: Curso DOMINA.IA — Formação AI-First (registro das aulas)
type: meta
status: active
created: '2026-05-06'
last_verified: '2026-05-06'
domain:
- meta
agents:
- content
- mentor
- sf-master
tags:
- domina-ia
- curso
- formacao
- ai-first
- aulas
- mentoria
decay_rate: 0.01
links:
- target: heuristic-dev-quando-um-sistema-materializa-dados-recorrentes-fixos-agend
  type: auto-linked
- target: whatsapp-bot
  type: auto-linked
- target: clienteexemplo-pacote-c-consolida-o-completa-abr-2026
  type: auto-linked
- target: skills-apresentacao
  type: auto-linked
- target: skills-apresentacao
  type: related
axis: meta
---

# Curso DOMINA.IA — Formação AI-First (registro das aulas)

# Curso DOMINA.IA — Formação AI-First

Curso de formação ministrado por ${CEO_NAME} toda **quarta às 20h-22h** (recorrente, calendário Google). Público: empresários da DOMINA.IA. Estilo: didático, analogias humanas, exemplos de empresário (não dev).

## Trilha completa

### ✅ AULA 1 — Criação (entregue)
**Tese:** Um agente sozinho, bem definido.
**Conceitos:** ROLE · CONTEXT · TASK · COLLABORATION (4 pilares).
**Arquivo HTML:** não localizado em ~/presentations/

### ✅ AULA 2 — Estruturação (entregue 08/Abr/2026)
**Tese:** O agente pronto pra colaborar.
**Conceitos:** 5 camadas, Protocols, Model Routing, Custos.
**Arquivo HTML:** ~/presentations/aula02-estruturacao-agentes.html (39KB)
**Versão PDF:** ~/presentations/aula02-pdf.html

### ✅ AULA 3 — Orquestração de Squads (entregue 29/Abr/2026)
**Tese:** Múltiplos agentes operando como time.
**Conceitos:** Composição (líder/executores/suporte), 3 modos de operação (Standard/Fork/Teammate), hand-off downstream (@sm → @po → @dev → @qa → @devops), sistema nervoso (Mailbox + Broadcast + Workspace Global), ignição coletiva (saliência ≥ 0.7 + 2+ agentes ressoam), 6 antipatterns.
**Arquivo HTML:** ~/presentations/aula03-orquestracao-squads.html (55KB, 15 slides)

### ✅ AULA 4 — Memória Persistente (entregue 06/Mai/2026 — HOJE)
**Tese:** Agentes que não esquecem — squad para de cobrar você toda semana.
**Conceitos:**
- 3 tipos de memória (analogias didáticas):
  - Episódica = 'Diário de bordo' (o que aconteceu)
  - Semântica = 'Manual da casa' (o que é verdade)
  - Procedural = 'Manhas do ofício' (como agir quando X)
- CORTEX como 'biblioteca da empresa' (395 notas, 1.354 links, 38 briefings)
- Busca por BM25 + Freshness ('Google pras suas notas, com prioridade pro fresco')
- Consciousness Engine = diário com valência ('como me senti')
- Heurísticas = 'cicatriz vira regra'
- Briefings = 'boletim do início do dia' (até 418 linhas pro @dev)
- Pipeline noturno = 'turno da noite' (5 etapas, 23:20-23:35 BRT)
- 6 antipatterns + 5 perguntas de fechamento
**Arquivo HTML:** ~/presentations/aula04-memoria-persistente.html (46KB, 15 slides)
**Versões anteriores:** v1 técnica (57KB) descartada por excesso de jargão; reescrita didática mantida.

### 🔜 AULA 5 — Em breve (próxima quarta)
**Tema sugerido (placeholder):** O squad em produção — aplicação ao negócio do aluno.
**Não confirmado.** Quando definir, atualizar esta nota.

## Padrões do curso (descobertos durante produção)

1. **Estrutura visual:** dark theme verde/teal, 15 slides por aula, tags de seção, layers, cards, glossário em rodapé (ou highlight didático), navegação keyboard + touch.
2. **CSS reutilizável:** mesmo arquivo de estilo entre aulas — design tokens em :root, slide.active/.exit, mode-badges, layers, cards, code blocks (quando técnico) ou story-cards (quando didático).
3. **Tom:** analogias humanas + exemplos de empresário > definições técnicas. Empresário entende quando vê.
4. **Pipeline de produção:**
   - Auditoria de dados (números reais do sistema, não placeholders) → roteiro → HTML → revisão → ajustes (didático/sem cliente).
   - Mentoria-autopilot grava aula via Meet, transcreve com Whisper, gera PDF didático com Claude e sobe pro Drive.
5. **Anti-cliente:** nunca citar nome de cliente em slide (CLIENTE_EXEMPLO, CLIENTE_EXEMPLO, ${PESSOA}, CLIENTE_EXEMPLO, CLIENTE_EXEMPLO). Trocar por 'projeto', 'campanha', 'deploy'.

## Como usar esta nota
Quando ${CEO_NAME} mencionar 'aula', 'mentoria DOMINA.IA', 'aula de quarta' ou 'preparar próxima aula' — ESTA é a primeira fonte de contexto. Trazer:
1. O que já foi entregue (recap até a última aula).
2. Continuidade lógica (próxima aula da trilha).
3. Padrão visual e tom validados.
4. Restrição anti-cliente.