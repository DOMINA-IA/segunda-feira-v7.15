---
id: crm-operado-por-agente-de-ia-10-padroes-arquiteturais
title: CRM operado por agente de IA — 10 padroes arquiteturais
type: playbook
axis: ops
status: active
created: '2026-08-10'
last_verified: '2026-08-10'
domain:
- product
- dev
agents:
- dev
- architect
- analyst
tags:
- crm
- agentes-ia
- kanban
- audit-trail
- clienteexemplo
decay_rate: 0.02
links:
- target: heuristic-dev-quando-o-cliente-diz-preciso-consumir-isso-ele-est-pedin
  type: auto-linked
- target: data-lookup-safety-full
  type: auto-linked
- target: briefing-2026-05-09
  type: auto-linked
- target: case-israel-king-domina-mai2026
  type: auto-linked
- target: feedback-clienteexemplo-tmv-funil-mai-2026
  type: related
- target: feedback-clienteexemplo-traffic-abril-2026
  type: related
- target: bug-slug-mismatch-endpoint-vs-tag-persistida
  type: related
- target: production-refactor-protocol-instrumenta-o-leve-antes-de-modulariza-o-full
  type: related
- target: workflow-execution
  type: related
- target: ids-principles
  type: related
- target: dashboard-data-freshness-toda-tabela-operacional-precisa-de-updated-at
  type: related
- target: external-api-patterns
  type: related
- target: CLIENTE_EXEMPLO-licoes-aprendidas
  type: related
- target: clienteexemplo-pacote-c-consolida-o-completa-abr-2026
  type: related
---

# CRM operado por agente de IA — 10 padroes arquiteturais

## Origem

Reel de @odanilogato (Instagram, 02-Ago-2026, 120s) demonstrando um CRM que se
auto-administra via agente de IA ("Isa"). Analisado frame a frame em 03-Ago-2026.
Peça de venda de mentoria (ASIA) — as telas são mockups de alta fidelidade, não
gravação de tela. O valor está na arquitetura demonstrada, não na prova de execução.

## Tese central

Inversão do fluxo de input. CRM tradicional: o humano trabalha, depois alimenta o
sistema (dupla digitação). Este: o humano trabalha, o sistema lê o trabalho onde ele
já acontece (WhatsApp, e-mail, Zoom/Meet) e se alimenta.

Frase de engenharia mais importante do vídeo: **"ele nasceu planejado pra ser operado
por agente de IA — tudo que eu faço clicando, a agente faz sozinha."** Não é feature,
é restrição de arquitetura assumida no dia zero.

## Os 10 padrões

1. **Paridade UI ↔ API como invariante.** Toda ação de interface existe como função
   chamável. Consequência prática: zero lógica de negócio dentro do handler do botão —
   handler e agente chamam o mesmo serviço. Aplicar no CLIENTE_EXEMPLO: extrair camada `services/`
   dos módulos que hoje renderizam e mutam estado no mesmo lugar.

2. **Todo campo precisa de fonte automática candidata antes de virar formulário.**
   Ao criar campo novo, primeira pergunta: "de qual fonte isso pode ser derivado?".
   Só vira input manual se não houver nenhuma.

3. **Ordenar por criticidade, não por cronologia.** A inbox reordena por urgência do
   negócio — inverso do padrão de todo feed. Já existe parcialmente na régua de
   cobrança do CLIENTE_EXEMPLO (fila do dia); falta aplicar às conversas.

4. **Audit trail do agente é feature de primeira classe, não log de debug.** Tela
   "Atividade da IA — tudo que a agente alterou no CRM", com hora e objeto afetado.
   É o que torna um card que se move sozinho confiável. Sem isso, automação vira
   ansiedade: ninguém sabe se o número está errado porque a IA errou ou porque
   alguém mexeu. PADRÃO MAIS TRANSFERÍVEL E MENOS COPIADO.

5. **Dois modos de execução: reflexo + ronda.** Eventos disparam reação imediata
   (chegou e-mail -> cria card); rondas periódicas varrem o board (reagendar follow-up,
   detectar negócio parado). Falham de formas diferentes — evento perde mensagem,
   ronda pega o que o evento perdeu. Espelha o heartbeat do Segunda-feira.

6. **A notificação é a interface principal; o CRM é backend.** O humano não abre o
   sistema — o sistema procura o humano (Telegram). Derruba o custo de adoção a quase
   zero. Conecta com o diagnóstico do CLIENTE_EXEMPLO: "adoção, não features".

7. **Header de coluna com soma de valor** ("3 negócios · R$ X.XXX") transforma
   kanban em previsão de receita sem relatório separado.

8. **O card carrega a própria urgência.** Semáforo no rodapé: "Follow up HOJE"
   (laranja) / "em 2 dias" (amarelo) / "em 9 dias" (verde).

9. **Card como dossiê, não como registro.** Acumula a timeline da relação (e-mail
   recebido -> negócio criado -> reunião de 42min com resumo -> proposta gerada),
   em vez de guardar só o estado atual.

10. **Sob medida vence prateleira quando o custo de construir cai.** "Não é melhor
    porque tem mais recurso, é melhor porque foi feito 100% pro meu jeito de
    trabalhar." Argumento de posicionamento pronto para CLIENTE_EXEMPLO vs CLIENTE_EXEMPLO.

## O furo de engenharia que o vídeo não menciona

Mover card porque a IA leu "Fechado!" no WhatsApp é um classificador sobre linguagem
ambígua — e não há menção a limiar de confiança, confirmação ou reversão. "Quase
fechado", "não fechou", "fechado com o outro fornecedor" produzem o mesmo gatilho.
Num card de R$ X.XXX, um falso positivo contamina forecast e dispara cobrança errada.

Mitigação: ação automática só acima de confiança alta; abaixo, a IA propõe e espera
um toque. Mesma matriz confidence x risco da rule `judgment.md`. O audit trail (#4)
existe justamente para socorrer o que passar.

## Outras ressalvas

- Mockups, não software rodando: valores redondos, mesmos 8 contatos em todas as telas.
- Ler o WhatsApp inteiro é bloqueante em LGPD quando há dado de paciente (CLIENTE_EXEMPLO).
- WhatsApp não-oficial = risco de ban de número (já sabido via Evolution API).
- Custo: 151 conversas classificadas por ronda exige triagem em modelo barato e
  modelo bom só no que passa do filtro.

## Telas inventariadas

Kanban "Negócios" (Novo lead / Reunião marcada / Proposta enviada / Fechado) ·
inbox unificada "Organizap" (WhatsApp + Email com filtros contados) · reordenação
animada por prioridade · conversa WhatsApp como gatilho · e-mail virando card ·
card-dossiê com resumo de reunião e HISTÓRICO · feed "Atividade da IA" · notificações
Telegram tipadas · proposta gerada + relatório da semana.

## Prioridade de adoção

Se escolher três: #4 (audit trail), #1 (paridade UI/API), #6 (notificação como
interface). Atacam o mesmo problema já diagnosticado no CLIENTE_EXEMPLO — sistema completo que
ninguém usa — por ângulos diferentes: confiança, extensibilidade e alcance.
Os de menor esforço e efeito mais visível: #7, #8 e #4 no CRM Diagnóstico.