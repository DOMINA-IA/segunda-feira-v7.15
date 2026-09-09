---
id: pipeline-v-deo-ia-stack-validada-heygen-video-avatar-elevenlabs
title: Pipeline Vídeo IA — Stack Validada (HeyGen Video Avatar + ElevenLabs)
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
- copywriter
tags:
- vídeo
- pipeline
- heygen
- elevenlabs
- avatar
- voice-clone
- validado
decay_rate: 0.02
links:
- target: video-editing
  type: auto-linked
- target: open-genai-anil-matcha-auditoria-cr-tica-loader-yaml-local-derivado
  type: auto-linked
- target: pipeline-domina-ia-3-stages-pro-audio-enhance-smart-crop-quality-gate
  type: auto-linked
- target: bave-metodologia-klt-know-like-trust-traffic-system
  type: related
- target: klt-curso-modulo-1-aula-2-a-desconstru-o-do-mercado-digital
  type: related
- target: klt-curso-modulo-2-aula-2-a-primeira-impress-o-a-que-fica
  type: related
- target: diffusers-mps-no-m1-8gb-invi-vel-por-swap-medi-o-emp-rica
  type: related
- target: bave-persona-m-nica-martins-mulher-executiva-corporativa
  type: related
- target: open-genai-anil-matcha-auditoria-cr-tica-loader-yaml-local-derivado
  type: related
- target: case-israel-king-domina-mai2026
  type: related
- target: creativity-protocol
  type: related
- target: klt-curso-modulo-5-aula-4-hackeando-conte-do-adamantium
  type: related
- target: bavi-email-marketing-75-abertura-sequ-ncia
  type: related
- target: klt-curso-modulo-1-aula-1-voc-desconhecido
  type: related
- target: klt-curso-modulo-4-aula-6-criar-consci-ncia-da-solu-o-1
  type: related
- target: klt-curso-modulo-3-aula-2-a-ci-ncia-dos-conte-dos-da-fase-l
  type: related
- target: klt-curso-modulo-4-aula-1-a-ci-ncia-da-constru-o-da-confian-a
  type: related
- target: klt-curso-modulo-4-aula-5-criar-consci-ncia-do-problema-1
  type: related
- target: klt-curso-modulo-3-aula-3-como-deixar-seus-seguidores-fascinados-por-voc
  type: related
- target: klt-curso-modulo-4-aula-2-cria-o-de-conte-do-1
  type: related
- target: klt-curso-modulo-4-aula-4-n-o-existe-uma-linearidade-1
  type: related
- target: pipeline-domina-ia-3-stages-pro-audio-enhance-smart-crop-quality-gate
  type: related
- target: klt-curso-modulo-5-aula-3-conte-do-adamantium
  type: related
- target: bave-klt-curso-oficial-estrutura-completa-avengers-academy
  type: related
- target: klt-curso-modulo-5-aula-2-como-eleger-as-melhores-headlines
  type: related
- target: klt-curso-modulo-1-aula-5-a-venda-sem-for-a
  type: related
- target: klt-curso-modulo-5-aula-1-calend-rio-de-produ-o-avengers
  type: related
- target: klt-curso-modulo-2-aula-3-o-segredo-para-atrair-as-pessoas-certas-e-repelir-as-erradas
  type: related
- target: klt-curso-modulo-3-aula-1-encantar-e-fascinar-as-pessoas
  type: related
- target: klt-curso-modulo-1-aula-6-os-3-grandes-mercados
  type: related
- target: klt-curso-modulo-1-aula-4-seu-produto-n-o-vitalicio
  type: related
- target: video-editing
  type: related
- target: calendario-instagram-semana-1-4-mai2026
  type: related
- target: skills-apresentacao
  type: related
- target: video-pipeline-referencia
  type: related
axis: ops
---

# Pipeline Vídeo IA — Stack Validada (HeyGen Video Avatar + ElevenLabs)

# Pipeline Vídeo IA DOMINA.IA — Stack Validada 05-Mai-2026

## TL;DR

