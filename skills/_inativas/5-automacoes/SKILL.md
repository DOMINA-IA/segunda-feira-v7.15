---
name: 5-automacoes
description: "Gera as 5 automações que mais vendem para qualquer nicho — Speed to Lead, Processamento de Docs, Follow-up, Reativação de Base, Relatórios. Baseado no framework INEMA TDS. Use para criar material de curso, proposta para cliente, ou implementação real."
---

# 5 Automações que Vendem — Framework INEMA TDS

> "Empresas não pagam por automações mirabolantes. Pagam por soluções simples que resolvem problemas reais." — INEMA

---

## As 5 Automações Universais

Estas 5 automações funcionam para qualquer nicho porque resolvem problemas universais de negócio.

### 1. Speed to Lead (Resposta Instantânea)

**Problema**: Lead entra pelo formulário/WhatsApp e espera 2h+ para resposta. A cada minuto de demora, conversão cai 7%.

**Automação**: Lead entra → IA responde em <30s com mensagem personalizada → qualifica → agenda ou encaminha.

**Stack**: N8N webhook + Claude API + WhatsApp (Evolution API) ou Email

#### Prompts por Nível

**Básico** (qualquer nicho):
```
Você é um assistente de atendimento. Um novo lead acabou de entrar.
Nome: {{nome}}
Origem: {{origem}}
Interesse: {{interesse}}

Responda de forma acolhedora em no máximo 3 frases:
1. Cumprimente pelo nome
2. Confirme o interesse
3. Faça UMA pergunta de qualificação
```

**Intermediário** (com contexto):
```
Você é o assistente virtual da [EMPRESA]. Tom: profissional mas próximo.

Novo lead:
- Nome: {{nome}}
- Canal: {{canal}}
- Página de origem: {{url}}
- Horário: {{hora}}

Regras:
- Se horário comercial (8h-18h): agendar conversa com consultor
- Se fora do horário: coletar telefone e informar que retornaremos
- NUNCA mencionar preço
- Sempre terminar com próximo passo claro
```

**Contextualizado (nicho clínica)**:
```
Você é a assistente virtual da Clínica [NOME]. Especialidade: [ESPECIALIDADE].

Novo paciente interessado:
- Nome: {{nome}}
- Procedimento de interesse: {{interesse}}
- Canal: {{canal}}

Regras:
- Chamar pelo nome
- Confirmar interesse no procedimento
- Perguntar se já realizou procedimento similar antes
- NÃO dar diagnóstico ou orientação médica
- Oferecer agendamento de avaliação gratuita
- Tom: empático, profissional, sem termos técnicos
```

---

### 2. Processamento de Documentos (Extração Inteligente)

**Problema**: Empresa recebe PDFs, contratos, notas fiscais, laudos e alguém precisa ler e extrair dados manualmente.

**Automação**: Documento chega (email/upload) → IA extrai campos relevantes → preenche planilha/CRM → notifica responsável.

**Stack**: N8N + Claude API (vision para PDFs) + Google Sheets ou DB

#### Prompts por Nível

**Básico**:
```
Examine o documento a seguir e extraia:
1. Tipo de documento
2. Data
3. Valores mencionados
4. Partes envolvidas
5. Principais obrigações ou itens

Formato: JSON estruturado.
```

**Intermediário**:
```
Você é um especialista em documentos. Extraia os campos abaixo do documento:

Campos obrigatórios:
{{lista_de_campos}}

Regras:
- Se campo não encontrado: marcar como "NÃO ENCONTRADO"
- Se valor ambíguo: extrair as duas interpretações
- Formatar datas como DD/MM/AAAA
- Formatar valores monetários como número (sem R$)
- Confidence score para cada campo extraído
```

**Contextualizado (escritório contábil)**:
```
Você é assistente contábil. Processe a nota fiscal e extraia:

1. CNPJ emitente
2. CNPJ destinatário
3. Número da NF
4. Data de emissão
5. Valor total
6. CFOP
7. Base de cálculo ICMS
8. Valor ICMS
9. Itens (descrição, quantidade, valor unitário)

Classificar automaticamente:
- Categoria fiscal: compra/venda/serviço/devolução
- Centro de custo sugerido
- Alerta se valor > R$ X.XXX (requer atenção especial)

Output: JSON + resumo executivo em 2 linhas.
```

