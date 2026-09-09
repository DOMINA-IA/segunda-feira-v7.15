# Video Prompt Pack — Geração de Prompts de Imagem e Animação

## Purpose

Dado um roteiro completo, gerar o pack de prompts otimizados para cada cena: prompts de imagem (Flux/Nano Banana Pro), prompts de animação (Kling 3.0/VO3), instruções de face swap, referências visuais e configurações de câmera. Output pronto para produção.

## Task Definition (AIOS Task Format V1.0)

```yaml
task: videoPromptPack()
agent: "@video-producer"
responsável: Dash
atomic_layer: Production

elicit: true

inputs:
  - name: roteiro
    type: string
    required: true
    validation: "Roteiro completo (texto ou path para arquivo .md/.json)"
  - name: estilo
    type: enum
    required: false
    default: realista
    options: [realista, cinematic, cartoon, anime, 3d, mixed]
    validation: "Estilo visual do vídeo"
  - name: tool_imagem
    type: enum
    required: false
    default: flux
    options: [flux, midjourney, dalle, hailuofield]
    validation: "Ferramenta principal para geração de imagens"
  - name: tool_animacao
    type: enum
    required: false
    default: kling
    options: [kling, vo3, runway, hailuofield, seedance]
    validation: "Ferramenta principal para animação"
  - name: persona_imagem
    type: file
    required: false
    validation: "Imagem de referência da pessoa que vai aparecer no vídeo"
  - name: aspect_ratio
    type: enum
    required: false
    default: "9:16"
    options: ["9:16", "16:9", "1:1", "4:3"]
    validation: "Proporção do vídeo"

outputs:
  - name: prompt_pack
    type: file
    location: "docs/video-production/prompts/{roteiro-slug}-prompts.md"
    persistido: true
  - name: prompt_pack_json
    type: file
    location: "docs/video-production/prompts/{roteiro-slug}-prompts.json"
    persistido: true
```

## Pre-Conditions

```yaml
pre-conditions:
  - [ ] Roteiro completo disponível (com cenas, visual, emoções, gestos)
    tipo: pre-condition
    blocker: true
    validação: "Roteiro tem pelo menos: texto falado + visual description por cena"
  - [ ] Estilo visual definido
    tipo: pre-condition
    blocker: false
    validação: "Se não definido, usar 'realista' como default"
  - [ ] Imagem de referência da persona (se aplicável)
    tipo: pre-condition
    blocker: false
    validação: "Se vídeo tem persona, ter imagem de referência"
```

## Interactive Elicitation Process

### Step 1: Roteiro

```
ELICIT: Roteiro Base

Cole o roteiro ou indique o arquivo:

Se já usou *roteiro antes, posso usar o último roteiro gerado.

→ Validation: Roteiro com pelo menos 3 cenas
→ Default: Último roteiro gerado na sessão
```

### Step 2: Estilo Visual

```
ELICIT: Estilo Visual

Qual estilo visual do vídeo?

1. Realista — Foto-realista, como pessoa real (padrão)
2. Cinematic — Estilo filme, iluminação dramática
3. Cartoon — Estilo cartoon/ilustração
4. Anime — Estilo anime japonês
5. 3D — Render 3D estilizado
6. Mixed — Mix de estilos por cena

→ Validation: Opção válida
→ Default: Realista
```

### Step 3: Ferramentas

```
ELICIT: Ferramentas de Produção

Quais ferramentas você vai usar?

**Imagens:**
1. Flux / Nano Banana Pro (padrão) — Melhor qualidade, face swap nativo
2. Midjourney — Estética premium
3. DALL-E — Rápido e acessível
4. Hailuofield Soul — Character consistency

**Animação:**
1. Kling 3.0 (padrão) — Bom em animação, não fala PT nativo
2. VO3 — Fala PT, mas restrições de face
3. Runway ML — Versátil
4. Seedance (fal.ai) — Integrado ao CLIENTE_EXEMPLO

→ Default: Flux + Kling 3.0
```

### Step 4: Persona e Face

```
ELICIT: Persona Visual

Quem aparece no vídeo?

1. Eu mesmo — preciso da minha foto de referência
2. Clone de criador — preciso da foto dele + face swap
3. Personagem IA — vou criar um character
4. Sem pessoa — apenas visual/narração

Se opção 1-3: Tem imagem de referência? (cole path ou URL)

→ Validation: Se tem persona, precisa de referência
→ Default: Baseado no roteiro
```

