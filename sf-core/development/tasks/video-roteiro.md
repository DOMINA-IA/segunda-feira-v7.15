# Video Roteiro — Criação de Roteiro Baseado em Benchmark

## Purpose

Criar roteiro completo de vídeo para IA, baseado em dados reais de benchmark: hooks validados, estruturas que performam, CTAs efetivos. O roteiro inclui cues visuais, emoções, gestos e indicações de câmera para facilitar a geração de prompts na fase seguinte.

## Task Definition (AIOS Task Format V1.0)

```yaml
task: videoRoteiro()
agent: "@video-producer"
responsável: Dash
atomic_layer: Creative

elicit: true

inputs:
  - name: tema
    type: string
    required: true
    validation: "Tema/ideia do vídeo"
  - name: formato
    type: enum
    required: false
    default: reels
    options: [reels, youtube-shorts, youtube-long, ad-meta, ad-youtube]
    validation: "Formato do vídeo alvo"
  - name: duracao
    type: string
    required: false
    default: "30-60s"
    validation: "Duração alvo do vídeo"
  - name: tom
    type: enum
    required: false
    default: provocativo
    options: [provocativo, educativo, inspiracional, storytelling, desafio, tutorial, humor]
    validation: "Tom principal do vídeo"
  - name: perfil_clone
    type: string
    required: false
    validation: "@username para clonar estilo (opcional)"
  - name: benchmark_data
    type: file
    required: false
    validation: "Arquivo de benchmark prévio (padrões extraídos)"
  - name: persona_alvo
    type: string
    required: false
    validation: "Quem vai 'aparecer' no vídeo (você, cliente, personagem IA)"

outputs:
  - name: roteiro
    type: file
    location: "docs/video-production/roteiros/{tema-slug}-roteiro.md"
    persistido: true
  - name: roteiro_json
    type: file
    location: "docs/video-production/roteiros/{tema-slug}-roteiro.json"
    persistido: true
```

## Pre-Conditions

```yaml
pre-conditions:
  - [ ] Tema definido
    tipo: pre-condition
    blocker: true
    validação: "Tema específico e claro"
  - [ ] Benchmark disponível (ideal) ou contexto suficiente
    tipo: pre-condition
    blocker: false
    validação: "Se não tiver benchmark, usar conhecimento do nicho como base"
```

## Interactive Elicitation Process

### Step 1: Tema e Objetivo

```
ELICIT: Tema e Objetivo do Vídeo

Qual o tema do vídeo e o objetivo principal?

Exemplos:
- "Substituindo conteúdo de big players por IA" → objetivo: viralizar + captar leads
- "Como usar ChatGPT para vender mais" → objetivo: educar + autoridade
- "Antes e depois: negócio sem IA vs com IA" → objetivo: provocar + vender

→ Validation: Tema específico, não genérico
→ Default: Baseado no nicho do usuário
```

### Step 2: Formato e Duração

```
ELICIT: Formato e Duração

Qual formato e duração?

1. Reels/TikTok (15-60s) — padrão
2. YouTube Shorts (até 60s)
3. YouTube Long-form (3-15min)
4. Ad Meta (15-30s)
5. Ad YouTube (15-30s)

→ Validation: Opção válida
→ Default: Reels 30-60s
```

### Step 3: Tom e Estilo

```
ELICIT: Tom e Estilo

Qual tom principal?

1. Provocativo — desafia crenças, confronta
2. Educativo — ensina com valor
3. Inspiracional — motiva, eleva
4. Storytelling — conta história
5. Desafio — formato "eu fiz X com Y"
6. Tutorial — passo a passo
7. Humor — entretenimento

Quer clonar o estilo de algum criador? Se sim, qual @username?

→ Validation: Tom definido
→ Default: Provocativo (melhor performance no nicho IA)
```

### Step 4: Persona do Vídeo

```
ELICIT: Quem Aparece no Vídeo

Quem vai "protagonizar" o vídeo?

1. Você mesmo (com sua face/voz)
2. Clone de um criador (face swap)
3. Personagem IA original (criado do zero)
4. Sem pessoa — apenas visual + narração

→ Validation: Opção definida
→ Default: Depende do contexto
```

## Implementation Steps

### Step 1: Contexto e Base de Dados

**Se benchmark disponível:**
- Carregar padrões extraídos (`*-padroes.json`)
- Identificar top hooks, estruturas e CTAs do nicho
- Usar vocabulário e tom validados por dados

**Se sem benchmark:**
- Usar conhecimento geral do nicho
- Aplicar frameworks universais de hook
- AVISAR: "Roteiro sem benchmark → performance pode ser menor. Recomendo `*benchmark` primeiro."

### Step 2: Geração de Hooks (5+ opções)

**Gerar pelo menos 5 opções de hook baseados em dados:**

```markdown
## Opções de Hook (primeiros 3 segundos)

| # | Hook | Tipo | Base |
|---|------|------|------|
| 1 | "Enquanto você pensa na festa do fim de semana, um jovem de 21 anos tá fazendo seu primeiro milhão" | Contraste | Top performer no benchmark |
| 2 | "Eu substituí o conteúdo de um influenciador de 2M de seguidores por IA em 3 minutos" | Prova/Desafio | Formato validado |
| 3 | "R$ X.XXX virou R$ X.XXX em 30 dias. E eu nem toquei num computador" | Resultado | Ângulo campeão |
| 4 | "Pare de criar conteúdo. Sério. Pare agora." | Provocação | Alto engajamento no nicho |
| 5 | "Ninguém tá falando isso sobre IA. E deveria." | Curiosidade | Pattern de viral |

**Recomendação:** Hook #{n} — {razão baseada em dados}
```

