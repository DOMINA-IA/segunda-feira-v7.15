---
id: playbook-trafego
title: Playbook de Tráfego Pago — Conhecimento de Especialistas
type: playbook
domain:
- traffic
agents:
- traffic
tags:
- tráfego
- playbook
- sobral
status: active
created: '2026-04-12'
last_verified: '2026-04-12'
decay_rate: 0.02
links:
- target: pixel-rollout-safe-fases
  type: auto-linked
- target: rules-trafego
  type: auto-linked
- target: playbook-israel-king-trafego
  type: auto-linked
- target: specialists
  type: auto-linked
migrated_from: $HOME/.claude/projects/-HOME-/memory/playbook-trafego.md
old_description: Frameworks e estratégias de Pedro Sobral, Alex Hormozi, Brian Manon
  e Motion para Meta Ads, escalabilidade, criativos e geração de leads
axis: ops
---

# Playbook de Tráfego Pago — Knowledge Base

Compilado de frameworks dos maiores especialistas em tráfego pago e geração de leads. Atualizado em 12/03/2026.

---

## 1. Pedro Sobral — O Maior Gestor de Tráfego do Brasil

### 3 Tipos de Campanha (Framework Central)

| Tipo | Objetivo | Quando Usar |
|------|----------|-------------|
| **Campanha de Teste** | Descobrir o que funciona | Sempre que testar novo criativo, público ou oferta |
| **Campanha de Escala** | Aumentar resultado do que já funciona | Quando tem criativo/público validado com CPL dentro da meta |
| **Campanha de Manutenção** | Manter resultado estável | Campanhas que já performam — NÃO MEXER |

### Regras de Teste (Sobral)

1. **Teste 1 variável por vez** — nunca mudar criativo E público ao mesmo tempo
2. **Budget de teste:** 2x a 3x o CPL alvo por dia, por ad set
3. **Tempo mínimo:** 48h antes de tirar conclusão (ciclo de aprendizado do Meta)
4. **Regra de pausa:** Se gastou 2x CPL alvo e CPL > 30% acima da meta → PAUSA
5. **Nunca religar campanha pausada** — duplicar e começar de novo
6. **Escalar = duplicar**, não aumentar budget individual

### Métricas Sobral (Hierarquia)

1. **CPL (Custo por Lead)** — métrica #1 para captação
2. **CPA (Custo por Aquisição)** — métrica #1 para venda
3. **ROAS** — retorno sobre investimento em ads
4. **CTR** — indicador de qualidade do criativo (>1% feed, >0.5% stories)
5. **Frequência** — se > 3.5 = criativo cansando, pausar
6. **CPM** — custo por mil impressões (indicador de competição no leilão)

### Análise de Conta (Framework Sobral)

- **Nota 8-10:** CPL dentro/abaixo da meta, escala limpa, criativos diversificados
- **Nota 6-7:** CPL próximo da meta, dependência de 1 criativo, fase de teste OK
- **Nota 4-5:** CPL acima da meta, desperdício > 30% em testes ruins
- **Nota 0-3:** Sem criativo validado, sem estrutura, queimando dinheiro

### Preparação para Tarifas Meta (PIS/COFINS + ISS)

- **Aumento:** 12.15% nos custos de anúncio no Brasil
- **Ações:**
  1. Aumentar budget em 12-15% para manter o mesmo volume
  2. Focar em criativos de alta conversão (CTR alto = CPM efetivo menor)
  3. Testar Advantage+ (Meta otimiza melhor com orçamento maior)
  4. Diversificar: Google Ads, TikTok Ads como backup
  5. Monitorar CPL diário — se subir >15%, ajustar imediatamente

---

## 2. Alex Hormozi — Blueprint de Geração de Leads

### Grand Slam Offer (Framework de Oferta Irresistível)

**Fórmula:** Valor = (Resultado Sonhado × Probabilidade Percebida) ÷ (Tempo × Esforço)

