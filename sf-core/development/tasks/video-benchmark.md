# Video Benchmark — Pesquisa de Mercado para Produção de Vídeo

## Purpose

Executar pesquisa de mercado completa para produção de vídeo com IA: identificar os melhores perfis do nicho, extrair os vídeos com maior performance, transcrever e analisar padrões (hooks, CTAs, estrutura, tom de voz, gatilhos).

## Task Definition (AIOS Task Format V1.0)

```yaml
task: videoBenchmark()
agent: "@video-producer"
responsável: Dash
atomic_layer: Research

elicit: true

inputs:
  - name: nicho
    type: string
    required: true
    validation: "Nicho/tema do conteúdo (ex: IA para negócios, marketing digital, fitness)"
  - name: num_perfis
    type: number
    required: false
    default: 10
    validation: "Quantidade de perfis para pesquisar (5-20)"
  - name: num_videos
    type: number
    required: false
    default: 5
    validation: "Quantidade de melhores vídeos por perfil (3-10)"
  - name: plataforma
    type: enum
    required: false
    default: instagram
    options: [instagram, tiktok, youtube]
    validation: "Plataforma alvo para benchmark"

outputs:
  - name: benchmark_report
    type: file
    location: "docs/video-production/benchmarks/{nicho}-benchmark.md"
    persistido: true
  - name: transcricoes
    type: file
    location: "docs/video-production/benchmarks/{nicho}-transcricoes.md"
    persistido: true
  - name: padroes_extraidos
    type: file
    location: "docs/video-production/benchmarks/{nicho}-padroes.json"
    persistido: true
```

## Pre-Conditions

```yaml
pre-conditions:
  - [ ] Nicho definido e claro
    tipo: pre-condition
    blocker: true
    validação: "Usuário forneceu nicho específico"
  - [ ] Acesso a ferramentas de scraping (Playwright/Apify) ou dados manuais
    tipo: pre-condition
    blocker: false
    validação: "Se não tiver scraper, usuário fornece perfis e dados manualmente"
```

## Interactive Elicitation Process

### Step 1: Nicho e Objetivo

```
ELICIT: Nicho e Objetivo do Benchmark

Qual é o nicho/tema que você quer pesquisar?

Exemplos:
- "IA para negócios"
- "Marketing digital com IA"
- "Fitness e saúde"
- "Crypto e finanças"

E qual o objetivo? (criar vídeos para seu perfil, para cliente, para ads?)

→ Validation: Nicho não pode ser genérico demais
→ Default: Baseado no contexto do perfil @${CEO_INSTAGRAM}
```

### Step 2: Perfis de Referência (opcional)

```
ELICIT: Perfis de Referência

Você já tem perfis específicos que quer analisar?

Se sim, liste os @usernames. Se não, eu vou pesquisar os melhores do nicho.

→ Validation: Lista de 1+ perfis ou "pesquisar automaticamente"
→ Default: Pesquisa automática
```

### Step 3: Plataforma e Formato

```
ELICIT: Plataforma Alvo

Qual plataforma você quer focar?

1. Instagram (Reels) — padrão
2. TikTok
3. YouTube (Shorts ou Long-form)

→ Validation: Opção válida
→ Default: Instagram
```

## Implementation Steps

### Step 1: Identificar Top Perfis do Nicho

**Objetivo:** Encontrar os 10 melhores perfis do nicho na plataforma alvo.

**Critérios de seleção:**
- Engajamento alto (não apenas seguidores)
- Conteúdo recente (últimos 3 meses)
- Estilo de vídeo com IA ou formato replicável
- Mix de perfis grandes (100k+) e médios (10k-100k)

**Output:**
```markdown
| # | Perfil | Seguidores | Engajamento | Nicho Específico | Por que incluir |
|---|--------|-----------|-------------|-----------------|----------------|
| 1 | @perfil | 150k | 3.2% | IA + Negócios | Hooks virais |
```

### Step 2: Extrair Melhores Vídeos de Cada Perfil

**Objetivo:** Para cada perfil, extrair os 5 vídeos com mais views/engagement.

**Dados a extrair por vídeo:**
- URL do vídeo
- Número de views
- Número de likes
- Número de comentários
- Número de compartilhamentos (se disponível)
- Número de saves (se disponível)
- Descrição/caption
- Data de publicação
- Duração

**Ordenação:** Por likes (do mais curtido ao menos curtido)

**Output:**
```markdown
### Perfil: @username

| # | Views | Likes | Comments | Shares | Duração | Descrição (resumo) |
|---|-------|-------|----------|--------|---------|-------------------|
| 1 | 250k | 15k | 432 | 1.2k | 28s | "Como usar IA para..." |
```

### Step 3: Transcrever Todos os Vídeos

**Objetivo:** Transcrever cada vídeo e organizar com metadados.