Stack vencedora após 4 iterações: **ElevenLabs voice clone + HeyGen Video Avatar lipsync**.
Não usar HeyGen TTS interno (voz robotizada). Custo ~R$5/Reel 60s.

## IDs persistidos

- HeyGen Video Avatar ${CEO_NAME}: `${PLATFORM_ID}`
- HeyGen avatar group: `${REDIGIDO}` (25 looks)
- ElevenLabs voice clone ${CEO_NAME}: `${PLATFORM_ID}`
- Sample original: 90s do IMG_2638 limpo a -18 LUFS

Salvos em `~/video-pipeline-local/.env`.

## Arquitetura validada

```
Texto → ElevenLabs TTS (voz clonada) → MP3
       → litterbox.catbox.moe (URL pública 24h)
       → HeyGen /v2/video/generate {voice.type: audio, audio_url: ...}
       → HeyGen apenas faz LIPSYNC (não TTS)
       → MP4 1080x1920
       → Pipeline DOMINA.IA (legendas word-slam + overlays + quality gate)
       → Reel pronto
```

## Por que essa stack venceu

| Tentativa | Resultado |
|---|---|
| Photo avatar HeyGen + TTS HeyGen | Painha, cabeça mexendo só, voz robotizada |
| Avatar IV HeyGen + TTS HeyGen | Gestos artificiais, voz robotizada |
| Video Avatar HeyGen + TTS HeyGen | Movimento bom, voz robotizada |
| **Video Avatar HeyGen + ElevenLabs voice** | **Aprovado: tudo natural** |

## Settings ElevenLabs validados

```json
{
  "model_id": "eleven_multilingual_v2",
  "voice_settings": {
    "stability": 0.5,
    "similarity_boost": 0.85,
    "style": 0.3,
    "use_speaker_boost": true
  }
}
```

## Custo real por Reel 60s

- ElevenLabs (~600 chars): ~0.5% do plano Creator (131k chars/mês) ≈ grátis
- HeyGen lipsync: ~60 credits ≈ R$5
- Total: ~R$5/Reel

Comparativo: HeyGen TTS interno custa R$15-20/Reel. **Economia de 70%**.

## Heurísticas extraídas

1. **Sempre separar TTS de lipsync.** ElevenLabs faz voz melhor; HeyGen faz lipsync sobre áudio externo. Combinação > integração.
2. **Sample ElevenLabs limite 11MB.** Comprimir pra MP3 mono 22kHz antes de upload.
3. **Plano Creator ElevenLabs ($22/mês) > Starter ($5).** Creator destrava 131k chars/mês + Pro Voice Clone (necessário pra qualidade 95%).
4. **HeyGen API credits são SEPARADOS do plano Creator (200 web credits).** Necessário comprar add-on específico.
5. **Video Avatar HeyGen exige treino com vídeo real.** Photo avatar e Avatar IV ficam artificiais.
6. **Litterbox 24h serve pra teste.** Produção exige bucket S3 fixo.
7. **CEO valoriza autenticidade > custo.** Investir em qualidade da voz é o que faz diferença percebida.

## Limitações atuais (refinar)

1. Voice clone Instant tem ~85% similaridade. Pro Clone (5-10min limpo) sobe pra ~95%.
2. Falta aplicar pipeline DOMINA.IA (legendas word-slam + overlays + quality gate) no output.
3. Sem B-roll automático intercalado.

## TODO próximas iterações

- [ ] Voice Clone Pro ElevenLabs com 5-10min áudio limpo
- [ ] Pipeline DOMINA.IA aplicado pós-HeyGen
- [ ] B-roll automático (Pexels + Whisper tagging)
- [ ] Hospedagem fixa (S3 ao invés de litterbox)
- [ ] Tunar stability/style com A/B test

## Skill criada

`/criar-video-avatar` em `~/.claude/skills/criar-video-avatar.md` — uso em qualquer agente.

## Episódios relacionados

- 2026-05-05: 4 iterações de qualidade (painha → Avatar IV → Video Avatar → ElevenLabs win)
- Heurística salva: "voice clone instant ElevenLabs > HeyGen TTS interno"