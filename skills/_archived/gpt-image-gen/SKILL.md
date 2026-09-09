---
name: gpt-image-gen
description: "Gera imagens premium via gpt-image-2 (OpenAI, através do fal.ai) — text-to-image e image-to-image com preservação de identidade/rosto. Use quando o briefing pedir 'qualidade ChatGPT', preservar rosto do mentor/aluno, hero de LP cinematográfico, produto Eduzz/Hotmart 1:1 ou 16:9, 8 painéis consistentes com a mesma persona, ou texto em inglês pixel-perfect na imagem. NOT for: volume alto (50+ imagens) ou selfie realista de celebridade (isso é /banana-image-gen, mais barato e permissivo)."
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

⚠️ PIPELINE QUEBRADO — diretório segunda-feira-jarvis não existe mais (auditoria 2026-07-07)

# gpt-image-gen — Skill de Geração com gpt-image-2 (fal.ai)

> Pipeline ponta-a-ponta validado em 26-Abr-2026. Módulo Python local + endpoints fal queue + upload de referência via fal storage. Pertence ao **@creative-director** como ferramenta primária pra criativos premium.

---

## Quando usar (decision matrix)

Escolhe esta skill quando o briefing tiver QUALQUER dos sinais abaixo:

| Sinal | Por quê gpt-image-2 ganha |
|-------|--------------------------|
| Cliente quer "qualidade ChatGPT" | É literalmente o modelo que o ChatGPT usa por baixo desde 22-Abr-2026 |
| Preservar rosto/identidade de pessoa real (${CEO_NAME}, mentor, aluno) | Endpoint `/edit` aceita até 16 refs, mantém ~85-90% de fidelidade facial |
| Hero de LP que precisa "primeiro bloco impressionante" | Composição cinematográfica + smoke + lighting saem de primeira |
| Produto Eduzz/Hotmart que precisa imagem 1:1 ou 16:9 polida | Aspecto + qualidade fotográfica em 1 só geração |
| Briefing menciona "8 paineis consistentes" / "mesma persona em múltiplas cenas" | Feature exclusiva v2 — `num_images=4` mantém personagem |
| Texto em INGLÊS na imagem | Text rendering pixel-perfect (feature de destaque v2) |

### Quando NÃO usar (escolher outra skill)

| Caso | Skill recomendada | Razão |
|------|-------------------|-------|
| Volume alto (50+ imagens em lote) | banana-image-gen ou Flux | gpt-image-2 é ~$0.20/img, banana ~$0.15, Flux ~$0.04 |
| Selfie realista de famoso/celebridade | banana-image-gen | Nano Banana é mais permissivo |
| Texto em PORTUGUÊS na imagem | Imagem SEM texto + Pillow/Canva pra adicionar texto | gpt-image-2 erra diacríticos (~30% das vezes "INVISÍVEL" sai "INVISIVEL") |
| Variações rápidas de cor/fonte de um mesmo design | Editor (Canva/Figma) | Custo de regerar é maior que ajustar |
| Animação/vídeo | cinema-video skill ou Kling | Skill é só imagem estática |

---

## Pré-requisitos

| Recurso | Como verificar |
|---------|----------------|
| `FAL_KEY` no `.env` | `grep FAL_KEY ~/Desktop/segunda-feira-jarvis/.env` |
| Saldo no fal.ai | `https://fal.ai/dashboard/billing` — fal NÃO dá crédito grátis no signup |
| Módulo Python instalado | `~/Desktop/segunda-feira-jarvis/.venv/bin/python3 -c "import image_gen"` |
| Slash command `/img` registrado | `ls ~/.claude/commands/img.md` |

Se faltar `FAL_KEY`, oriente o usuário a pegar em `https://fal.ai/dashboard/keys` e colar no `.env` do projeto segunda-feira.

---

## Como invocar (3 caminhos)

### A) Como agente — chamar via Python module (preferível dentro do @creative-director)

```python
from image_gen import generate_image, edit_image

# Text-to-image
generate_image("hero da LP", size="landscape_16_9", quality="high", open_after=True)

# Image-to-image com referência (preserva rosto)
edit_image(
    "homem de terno preto, smoke vermelho atrás",
    refs=["$HOME/Downloads/foto.png"],
    quality="high",
    open_after=True
)
```