## Implementation Steps

### Step 1: Analisar Roteiro e Extrair Cenas

**Para cada cena do roteiro, extrair:**
- Descrição visual
- Emoção/tom
- Gestos/movimentos
- Câmera/enquadramento
- Duração estimada
- Elementos em cena (objetos, cenário, pessoas)

### Step 2: Gerar Prompts de Imagem (Flux/Nano Banana Pro)

**Para cada cena, gerar prompt de imagem otimizado:**

```markdown
### Cena {n}: {nome}

**Prompt de Imagem (Flux/Nano Banana Pro):**
```
{persona description}, {action/pose}, {emotion/expression},
{clothing/accessories}, {environment/background}, {lighting},
{camera angle}, {style modifiers}, {quality modifiers}

Example: A confident Brazilian man in his 30s, wearing a dark blazer,
pointing at the camera with intensity, modern office background with
screens showing data, dramatic side lighting, medium close-up shot,
photorealistic, 8K resolution, sharp focus, professional photography
```

**Aspect Ratio:** {9:16|16:9|1:1}
**Resolução:** 2K/4K
**Referência visual:** {Pinterest/clip.cafe URL ou descrição}
**Face swap necessário:** {sim|não} — {instruções se sim}
```

**Regras de prompt de imagem:**
1. SEMPRE especificar expressão facial congruente com a emoção da cena
2. SEMPRE incluir lighting description (crítico para qualidade)
3. SEMPRE incluir camera angle/framing
4. Se persona: incluir character description consistente em TODAS as cenas
5. Se face swap: gerar prompt adicional de `trade face a random face`
6. Quality modifiers no final: `8K, photorealistic, sharp focus, professional`

### Step 3: Gerar Prompts de Animação (Kling/VO3)

**Para cada cena, gerar prompt de animação estruturado:**

```markdown
### Cena {n}: Prompt de Animação

**Prompt (Kling 3.0 / VO3):**
```json
{
  "description": "A man speaks confidently to camera about AI replacing traditional content creation. He gestures with his right hand, emphasizing key points. His expression shifts from serious to excited as he reveals the solution.",
  "motion": {
    "type": "talking_head",
    "primary_action": "speaking to camera",
    "gestures": [
      "0:00-0:02: right hand raised, pointing at camera",
      "0:02-0:04: both hands open, explaining",
      "0:04-0:06: touches chin thoughtfully",
      "0:06-0:08: excited expression, hands spread wide"
    ],
    "camera": "static medium close-up, slight zoom in at 0:06"
  },
  "keywords": [
    "8K", "portuguese dialogue", "confident tone",
    "natural gestures", "emotional sync", "professional lighting"
  ],
  "voice": {
    "tone": "confident, direct",
    "language": "pt-BR",
    "emotion_shifts": [
      "0:00-0:04: serious, authoritative",
      "0:04-0:08: excited, revelatory"
    ]
  },
  "quality": "8K resolution, iPhone 15 Pro camera, cinematic lighting, shallow depth of field",
  "duration": "8s"
}
```

**Sync Control:** {imagem|vídeo} — o que predomina na geração
**Motion Control:** {sim|não} — se precisa manter face específica
```

**Regras de prompt de animação:**
1. **CRÍTICO: Sync de gestos com fala** — Cada gesto deve corresponder ao que está sendo dito
2. **CRÍTICO: Emoções congruentes** — Expressão facial deve bater com o tom da fala
3. Incluir `8K` e `camera type` para melhorar qualidade
4. Especificar idioma: `portuguese dialogue` ou `pt-BR`
5. Se usando Kling (não fala PT): foco nos gestos, voz será trocada depois
6. Se usando VO3: incluir texto falado no prompt para lip sync

### Step 4: Gerar Instruções de Face Swap (se necessário)

**Quando VO3 não aprova a face:**