Para aumentar valor da oferta:
1. **Aumentar resultado sonhado** — promessa mais específica e desejável
2. **Aumentar probabilidade percebida** — prova social, garantia, cases
3. **Diminuir tempo percebido** — "em 5 dias", "em 30 dias"
4. **Diminuir esforço percebido** — "passo a passo", "feito para você"

### 4 Canais de Geração de Leads

| Canal | Tipo | Custo | Velocidade |
|-------|------|-------|------------|
| **Warm Outreach** | 1-to-1, lista existente | Grátis | Rápido |
| **Cold Outreach** | 1-to-1, lista fria | Baixo | Médio |
| **Content** | 1-to-many, orgânico | Tempo | Lento mas compounding |
| **Paid Ads** | 1-to-many, pago | $$$ | Rápido e escalável |

### Lead Magnet (7 Tipos que Convertem)

1. **Checklist/Cheatsheet** — rápido de consumir, alta conversão
2. **Mini-curso gratuito** — alta percepção de valor
3. **Template/ferramenta** — valor imediato e prático
4. **Desafio X dias** — engajamento + compromisso (NOSSO CASO)
5. **Webinar/aula ao vivo** — autoridade + urgência
6. **Quiz/diagnóstico** — personalização + curiosidade
7. **Comunidade gratuita** — pertencimento + nurturing

### Modelo de Follow-up 5 Toques

1. **Toque 1 (imediato):** Confirmação + entrega do lead magnet
2. **Toque 2 (D+1):** Conteúdo de valor relacionado
3. **Toque 3 (D+2):** Case/prova social
4. **Toque 4 (D+3):** Objeção principal respondida
5. **Toque 5 (D+5):** Oferta com urgência

### Regra de Hormozi para Ads

> "Se seu CPL é R$5 e seu produto custa R$ X.XXX, você precisa de 200 leads para 1 venda (0.5% conversão). Isso custa R$ X.XXX em ads. ROI = 0. Para ser lucrativo com 2% de conversão, precisa de 50 leads = R$250 em ads. ROI = 3x."

**Implicação para Desafio MI:**
- CPL R$4.30 × 480 leads = R$ X.XXX em ads
- Se 5% convertem para produto de R$997 = 24 vendas = R$ X.XXX
- ROAS projetado: ~11.6x (excelente)

---

## 3. Brian Manon — Facebook Ads Scaling 2026

### Framework de Escala

#### Escala Vertical (aumentar budget)
- **Regra dos 20%:** Máximo 20% de aumento a cada 24-48h
- **Por quê:** Aumentos maiores resetam o aprendizado do algoritmo
- **Exceção:** Advantage+ tolera aumentos de até 30% (otimização mais robusta)

#### Escala Horizontal (duplicar campanhas)
- **Duplicar campanha inteira** — nunca apenas o ad set
- **Espaçar duplicações:** mínimo 24h entre cada
- **Monitorar canibalização:** se CPL sobe em TODAS as duplicações, o público está saturado

### Creative Velocity (Velocidade de Criativos)

| Budget Mensal | Criativos Novos/Semana | Variações/Semana |
|---------------|----------------------|------------------|
| < R$5K | 2-3 | 4-6 |
| R$5K-R$20K | 5-8 | 10-15 |
| R$20K-R$100K | 10-15 | 20-30 |
| > R$100K | 15-25 | 30-50 |

**Para nosso budget (R$3K/12 dias):**
- ~2 criativos novos/semana é suficiente
- ~4-6 variações (cores, headlines, CTAs diferentes)

### Sinais de Fadiga de Criativo

1. **CPL sobe >20% em 3 dias consecutivos**
2. **CTR cai >30% vs média histórica**
3. **Frequência > 3.5 no período**
4. **CPM sobe sem mudança de budget**

**Ação:** Não pausar imediatamente. Primeiro testar nova variação do mesmo ângulo. Se 2 variações falharem, trocar o ângulo.