**Formato de transcrição:**
```markdown
## Vídeo {n} — @{username}

**Métricas:** {views} views | {likes} likes | {comments} comments
**Duração:** {duração}
**URL:** {url}

### Transcrição Completa
{transcrição com timestamps}

### Análise Estrutural
- **Hook (0-3s):** {texto do hook}
- **Tipo de hook:** {pergunta|estatística|provocação|promessa|before-after|curiosidade}
- **Corpo:** {estrutura: problema→solução, storytelling, tutorial, etc.}
- **CTA:** {tipo de CTA e texto}
- **Tom de voz:** {direto|provocativo|educativo|inspiracional|urgente}
- **Gatilhos mentais:** {escassez|autoridade|prova social|curiosidade|medo|ganância}
- **Palavras-chave repetidas:** {lista}
```

### Step 4: Análise de Padrões

**Objetivo:** Cruzar dados de todos os vídeos para identificar padrões de alta performance.

**Padrões a extrair:**

1. **Hooks que performam:**
   - Top 5 tipos de hook por engajamento
   - Palavras-gatilho mais usadas nos melhores hooks
   - Duração média do hook nos top performers

2. **Estruturas de vídeo:**
   - Estrutura mais comum nos top 10 vídeos
   - Pacing médio (cortes/segundo)
   - Duração ideal por plataforma

3. **CTAs efetivos:**
   - Tipos de CTA com mais conversão (comentário, follow, DM)
   - Posição do CTA (final, meio, múltiplos)
   - Texto dos melhores CTAs

4. **Tom e linguagem:**
   - Tom predominante nos vídeos virais
   - Vocabulário comum
   - Nível de informalidade

5. **Visual patterns:**
   - Tipo de vídeo (talking head, B-roll, screencast, animação)
   - Uso de legendas/captions
   - Qualidade visual (produção alta vs. raw)

**Output JSON:**
```json
{
  "nicho": "string",
  "data_analise": "ISO date",
  "total_perfis": 10,
  "total_videos": 50,
  "padroes": {
    "hooks": {
      "top_tipos": [
        {"tipo": "provocação", "frequencia": "35%", "engajamento_medio": "4.2%"},
        {"tipo": "estatística", "frequencia": "25%", "engajamento_medio": "3.8%"}
      ],
      "palavras_gatilho": ["você", "pare", "cuidado", "segredo", "ninguém"],
      "duracao_media_hook": "2.8s"
    },
    "estruturas": {
      "mais_comum": "hook → problema → solução → CTA",
      "duracao_ideal": "28-35s",
      "pacing_medio": "corte a cada 3.2s"
    },
    "ctas": {
      "top_tipos": [
        {"tipo": "comentário", "frequencia": "45%"},
        {"tipo": "follow", "frequencia": "30%"}
      ],
      "melhor_cta_texto": "Comenta X que eu mando no DM"
    },
    "tom": {
      "predominante": "provocativo-educativo",
      "informalidade": "alta",
      "vocabulario_top": ["mano", "tá ligado", "porra", "sacada"]
    },
    "visual": {
      "tipo_predominante": "talking_head + B-roll IA",
      "legendas": "95% usam",
      "qualidade": "mix de raw + produzido"
    }
  },
  "recomendacoes": [
    "Usar hooks de provocação — 35% mais engajamento",
    "Duração ideal: 28-35s para Reels",
    "CTA de comentário gera mais interação"
  ]
}
```

### Step 5: Gerar Relatório Final

**Objetivo:** Consolidar tudo em relatório acionável.

**Estrutura do relatório:**

```markdown
# Benchmark: {nicho} — {data}

## Resumo Executivo
- {n} perfis analisados, {n} vídeos transcritos
- Top padrões identificados: {lista}
- Recomendações principais: {lista}

## Top 10 Perfis Analisados
{tabela com dados}

## Padrões de Alta Performance

### Hooks que Viralizam
{análise detalhada}

### Estruturas Vencedoras
{análise detalhada}

### CTAs que Convertem
{análise detalhada}

### Tom e Linguagem
{análise detalhada}

## Recomendações para Produção
1. {recomendação acionável}
2. {recomendação acionável}
...

## Próximos Passos
- [ ] Criar roteiro baseado nos padrões → `*roteiro {tema}`
- [ ] Gerar prompts de imagem/animação → `*prompt-pack {roteiro}`
- [ ] Produzir vídeo piloto para validar
```

## Post-Conditions

```yaml
post-conditions:
  - [ ] Relatório de benchmark salvo em docs/video-production/benchmarks/
    tipo: output-validation
    validação: "Arquivo existe e contém dados estruturados"
  - [ ] Transcrições salvas separadamente
    tipo: output-validation
    validação: "Arquivo de transcrições existe"
  - [ ] Padrões extraídos em JSON
    tipo: output-validation
    validação: "JSON válido com padrões estruturados"
  - [ ] Recomendações acionáveis geradas
    tipo: quality-check
    validação: "Pelo menos 5 recomendações concretas"
```

---
*AIOS Task - video-benchmark.md — Created 2026-03-17*