```markdown
### Face Swap Workaround — Cena {n}

**Step 1: Trade Face (Nano Banana Pro)**
```
trade face a random face. Keep the same lighting, position,
clothing and background. Only change the face to a completely
random, generic face.
```
→ Input: imagem original da persona
→ Output: mesma imagem com face genérica

**Step 2: Animar no VO3**
→ Usar a imagem com face genérica
→ VO3 vai aprovar (face não reconhecida)
→ Gerar animação normal

**Step 3: Motion Control (VO3)**
→ Usar a imagem ORIGINAL como referência de motion control
→ Sync Control: IMAGEM (não vídeo)
→ O que predomina: a face real + movimentos do vídeo animado
```

### Step 5: Montar Reference Pack

**Para cada cena, sugerir referências visuais:**

```markdown
### Referências Visuais — Cena {n}

**Pinterest:**
- Buscar: "{termos de busca sugeridos}"
- Tipo: {iluminação|composição|cenário|pose|estilo}

**clip.cafe:**
- Filme sugerido: {nome do filme}
- Cena de referência: {descrição da cena}
- Uso: {iluminação|enquadramento|cenário}

**Instagram (conta spy):**
- Pesquisar: "{termos}"
- Tipo de conteúdo: {talking head|B-roll|screencast}
```

### Step 6: Exportar Pack Completo

**Formato Markdown:**

```markdown
# Prompt Pack: {título do roteiro}

**Data:** {data}
**Roteiro base:** {path}
**Ferramentas:** {imagem} + {animação}
**Persona:** {quem}
**Aspect ratio:** {ratio}
**Total de cenas:** {n}

---

## Cena 1: {nome}
### Imagem
{prompt de imagem}
### Animação
{prompt de animação JSON}
### Face Swap
{instruções se necessário}
### Referências
{links/sugestões}

---

## Cena 2: {nome}
...

---

## Checklist de Produção
- [ ] Gerar todas as imagens
- [ ] Revisar qualidade e consistência de character
- [ ] Animar cada cena
- [ ] Verificar lip sync
- [ ] Aplicar face swap onde necessário
- [ ] Fazer voice clone (ElevenLabs)
- [ ] Aplicar voice changer
- [ ] Entregar para @video-editor (Pixel) para edição final
```

**Formato JSON:**

```json
{
  "titulo": "string",
  "roteiro_base": "path",
  "ferramentas": {
    "imagem": "flux",
    "animacao": "kling"
  },
  "persona": {
    "tipo": "clone|original|sem",
    "referencia": "path/url",
    "face_swap_necessario": false
  },
  "aspect_ratio": "9:16",
  "cenas": [
    {
      "numero": 1,
      "nome": "HOOK",
      "prompt_imagem": "full prompt string",
      "prompt_animacao": {
        "description": "string",
        "motion": {},
        "keywords": [],
        "voice": {},
        "quality": "string",
        "duration": "8s"
      },
      "face_swap": {
        "necessario": false,
        "instrucoes": "string if needed"
      },
      "referencias": {
        "pinterest": ["search terms"],
        "clip_cafe": {"filme": "", "cena": ""},
        "instagram": ["search terms"]
      },
      "sync_control": "imagem",
      "motion_control": false
    }
  ],
  "metadata": {
    "data_criacao": "ISO date",
    "agent": "Dash (video-producer)",
    "total_cenas": 5,
    "estimativa_producao": "2-4 horas"
  }
}
```

## Post-Conditions

```yaml
post-conditions:
  - [ ] Prompt pack completo salvo (MD + JSON)
    tipo: output-validation
    validação: "Ambos os arquivos existem com todas as cenas"
  - [ ] Cada cena tem prompt de imagem E animação
    tipo: quality-check
    validação: "Nenhuma cena sem prompts"
  - [ ] Gestos e emoções sincronizados em todos os prompts de animação
    tipo: quality-check
    validação: "Cada prompt tem gesture sync e emotion sync"
  - [ ] Face swap workaround documentado (se necessário)
    tipo: quality-check
    validação: "Instruções claras para cada cena que precisa"
  - [ ] Referências visuais sugeridas para cada cena
    tipo: quality-check
    validação: "Pelo menos 1 sugestão de referência por cena"
  - [ ] Checklist de produção incluído
    tipo: quality-check
    validação: "Checklist com todas as etapas"
```

---
*AIOS Task - video-prompt-pack.md — Created 2026-03-17*