---

## 4. Motion — Framework de Teste de Criativos (3 Fases)

### Fase 1: Pre-Flight (Conceito)

- **Objetivo:** Validar o CONCEITO antes de gastar em produção
- **Budget:** Mínimo viável (R$10-20/dia por criativo)
- **Tempo:** 48-72h
- **Métrica decisiva:** CTR + CPL
- **Decisão:**
  - CTR > 1% E CPL < meta → APROVADO para Fase 2
  - CTR > 1% MAS CPL > meta → Testar LP diferente
  - CTR < 1% → REPROVAR conceito

### Fase 2: Competitive (Variações)

- **Objetivo:** Encontrar a melhor execução do conceito aprovado
- **O que variar:**
  1. Headlines (3-5 variações)
  2. Imagens/vídeos (2-3 variações)
  3. CTAs (2 variações)
  4. Formatos (story vs feed vs reels)
- **Budget:** 2-3x o da Fase 1
- **Tempo:** 5-7 dias
- **Decisão:** Top 2-3 variações vão para Fase 3

### Fase 3: Scaling (Escala)

- **Objetivo:** Maximizar resultado dos winners
- **Ações:**
  1. Duplicar campanhas com winners
  2. Testar em públicos diferentes (lookalike 1%, 3%, 5%)
  3. Aumentar budget gradualmente (regra dos 20%)
  4. Monitorar fadiga diariamente
- **Quando parar:** CPL > meta por 3 dias consecutivos

### Hierarquia de Impacto em Performance

1. **Oferta** (maior impacto) — o que você está oferecendo
2. **Ângulo/Hook** — como você apresenta a oferta
3. **Formato** — vídeo vs imagem vs carrossel
4. **Copy** — headline + body text
5. **Design/Execução** (menor impacto) — cores, fontes, layout

**Implicação:** Sempre testar conceitos/ângulos ANTES de variações visuais.

---

## 5. Aplicação Prática — Desafio MI

### Status Atual (12/03/2026)
- Ângulo campeão validado: "R$3K a R$30K" (CPL R$2.98-R$4.26)
- Estamos na **Fase 3 (Scaling)** do framework Motion
- Creative velocity adequada: 2 novos criativos (V5) + duplicação do campeão

### Próximos Passos Recomendados

1. **Monitorar V5 por 48h** — se CPL < R$5, escalar
2. **Se V5 funcionar:** duplicar V5 em 48h (nova campanha)
3. **Se V5 não funcionar:** criar mais 2 variações do ângulo campeão com headlines diferentes
4. **Dia 18/03 (5 dias antes):** aumentar budget total em 20% para push final
5. **Dia 20/03 (3 dias antes):** remarketing de quem visitou a LP mas não converteu
6. **Follow-up pós-inscrição:** sequência de 5 toques (Hormozi) para aumentar show-up rate

### Regras de Decisão Rápida

| Situação | Ação |
|----------|------|
| CPL < R$4 por 48h | Duplicar campanha |
| CPL R$4-R$5 por 48h | Manter rodando |
| CPL R$5-R$7 por 48h | Observar mais 24h |
| CPL > R$7 por 48h | PAUSAR |
| Frequência > 3.5 | Criar variação do criativo |
| CTR < 0.5% | Trocar headline/hook |
| Novo criativo CTR > 1.5% | Winner potencial, dar budget |

---

## Fontes

- Pedro Sobral: Blog (pedrosobral.com.br), YouTube, metodologia de tráfego
- Alex Hormozi: "$100M Leads" book, YouTube, acquisition.com
- Brian Manon: YouTube, Facebook Ads scaling guides 2026
- Motion: Creative analytics platform, blog (motionapp.com)
- Social Media Examiner: Meta Ads strategy articles
- Meta Business: Documentação oficial sobre tarifas PIS/COFINS/ISS