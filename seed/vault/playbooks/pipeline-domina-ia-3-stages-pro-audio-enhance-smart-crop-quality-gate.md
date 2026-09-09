---
id: pipeline-domina-ia-3-stages-pro-audio-enhance-smart-crop-quality-gate
title: Pipeline DOMINA.IA — 3 Stages PRO (audio_enhance + smart_crop + quality_gate)
type: playbook
status: active
created: '2026-05-05'
last_verified: '2026-05-05'
domain:
- content
agents:
- video-producer
- content
- sf-master
tags:
- vídeo
- pipeline
- ffmpeg
- loudnorm
- face-detection
- quality-gate
decay_rate: 0.02
links:
- target: issue-personalizacao-nome-dm-CLIENTE_EXEMPLO
  type: auto-linked
- target: pipeline-v-deo-ia-stack-validada-heygen-video-avatar-elevenlabs
  type: auto-linked
- target: diffusers-mps-no-m1-8gb-invi-vel-por-swap-medi-o-emp-rica
  type: auto-linked
- target: content-studio
  type: auto-linked
- target: open-genai-anil-matcha-auditoria-cr-tica-loader-yaml-local-derivado
  type: auto-linked
- target: feedback-sessao-05abr
  type: auto-linked
- target: pipeline-v-deo-ia-stack-validada-heygen-video-avatar-elevenlabs
  type: related
- target: diffusers-mps-no-m1-8gb-invi-vel-por-swap-medi-o-emp-rica
  type: related
- target: open-genai-anil-matcha-auditoria-cr-tica-loader-yaml-local-derivado
  type: related
- target: video-editing
  type: related
- target: skills-apresentacao
  type: related
- target: video-pipeline-referencia
  type: related
axis: ops
---

# Pipeline DOMINA.IA — 3 Stages PRO (audio_enhance + smart_crop + quality_gate)

# Pipeline DOMINA.IA — 3 Stages PRO Validados (05-Mai-2026)

## Contexto

Após confirmar que diffusers/sd-turbo é inviável no M1 8GB (swap intenso, ~14min/img),
pivotamos para ferramentas LEVES que melhoram a qualidade percebida do output sem
depender de modelos diffusion. Resultado: 3 stages novos, todos rodando em
tempo real no hardware atual.

## Stages criados e validados

### 1. `audio_enhance` (2.44s para 10s de áudio)

ffmpeg puro (zero deps Python adicionais):
- highpass 80Hz + lowpass 14kHz (limpeza de bandas)
- afftdn (FFT denoise — remove ruído de fundo)
- dynaudnorm (compressão dinâmica)
- loudnorm 2-pass → -14 LUFS (padrão Instagram/Reels)

Resultado medido: -28.84 LUFS → -14.0 LUFS no smoke test.

### 2. `smart_crop_9_16` (12.10s para 10s de vídeo)

OpenCV Haar Cascade (incluído em opencv-python, zero downloads de modelo):
- detecta rosto em 5s iniciais do vídeo
- pega o maior bounding box (mais próximo da câmera)
- centra crop 9:16 no rosto detectado
- fallback para crop central se não detecta

Resultado medido: rosto detectado em x=268, crop 1080x1920 centrado corretamente.

NOTA: mediapipe 0.10.35 removeu API antiga (`mp.solutions`); migrar para
nova API (`mp.tasks`) exige download de modelo .tflite. OpenCV Haar é
suficiente para o caso de uso e zero overhead.

### 3. `quality_gate` (2.01s)

Validações pré-publicação:
- Aspect 9:16 (1080x1920 exato)
- Duração ≤ 90s (Reel limit)
- Tamanho ≤ 100MB
- Codecs h264/aac (Instagram Graph API)
- LUFS entre -16 e -12 (faixa Instagram)

Bloqueia publicação se qualquer fail. No teste, bloqueou corretamente um vídeo
com áudio fora de range.

## Pipeline integrado: reels-pro.yaml

```
extract_audio → enhance_audio → transcribe → jump_cuts →
captions → overlays → smart_crop → gate → final_video
```

8 nodes em ordem topológica, tudo rodando em segundos no M1 8GB.

## Impacto esperado em produção

| Antes | Depois |
|---|---|
| Áudio com volume inconsistente | Sempre -14 LUFS (Instagram standard) |
| Crop centralizado cego (cabeça cortada possível) | Sempre centrado no rosto |
| Posts publicados com erros (aspect/duração/LUFS) | Bloqueados antes da publicação |
| Pipeline binário (passa ou falha sem detalhe) | Checks granulares com diagnóstico |

## Como portar pro VPS

Copiar `~/video-pipeline-local/stages/{audio_enhance,smart_crop_face,quality_gate}.py`
para `/opt/video-pipeline/stages/` no VPS, ajustar paths de FFMPEG (deve ser
`/usr/bin/ffmpeg` no Ubuntu), e adicionar ao registry. mediapipe não é necessário
(usamos opencv).

## Heurística

Quando hardware limita modelos diffusion, focar em ferramentas leves de
**pós-produção** (ffmpeg loudnorm, opencv face detect, validação de specs)
entrega ganho de qualidade percebida REAL com custo computacional zero.
"Mais inteligência no pipeline existente" > "modelo maior".