### Step 3: Estrutura do Roteiro

**Formato do roteiro completo:**

```markdown
## Roteiro: {título}

**Formato:** {reels|youtube|ad}
**Duração alvo:** {duração}
**Tom:** {tom}
**Persona:** {quem aparece}
**Hook escolhido:** #{n}

---

### CENA 1: HOOK (0:00 - 0:03)
**Texto falado:** "{hook}"
**Visual:** {descrição da cena — o que aparece na tela}
**Emoção:** {confiante|urgente|provocativo|calmo}
**Gesto:** {apontar para câmera|cruzar braços|levantar mão}
**Câmera:** {close-up face|medium shot|zoom in}
**Música/SFX:** {bass drop|tension build|silence}

---

### CENA 2: PROBLEMA/CONTEXTO (0:03 - 0:10)
**Texto falado:** "{desenvolvimento do problema}"
**Visual:** {descrição visual — B-roll, screencast, imagem IA}
**Emoção:** {preocupação|curiosidade|empatia}
**Gesto:** {balançar cabeça|mostrar tela|expressão séria}
**Câmera:** {pan para tela|cut para B-roll|medium shot}
**Transição:** {corte seco|fade|zoom}
**Música/SFX:** {tension loop|subtle beat}

---

### CENA 3: VIRADA/SOLUÇÃO (0:10 - 0:25)
**Texto falado:** "{solução, revelação, tutorial}"
**Visual:** {demonstração, screencast, resultado}
**Emoção:** {entusiasmo|confiança|surpresa}
**Gesto:** {mostrar resultado|apontar|sorriso}
**Câmera:** {screencast|medium shot|cut entre cenas}
**Música/SFX:** {beat drop|energy build}

---

### CENA 4: PROVA/RESULTADO (0:25 - 0:40)
**Texto falado:** "{resultado, prova social, antes/depois}"
**Visual:** {resultado na tela, números, before/after}
**Emoção:** {orgulho|surpresa|satisfação}
**Gesto:** {mostrar tela|expressão de wow|aplaudir}
**Câmera:** {close-up resultado|cut para face|zoom out}
**Música/SFX:** {triumphant|celebration}

---

### CENA 5: CTA (0:40 - 0:50)
**Texto falado:** "{CTA direto e claro}"
**Visual:** {face camera|texto overlay|seta para ação}
**Emoção:** {urgente|amigável|direto}
**Gesto:** {apontar para baixo|pedir para comentar}
**Câmera:** {close-up face|medium shot}
**Música/SFX:** {fade out|stinger}

---

### TEXTO COMPLETO (para voice clone)
"{roteiro inteiro corrido, sem indicações de cena}"
```

### Step 4: Exportar em JSON

**Formato JSON para automação:**

```json
{
  "titulo": "string",
  "formato": "reels|youtube|ad",
  "duracao_alvo": "30-60s",
  "tom": "provocativo",
  "persona": "string",
  "hook_escolhido": 1,
  "hooks_alternativos": ["hook2", "hook3"],
  "cenas": [
    {
      "numero": 1,
      "nome": "HOOK",
      "timestamp": "0:00 - 0:03",
      "texto_falado": "string",
      "visual": "string",
      "emocao": "string",
      "gesto": "string",
      "camera": "string",
      "musica_sfx": "string",
      "transicao": "string"
    }
  ],
  "texto_completo": "roteiro inteiro corrido",
  "metadata": {
    "baseado_em_benchmark": true,
    "benchmark_file": "path/to/benchmark",
    "data_criacao": "ISO date",
    "agent": "Dash (video-producer)"
  }
}
```

### Step 5: Validação e Próximos Passos

**Checklist de qualidade do roteiro:**
- [ ] Hook é impactante (para o scroll em 3s)
- [ ] Estrutura flui naturalmente (sem saltos)
- [ ] CTA é claro e acionável
- [ ] Emoções e gestos são congruentes com a fala
- [ ] Duração está dentro do alvo
- [ ] Tom é consistente do início ao fim
- [ ] Texto completo está pronto para voice clone
- [ ] Visual descriptions são suficientes para prompt de IA

**Próximos passos:**
```
→ *prompt-pack {roteiro} — Gerar prompts de imagem e animação
→ *voice-plan {roteiro} — Planejar voice clone e lip sync
→ *reference-pack {tema} — Buscar referências visuais
```

## Post-Conditions

```yaml
post-conditions:
  - [ ] Roteiro completo salvo em docs/video-production/roteiros/
    tipo: output-validation
    validação: "Arquivo existe com todas as cenas"
  - [ ] JSON exportado
    tipo: output-validation
    validação: "JSON válido com estrutura completa"
  - [ ] Pelo menos 5 opções de hook geradas
    tipo: quality-check
    validação: "Hooks variados e baseados em dados"
  - [ ] Todas as cenas têm indicações de visual, emoção e gesto
    tipo: quality-check
    validação: "Nenhuma cena sem cues visuais"
  - [ ] Texto completo corrido disponível para voice clone
    tipo: quality-check
    validação: "Texto sem indicações técnicas, pronto para falar"
```

---
*AIOS Task - video-roteiro.md — Created 2026-03-17*
