---
name: video-avatar
description: "Pipeline de criação de influencer virtual de IA do zero — gera personagem original (GROK/Whisk/Nano Banana), produz vídeos (Veo 3.1/KLING/Pimeca), aplica motion transfer de trends e cobre monetização via Telegram. Use quando pedirem 'criar influencer virtual', 'personagem de IA do zero', 'avatar sem gravar'. NOT for: clone de vídeo com avatar e voz reais do ${CEO_NAME} — isso é /criar-video-avatar."
version: 2.0.0
author: Segunda-feira
tags: [video, avatar, clone, heygen, elevenlabs, content, influencer-virtual, grok, kling, comfyui, veo]
---

# /video-avatar — Pipeline de Vídeos com Avatar IA

## Descrição
Gera vídeos completos de influencer virtual de IA do zero, ponta a ponta — cria personagem original com GROK/Whisk/Nano Banana, gera vídeos com Veo 3.1/KLING/Pimeca, motion transfer de trends, monetização via Telegram.

> Clone de você (avatar + voz reais do ${CEO_NAME}) não é mais coberto aqui — use `/criar-video-avatar`.

## Uso
```
/video-avatar [tema] --format=[talking-head|react|podcast|palestra|montagem] --duration=[30s|60s|90s] --look=[id]
/video-avatar --mode=influencer --name="Luna" --style="morena, 25 anos, fitness"
/video-avatar --mode=influencer --trend=[url-video-referencia]
```

## Exemplos
```
/video-avatar "5 ferramentas de IA que vão substituir agências" --format=talking-head --duration=60s
/video-avatar "react ao novo modelo GPT-5" --format=react --duration=90s
/video-avatar batch --count=5 --topic="IA para negócios"
/video-avatar --mode=influencer --name="Sofia" --style="loira, olhos azuis, 23 anos" --niche="fitness"
/video-avatar --mode=influencer --trend="https://tiktok.com/..." --motion-transfer
```

## Modo 1: Clone do ${CEO_NAME}
→ usar `/criar-video-avatar` (versão validada em produção, com IDs reais e custo medido de R$3/Reel)

## Modo 2: Influencer Virtual do Zero

### 1. Criação do Personagem
- **GROK (xAI):** Geração de imagens hiper-realistas, modo Especialista, 9:16
- **Google Whisk:** Consistência facial via foto de referência + prompt
- **Nano Banana Pro (FreePik):** Imagens até 4K, texto embutido
- **Seedream 4/5:** Fallback quando Nano Banana recusa conteúdo
- **ComfyUI:** Batch processing via workflows visuais com nodes

### 2. Banco de Assets
- Gerar 20-30 fotos (poses, roupas, ambientes variados)
- Troca de roupa: Pinterest (referência) > ChatGPT (descreve) > aplicar
- Troca de cenário: foto real Pinterest > ChatGPT descreve > aplicar
- Body Swap: Gemini 3 Pro como intermediário
- Upscale obrigatório para imagens gratuitas
- FreePik Spaces node "Variations": 9+ variações automáticas com 1 clique

### 3. Produção de Vídeo
- **Veo 3.1 (Flow):** 8s com fala sincronizada, câmera fixa, aceita PT-BR
- **KLING AI Motion Control:** Melhor transferência de movimento, 3-30s
- **Pimeca (Minimax):** Animação premium $6/mês, constância do personagem
- **Viggle/Furo:** Animação gratuita rápida, créditos diários
- **1.video (Wan 2.2):** Character Swap gratuito
- **Sora 2:** Cenas cinematográficas, função Cameo (requer VPN)

### 4. Motion Transfer (Trends/Danças)
- Encontrar vídeo de referência (Pinterest, TikTok, Instagram)
- KLING AI: gerar imagem no MESMO AMBIENTE do vídeo de referência antes de aplicar
- Regra: foto deve cobrir cabeça até joelhos, mesmo ângulo do vídeo
- Evitar "dança girando" — usar "dança normal, sem virar"

### 5. Voz Consistente
- Gerar vídeo com voz padrão (Veo 3.1)
- Trocar voz no ElevenLabs (exportar MP3 > trocar > substituir = sincronização perfeita)