---

### 3. Follow-up / Nutrição (Sequência Inteligente)

**Problema**: 80% dos leads precisam de 5+ toques para converter. Maioria das empresas faz 1-2 follow-ups e desiste.

**Automação**: Lead entra na sequência → IA envia mensagens espaçadas (D1, D3, D7, D14) → personaliza por comportamento → identifica momento de compra.

**Stack**: N8N cron + Claude API + WhatsApp/Email + CRM

#### Prompts por Nível

**Básico**:
```
Escreva uma mensagem de follow-up para {{nome}}.
Contexto: entrou em contato há {{dias}} dias, interessado em {{produto}}.
Mensagem anterior: {{ultima_msg}}

Regras:
- Máximo 3 frases
- Não repetir o que já foi dito
- Terminar com pergunta aberta
- Tom: amigável, não insistente
```

**Intermediário**:
```
Sequência de nutrição para {{nome}}.
Dia da sequência: D{{dia}}
Produto: {{produto}}
Ticket: {{valor}}
Interações anteriores: {{historico_resumido}}

Estratégia por dia:
- D1: Valor educativo (insight relevante)
- D3: Prova social (resultado de cliente similar)
- D7: Escassez suave (vagas/prazo)
- D14: Última tentativa (oferta especial ou fechamento)

Gere a mensagem para D{{dia}} seguindo a estratégia.
Tom: consultivo, como um amigo que sabe do assunto.
```

**Contextualizado (mentoria de IA)**:
```
Nutrição para lead DOMINA.IA:
- Nome: {{nome}}
- Profissão: {{profissao}}
- Dia: D{{dia}}
- Dor principal: {{dor}}

Gere mensagem WhatsApp seguindo:
- D1: "{{nome}}, vi que você [ação]. Sabia que [insight de IA para profissão]?"
- D3: "Nosso aluno [nome], que também é [profissão], [resultado concreto]."
- D7: "A próxima turma da mentoria começa [data]. São apenas [N] vagas."
- D14: "[nome], última chance antes de fecharmos. Posso te explicar como funciona em 5 min?"

Regras DOMINA.IA:
- Sempre citar IA + resultado financeiro
- Nunca parecer robô
- Emojis: máximo 1 por mensagem
- CTA: sempre com próximo passo claro
```

---

### 4. Reativação de Base (CRM Inteligente)

**Problema**: Empresa tem 5.000 contatos no CRM que nunca mais foram tocados. Dinheiro parado.

**Automação**: Filtrar base por critérios → IA gera mensagem personalizada por perfil → enviar em lotes → rastrear respostas → encaminhar interessados.

**Stack**: N8N + CRM/Google Sheets + Claude API + WhatsApp/Email

#### Prompts por Nível

**Básico**:
```
Crie uma mensagem de reativação para {{nome}}.
Último contato: {{data_ultimo_contato}}
Produto anterior de interesse: {{produto}}

Tom: casual, como se estivesse retomando uma conversa antiga.
Máximo 2 frases + 1 pergunta.
```

**Intermediário**:
```
Reativação segmentada:
- Segmento: {{segmento}} (ex: "comprou há 6 meses", "abandonou carrinho", "pediu orçamento")
- Nome: {{nome}}
- Histórico: {{resumo_historico}}
- Novidade desde último contato: {{novidade}}

Gere mensagem que:
1. Reconecte (referência ao passado)
2. Apresente novidade relevante
3. Crie curiosidade
4. NÃO venda diretamente — reative o interesse

Formato: WhatsApp (curto, direto, informal).
```

