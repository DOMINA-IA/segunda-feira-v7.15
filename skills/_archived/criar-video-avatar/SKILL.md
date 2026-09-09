---
name: criar-video-avatar
description: Pipeline validado de vídeo com avatar+voz do ${CEO_NAME} (HeyGen Video Avatar + ElevenLabs voice clone). Use quando pedirem "cria vídeo", "gera reel", "produz vídeo da copy X", "vídeo do ${CEO_NAME} falando".
---

# /criar-video-avatar — Pipeline Vídeo IA DOMINA.IA

> **Status:** Validado em produção 2026-05-05 (Reel Mercado Invisível)
> **Custo médio:** ~R$5/Reel de 60s (4× mais barato que rodar TTS no HeyGen) — valor recalculado a partir da tabela "Custo por Reel (60s)" abaixo (ElevenLabs grátis dentro do plano Creator + ~60 credits HeyGen ≈ R$5)
> **Qualidade:** Aceitável (CEO aprovou, ainda há margem de refinamento)

## Quando usar

- Usuário pede "cria vídeo do ${CEO_NAME} falando sobre X"
- Geração programática de Reels com avatar
- Conteúdo onde ${CEO_NAME} NÃO grava manualmente
- VSL curto, ad de tráfego, aula promocional

## Quando NÃO usar

- Vídeo gravado pelo ${CEO_NAME} pra editar (use pipeline `/opt/video-pipeline/` no VPS)
- Conteúdo que exige pessoa REAL falando ao vivo
- Lives, reações, depoimentos espontâneos

## Stack vencedora (validada 05-Mai-2026)

| Componente | Provider | Por quê escolhido |
|---|---|---|
| **Voz** | ElevenLabs clone (`${PLATFORM_ID}`) | Soa natural; HeyGen TTS interno é robotizado |
| **Avatar** | HeyGen Video Avatar (`${PLATFORM_ID}`) | Movimento corporal REAL (vídeo treinado), não simulado |
| **Hosting áudio** | litterbox.catbox.moe (24h) | Grátis, suficiente pra HeyGen baixar |
| **Pipeline final** | `~/projetos/dominaia/video-pipeline-local/` (legendas + overlays + quality gate) | Aplicar ANTES de publicar |

## Arquitetura: ElevenLabs gera áudio → HeyGen só faz lipsync

**NÃO usar HeyGen TTS interno** (`voice.type: text`). Sempre `type: audio` com URL da ElevenLabs:

1. ElevenLabs gera áudio com voz clonada do ${CEO_NAME} → MP3
2. Upload do MP3 pra litterbox.catbox.moe → URL pública 24h
3. HeyGen `POST /v2/video/generate` com `voice.type: audio` + `audio_url`
4. HeyGen apenas sincroniza boca com áudio (custo 4× menor)
5. Pipeline DOMINA.IA aplica legendas word-slam + overlays + quality gate

## IDs persistidos em `~/projetos/dominaia/video-pipeline-local/.env`

```bash
${REDIGIDO}=${PLATFORM_ID}
${REDIGIDO}=${PLATFORM_ID}
ELEVEN_STABILITY=0.5
ELEVEN_SIMILARITY_BOOST=0.85
ELEVEN_STYLE=0.3
ELEVEN_MODEL=eleven_multilingual_v2
```

## Fluxo executável (template Python)