### 6. GRWM (Get Ready With Me)
- Buscar vídeo GRWM real (câmera fixa, boa iluminação)
- Gemini 3 Pro extrai prompts de movimento
- Substituir pessoa frame a frame mantendo ambiente
- Gerar vídeos de cada frame > editar no CapCut

## Pipeline de Monetização

```
Instagram/TikTok (orgânico + pago)
    |
    +-- Privacy (assinatura — público que conhece a plataforma)
    |
    +-- Telegram Free (prévias para atrair)
            |
            +-- Bot VIP (Medibot/VIPGRAM — checkout PIX automático)
                    |
                    +-- Grupo VIP (conteúdo exclusivo)
                            |
                            +-- Planos: 7d (R$29,90) / 30d (R$49,90) / 1 ano (R$299,90)
```

**Automação de vendas:**
- MedBoot/Medibot: pagamento PIX > link automático > acesso ao VIP
- Remarketing automático: leads que geraram PIX mas não pagaram
- Renovação automática: mensagem 1 dia antes do vencimento
- Múltiplos modelos/perfis = multiplicador de receita

## Ferramentas — Stack Completo

### Geração de Imagens
| Ferramenta | Função | Custo |
|-----------|--------|-------|
| GROK (xAI) | Imagens hiper-realistas, modo Especialista | Grátis |
| Google Whisk | Consistência facial | Grátis |
| Nano Banana Pro | Imagens 4K, texto embutido | Incluso FreePik |
| Seedream 4/5 | Fallback para conteúdo liberal | Incluso FreePik |
| FLUX Image Turbo | Volume rápido (open-source) | ~1 crédito/img |
| Gemini | Geração gratuita limitada | Grátis |

### Geração de Vídeos
| Ferramenta | Função | Custo |
|-----------|--------|-------|
| HeyGen | Avatar/clone, talking-head | $29/mês |
| Veo 3.1 (Flow) | Vídeos com fala sincronizada | US$24.99/mês |
| KLING AI | Motion Control superior | US$8.80+/mês |
| Sora 2 | Cenas cinematográficas, Cameo | VPN + ChatGPT |
| Pimeca | Animação premium | ~$6/mês |
| Viggle/Furo | Animação gratuita | Grátis |
| 1.video (Wan 2.2) | Character Swap | Grátis |

### Áudio e Edição
| Ferramenta | Função | Custo |
|-----------|--------|-------|
| ElevenLabs | Clonagem de voz profissional | $22-99/mês |
| Claude API | Roteiros, prompts | ~R$50/mês |
| Whisper | Transcrição e legendas | ~R$10/mês |
| FFmpeg | Edição automática | Grátis |
| CapCut | Edição manual | Free/Pago |

### Plataformas de Workflow
| Ferramenta | Função | Custo |
|-----------|--------|-------|
| ComfyUI Cloud | Workflows visuais, GPU RTX 6000 Pro 96GB | Grátis (400 créditos) |
| FreePik Spaces | Nodes visuais interligáveis | R$34-180/mês |
| Civit.ai | Biblioteca de LoRAs/modelos | Grátis |

### Design Estático
| Ferramenta | Função | Custo |
|-----------|--------|-------|
| FreePik + Nano Banana | Imagens com texto embutido | ~$10/mês |
| NotebookLM | Infográficos, mapas mentais | Grátis |
| Canva AI | Refinamento, captura de texto | Pago |

## Projeto
Código fonte em: `~/video-agent/`

## Base de Conhecimento
- Knowledge base completa: `~/fabrica-conteudo-invisivel/KNOWLEDGE-BASE-COMPLETA.md`
- Cursos consolidados:
  - Fábrica de Conteúdo Invisível (Lucas Arrial, Hotmart) — 17 aulas
  - Método Job Com IA + Modelo Influencer (Cakto) — 14 aulas
  - Influencer Academy (Cakto) — 36 aulas
  - Influencer Sem Censura (Cakto) — 14 aulas
- Transcrições completas em `~/fabrica-conteudo-invisivel/transcricoes/` e `~/fabrica-conteudo-invisivel/transcricoes-cakto/`
- Resumos executivos em `~/fabrica-conteudo-invisivel/resumos/`