### B) Como humano — slash command no Claude Code

```
/img orbe holográfico azul flutuando
```

### C) Como humano — CLI direto no terminal

```bash
cd ~/Desktop/segunda-feira-jarvis
.venv/bin/python3 image_gen.py "prompt" --quality high --open
.venv/bin/python3 image_gen.py "prompt" --ref /path/foto.png --quality high --open
.venv/bin/python3 image_gen.py "prompt" -n 4 --size landscape_16_9 --open
```

---

## Sizes válidas

| Size | Pixels | Quando usar |
|------|--------|-------------|
| `square_hd` | 1024x1024 | Produto Eduzz/Hotmart, post Instagram, padrão default |
| `landscape_16_9` | 1344x768 | Hero de LP desktop, banner web, thumbnail YouTube |
| `landscape_4_3` | 1024x768 | Slide/apresentação, capa de e-book |
| `portrait_4_3` | 768x1024 | Capa de carrossel Instagram |
| `portrait_16_9` | 768x1344 | Reels/Stories estático, mobile-first hero |
| `auto` | infere do input | **Apenas no edit** — preserva proporção da referência |

---

## Quality (impacto direto em custo + tempo + fidelidade)

| Quality | Tempo médio | Custo aprox | Quando usar |
|---------|-------------|-------------|-------------|
| `low` | 30-60s | ~$0.04 | Rascunho, brainstorm visual rápido |
| `medium` | 60-120s | ~$0.08 | Iteração, validação de conceito |
| `high` | 180-300s | ~$0.20 | **Default** — entrega final, criativo de ad, hero LP |

`POLL_TIMEOUT` no módulo está em 600s — folga suficiente pra qualquer caso.

---

## Padrões de prompt validados

### Hero de LP com rosto preservado (image-to-image)

```
Cinematic professional portrait of the same {pessoa} from the reference image — preserve EXACT facial identity (same beard shape, same eyes, same eyebrows, same nose, same skin tone, same head shape). {Pose desejada}. {Roupa específica em inglês}. {Cenário cinematográfico}. {Lighting}. The {person} is positioned on the {LEFT|RIGHT} THIRD of the frame, leaving the {opposite half} of the image as empty {color} negative space (for text overlay). {Aspect} composition. High detailed natural skin texture with realistic pores, 8k resolution, photorealistic cinematic quality. ABSOLUTELY NO logos, NO brand marks, NO watermarks anywhere.
```

**Variáveis críticas a customizar:**
- Pose — específica e literal ("arms crossed at chest level"), senão modelo escolhe
- Roupa — em INGLÊS e explícita ("black formal long-sleeve dress shirt", não "social wear")
- Negativa — "ABSOLUTELY NO" + lista (logos/brands/watermarks/cartoon/anime)
- Lado da composição — espaço pra texto na LP

### Hero de LP sem foto (text-to-image)

```
{Conceito visual} in {style} aesthetic. {Cores específicas}. {Lighting}. {Composition rule — rule of thirds, central, etc}. Cinematic quality, 8k resolution, photorealistic, no text, no logos.
```

### Carrossel consistente (8 paineis com mesma persona) — feature v2

```
A series of 8 panels showing {persona} in {8 cenários sequenciais}. Same character throughout — same face, same clothing, same color palette. {Estilo geral}. Cinematic continuity.
```

Use `-n 4` (máximo aceito por chamada) duas vezes pra obter 8.

---

## Limitação conhecida: diacríticos em português

**Problema:** o gpt-image-2 escreve "INVISÍVEL" como "INVISIVEL" (sem til) em ~30% das gerações, mesmo com prompt em português. Falha esporádica, não determinística.

**Soluções por ordem de robustez:**

1. **Recomendada:** gerar imagem SEM texto, adicionar texto via Pillow/script (controle 100% tipográfico, custo zero adicional)
2. **Mid:** reforçar no prompt: `"render the EXACT Portuguese text 'MERCADO INVISÍVEL' with acute accent (Í) on the second I"` — taxa de sucesso sobe pra ~70%
3. **Alta tentativa:** gerar `n=4` e escolher a que acertou — caro, mas 1 das 4 quase sempre acerta
4. **Fallback:** texto inteiro em INGLÊS (sem diacríticos) — modelo é pixel-perfect