```python
import os, json, time, subprocess, requests
from pathlib import Path

# Carrega .env
env = {l.split("=", 1)[0]: l.split("=", 1)[1].strip()
       for l in Path("~/projetos/dominaia/video-pipeline-local/.env").expanduser().read_text().splitlines()
       if "=" in l and not l.startswith("#")}

ELEVEN = env["ELEVENLABS_API_KEY"]
HEYGEN = env["HEYGEN_DEVELOP_KEY"]
AVATAR = env["${REDIGIDO}"]
VOICE = env["${REDIGIDO}"]

SCRIPT = "..."  # texto a falar (≤500 chars pra Reel ≤60s)

# 1) ElevenLabs gera áudio
r = requests.post(
    f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}",
    headers={"xi-api-key": ELEVEN, "Accept": "audio/mpeg"},
    json={
        "text": SCRIPT,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.85,
                           "style": 0.3, "use_speaker_boost": True},
    }, timeout=180,
)
audio_path = "/tmp/voice.mp3"
Path(audio_path).write_bytes(r.content)

# 2) Upload pra litterbox (URL pública 24h)
with open(audio_path, "rb") as f:
    r = requests.post("https://litterbox.catbox.moe/resources/internals/api.php",
                      data={"reqtype": "fileupload", "time": "24h"},
                      files={"fileToUpload": ("audio.mp3", f, "audio/mpeg")}, timeout=60)
audio_url = r.text.strip()

# 3) HeyGen lipsync (NÃO TTS — só sincroniza boca)
r = requests.post("https://api.heygen.com/v2/video/generate",
    headers={"X-Api-Key": HEYGEN, "Content-Type": "application/json"},
    json={
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": AVATAR, "avatar_style": "normal"},
            "voice": {"type": "audio", "audio_url": audio_url},
        }],
        "dimension": {"width": 1080, "height": 1920},
    }, timeout=30,
)
video_id = r.json()["data"]["video_id"]

# 4) Polling até completed
while True:
    time.sleep(8)
    rs = requests.get(f"https://api.heygen.com/v1/video_status.get?video_id={video_id}",
                      headers={"X-Api-Key": HEYGEN}, timeout=20)
    d = rs.json()["data"]
    if d.get("status") == "completed":
        Path("/tmp/video_final.mp4").write_bytes(requests.get(d["video_url"], timeout=180).content)
        subprocess.run(["open", "/tmp/video_final.mp4"])
        break
    if d.get("error"):
        raise RuntimeError(d["error"])
```

## Custo por Reel (60s)

| Item | Custo |
|---|---|
| ElevenLabs (~600 chars) | ~0.5% do plano Creator/mês = grátis |
| HeyGen lipsync 60s | ~60 credits ≈ R$5 |
| **Total** | **~R$5/Reel** |

## Limitações conhecidas (2026-05-05)

1. **Voz**: clone Instant ElevenLabs (~85% qualidade). Pra ~95% subir pra **Voice Clone Pro** (5-10min áudio limpo). Já tem material em `/tmp/rudnei_voice_raw.enhanced.wav`.
2. **Aspect**: HeyGen retorna 1080×1920 mas pode precisar smart_crop_face do pipeline DOMINA.IA pra reframing.
3. **Litterbox 24h**: pra produção considerar S3/CloudFront fixo.
4. **HeyGen credits**: monitorar consumo, recarregar via wallet quando <100.

## Próximas melhorias (TODO mapeadas)

- [ ] Voice Clone Pro ElevenLabs (qualidade 95%+)
- [ ] Tunar `stability` (testar 0.4 vs 0.5 vs 0.6)
- [ ] Tunar `style` (testar 0.2 vs 0.3 vs 0.4)
- [ ] Aplicar pipeline DOMINA.IA completo (legendas + overlays) após HeyGen
- [ ] Estudar emotions ElevenLabs API v2 (`emotion: "calm/excited/serious"`)
- [ ] Adicionar SSML pra pausas naturais (`<break time="0.5s"/>`)
- [ ] B-roll automático intercalado (Pexels API + Whisper tagging)

## Histórico de evolução

- **2026-05-05 v1**: HeyGen photo_avatar standard — qualidade ruim (CEO chamou de "painha")
- **2026-05-05 v2**: HeyGen Avatar IV — gestos artificiais
- **2026-05-05 v3**: HeyGen Video Avatar (treinado) + voz HeyGen — voz robotizada
- **2026-05-05 v4 (vencedora)**: HeyGen Video Avatar + ElevenLabs voice clone — aprovada