**Contextualizado (e-commerce)**:
```
Reativação de cliente e-commerce:
- Nome: {{nome}}
- Última compra: {{produto}} em {{data}}
- Valor gasto total: R${{valor_total}}
- Categoria favorita: {{categoria}}

Gere mensagem:
"{{nome}}, [referência pessoal ao produto comprado]. 
Acabamos de lançar [novidade na categoria favorita]. 
[Oferta exclusiva para clientes antigos]."

Regras:
- Cupom exclusivo: VOLTA{{primeiras_3_letras_nome}}
- Desconto: 15% se gasto total > R$500, 10% se menor
- Validade: 48h (urgência real)
```

---

### 5. Relatórios Internos (Inteligência Automática)

**Problema**: Gestor precisa de relatório semanal mas ninguém tem tempo de montar. Dados espalhados em 5 ferramentas.

**Automação**: Cron semanal → coleta dados de N fontes → IA faz a síntese e gera relatório → envia por email/Slack/WhatsApp.

**Stack**: N8N cron + APIs das ferramentas + Claude API + Email/Slack

#### Prompts por Nível

**Básico**:
```
Gere um relatório semanal com os seguintes dados:

{{dados_brutos}}

Formato:
1. Resumo executivo (3 frases)
2. Métricas principais (tabela)
3. O que melhorou vs semana anterior
4. O que piorou
5. 3 ações recomendadas para próxima semana
```

**Intermediário**:
```
Relatório executivo semanal — Semana {{número}} de {{ano}}

Dados coletados:
- Vendas: {{dados_vendas}}
- Marketing: {{dados_marketing}}
- Atendimento: {{dados_atendimento}}
- Financeiro: {{dados_financeiro}}

Gere relatório com:
1. Score geral da semana (1-10) com justificativa
2. Top 3 vitórias
3. Top 3 alertas
4. Comparação vs semana anterior (% variação)
5. Previsão próxima semana (tendência)
6. Ações prioritárias (máximo 3, com responsável sugerido)

Tom: objetivo, sem enrolação. CEO lê em 2 minutos.
```

**Contextualizado (agência de marketing)**:
```
Relatório semanal — Agência [NOME]

Clientes ativos: {{lista_clientes}}
Dados por cliente:
{{dados_por_cliente}}

Para cada cliente gerar:
1. Investimento vs resultado (ROAS)
2. CPL e variação vs semana anterior
3. Melhor e pior campanha
4. Alerta se CPL > meta definida
5. Sugestão de otimização (1 por cliente)

Consolidado geral:
- Receita total da agência
- Margem estimada
- Clientes em risco (performance caindo 2+ semanas)
- Clientes para upsell (performance subindo)

Formato: Markdown formatado para envio por email.
```

---

## Como Usar esta Skill

### Para Material de Curso/Mentoria
1. Escolher nicho do aluno
2. Gerar os 3 níveis de prompt para cada automação
3. Adaptar exemplos para o nicho específico
4. Incluir stack sugerido (ferramentas)

### Para Proposta de Cliente
1. Identificar quais das 5 automações o cliente precisa
2. Gerar prompts contextualizados para o nicho dele
3. Estimar tempo de implementação:
   - Speed to Lead: 4-8h
   - Processamento de Docs: 8-16h
   - Follow-up: 8-12h
   - Reativação: 4-8h
   - Relatórios: 8-16h

### Para Implementação Real
1. Configurar N8N workflow
2. Inserir prompt contextualizado
3. Conectar canais (WhatsApp, Email, CRM)
4. Testar com 10 leads/docs antes de escalar
5. Monitorar por 1 semana → ajustar prompts

---

## Precificação Sugerida (Referência INEMA)

| Automação | Preço mínimo | Preço premium |
|-----------|-------------|---------------|
| Speed to Lead | R$ X.XXX | R$ X.XXX |
| Processamento Docs | R$ X.XXX | R$ X.XXX |
| Follow-up/Nutrição | R$ X.XXX | R$ X.XXX |
| Reativação de Base | R$ X.XXX | R$ X.XXX |
| Relatórios | R$ X.XXX | R$ X.XXX |
| **Pacote 5 automações** | **R$ X.XXX** | **R$ X.XXX** |

> Insight INEMA: "A venda não é da automação. É do tempo que o dono recupera e da receita que para de perder."