**Para produto Eduzz/Hotmart com texto em PT-BR:** sempre opção 1.

---

## Output e organização

- Pasta: `~/Pictures/segunda-feira/`
- Naming: `YYYY-MM-DD_HHMMSS_<slug-do-prompt>.png`
- Open: usar flag `--open` (CLI) ou `open_after=True` (Python) abre no Preview macOS

Pra fluxo de criativo de ad/LP, SEMPRE:
1. Salvar a imagem no diretório do criativo do projeto (não em `~/Pictures` solto)
2. Logar metadata (prompt, ref usada, tamanho, custo) num `.md` ao lado da imagem
3. Subir cópia no CLIENTE_EXEMPLO se for pra calendário de conteúdo

---

## Workflow recomendado (creative-director invocando)

```
1. RECEBER briefing → identificar se gpt-image-gen é a skill certa (decision matrix)
2. CONSULTAR feedback loop (~/feedback-loop/results.json) — ângulo já validou?
3. CONSULTAR patterns (~/patterns/formats.md, angles.md) — direção visual?
4. ESCREVER prompt seguindo padrões validados (preservação de rosto, negativas, composição)
5. ESCOLHER quality:
   - Rascunho/iteração → low
   - Final → high
6. INVOCAR via image_gen.py (CLI ou import Python)
7. AVALIAR resultado contra checklist de revisão (ver creative-director.md)
8. SE diacrítico errou → re-gerar SEM texto + adicionar com Pillow
9. SE rosto fugiu da referência → adicionar mais refs (-ref) ou descrever rosto literalmente
10. ENTREGAR + REGISTRAR episódio no Consciousness Engine
```

---

## Custos e benchmarks (Abril 2026)

| Operação | Custo aprox |
|----------|-------------|
| 1 imagem text-to-image, low | ~$0.04 |
| 1 imagem text-to-image, medium | ~$0.08 |
| 1 imagem text-to-image, high | ~$0.20 |
| 1 imagem edit (com 1 ref), high | ~$0.25 |
| 4 imagens edit, high | ~$1.00 |
| Upload de ref ao fal storage | gratuito |

Saldo é gerenciado em `https://fal.ai/dashboard/billing` — fal devolve `403 "User is locked. Reason: Exhausted balance"` quando zera. Avisar usuário pra fazer top-up.

---

## Anti-Patterns (não fazer)

| Evitar | Por quê |
|--------|---------|
| Usar `quality=high` em rascunho | Custo 5x maior do que `low`, sem ganho na fase de exploração |
| Gerar texto em PT-BR direto na imagem (caso de produto) | Diacríticos falham em 30% — não passa no QA |
| Esquecer de subir ref ao fal storage (usar data URI) | Servidor descarta silenciosamente, pseudo-funciona com erro 500 no final |
| Prompt em português sem traduzir | Modelo entende, mas qualidade cai. Inglês > português pra prompt |
| Briefing genérico ("homem moderno") | Faltou pose, roupa, lighting, composição — modelo improvisa e diverge |
| Não passar `--ref` quando precisa de identidade preservada | Text-to-image NÃO sabe quem é ${CEO_NAME}, vai inventar um homem qualquer |

---

## Memória relacionada

- Pipeline implementado em: `~/Desktop/segunda-feira-jarvis/image_gen.py`
- Slash command: `~/.claude/commands/img.md`
- Action voz no SEGUNDA-FEIRA: `actions.py` → tag `IMAGE`
- Memory persistida: `project_image_gen_pipeline.md`
- Episódio registrado em: `~/consciousness/memory/episodic/dev.jsonl`

---

## Integração com outras skills/agentes

| Trigger no briefing | Skill secundária |
|---------------------|------------------|
| Pediu post Instagram | content.md → escolhe formato → invoca esta skill |
| Pediu ad criativo | ad-creative.md → define ângulo → invoca esta skill |
| Pediu identidade de marca | brand-identity.md → define paleta → invoca esta skill |
| Texto em PT-BR na imagem | esta skill (sem texto) + Pillow/script externo |
| Vídeo a partir da imagem | esta skill (gerar still) → cinema-video.md (animar via Kling) |
