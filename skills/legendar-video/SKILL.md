---
name: legendar-video
description: "Queima legendas word-by-word estilo OpusClip em MP4/MOV via pipeline ffmpeg local. Use para Reel ou VSL que precisa de legenda gravada. NOT for: gerar o vídeo em si — isso é /video-avatar."
harnesses:
  - claude-code: full
  - codex: native
  - cursor: limited
  - aider: limited
---

# Legendar Vídeo — Estilo OpusClip Reproduzível

> Pipeline 100% local. Sem APIs externas. Roda em ~2-3 minutos pra vídeo de 1-2 min.

---

## Anatomia do Estilo OpusClip (extraído de referência)

| Elemento | Especificação |
|---|---|
| Posição | Terço inferior, ~78% da altura do vídeo |
| Fonte | Sans-serif geométrica bold, ALL CAPS (Montserrat Black, Avenir Black ou Helvetica Bold) |
| Tamanho | ~7-8% da altura (em 1920px ≈ 140-160px) |
| Cor texto | Branco puro `#FFFFFF` |
| Fundo | Caixa preta sólida `#000000`, padding ~24px, cantos levemente arredondados |
| Palavras por bloco | 1-3 (varia conforme cadência da fala) |
| Highlight | Sublinhado roxo neon `#A855F7` na palavra-chave |
| Sincronização | Word-by-word (kinetic) — palavra "pinta" em sync com áudio |
| Animação | Pop-in sutil ~80ms ao aparecer |

---

## Pipeline (4 etapas)

### Etapa 1 — Extrair áudio mono 16kHz

```bash
mkdir -p /tmp/legenda_work
ffmpeg -hide_banner -loglevel error -y \
  -i input.mp4 \
  -vn -c:a pcm_s16le -ar 16000 -ac 1 \
  /tmp/legenda_work/audio.wav
```

### Etapa 2 — Transcrever com Whisper word-level

Usar `mlx_whisper` (Apple Silicon, ~3x mais rápido) ou `whisper` (CPU/CUDA).

```bash
mlx_whisper --model mlx-community/whisper-small-mlx \
  --language pt \
  --word-timestamps True \
  --output-format json \
  --output-dir /tmp/legenda_work \
  --output-name transcript \
  /tmp/legenda_work/audio.wav
```

**Modelos por trade-off**:
- `whisper-tiny-mlx` — 3x mais rápido, qualidade aceitável só pra inglês
- `whisper-small-mlx` — bom equilíbrio pra português
- `whisper-medium-mlx` — melhor pra português acentuado, mais lento
- `whisper-large-v3-mlx` — máxima qualidade, mais lento

### Etapa 3 — Converter JSON em ASS karaoke

Salvar como `/tmp/whisper_to_ass.py`:

```python
#!/usr/bin/env python3
"""Converte transcript JSON do Whisper em ASS karaoke estilo OpusClip.
Uso: whisper_to_ass.py <transcript.json> <output.ass> <video_height>
"""
import json, sys

if len(sys.argv) != 4:
    print("uso: whisper_to_ass.py <transcript.json> <output.ass> <video_height>")
    sys.exit(2)

JSON_PATH = sys.argv[1]
OUT_PATH = sys.argv[2]
VIDEO_H = int(sys.argv[3])

FONT = "Avenir Next"
FONT_SIZE = int(VIDEO_H * 0.038)
COLOR_TEXT = "&H00FFFFFF"
COLOR_BG = "&H00000000"
COLOR_HIGHLIGHT = "&H00F755A8"
MARGIN_V = int(VIDEO_H * 0.18)
WORDS_PER_BLOCK = 3

def fmt_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"

with open(JSON_PATH) as f:
    data = json.load(f)

all_words = []
for seg in data["segments"]:
    if "words" not in seg:
        continue
    for w in seg["words"]:
        word = w.get("word", "").strip().upper()
        if word:
            all_words.append({"text": word, "start": w["start"], "end": w["end"]})

blocks = []
cur = []
for i, w in enumerate(all_words):
    cur.append(w)
    next_gap = (all_words[i+1]["start"] - w["end"]) if i+1 < len(all_words) else 999
    if len(cur) >= WORDS_PER_BLOCK or next_gap > 0.4 or i == len(all_words)-1:
        blocks.append(cur)
        cur = []

header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: {VIDEO_H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT},{FONT_SIZE},{COLOR_TEXT},{COLOR_TEXT},{COLOR_BG},{COLOR_BG},1,0,0,0,100,100,0,0,3,12,0,2,40,40,{MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

events = []
for block in blocks:
    start = block[0]["start"]
    end = block[-1]["end"] + 0.15
    parts = []
    for w in block:
        dur_cs = max(1, int((w["end"] - w["start"]) * 100))
        parts.append(f"{{\\k{dur_cs}}}{w['text']}")
    text = " ".join(parts)
    text = "{\\fad(80,0)}" + text
    events.append(f"Dialogue: 0,{fmt_time(start)},{fmt_time(end)},Default,,0,0,0,,{text}")

with open(OUT_PATH, "w") as f:
    f.write(header)
    f.write("\n".join(events) + "\n")

print(f"OK — {len(blocks)} blocos, {len(all_words)} palavras → {OUT_PATH}")
```

Rodar:
```bash
HEIGHT=$(ffmpeg -i input.mp4 2>&1 | grep -oE '[0-9]+x[0-9]+' | head -1 | cut -dx -f2)
python3 /tmp/whisper_to_ass.py /tmp/legenda_work/transcript.json /tmp/legenda_work/captions.ass $HEIGHT
```

### Etapa 4 — Queimar legenda no vídeo (burn-in)

```bash
ffmpeg -hide_banner -loglevel warning -y \
  -i input.mp4 \
  -vf "ass=/tmp/legenda_work/captions.ass" \
  -c:v h264_videotoolbox -b:v 8M -tag:v avc1 -pix_fmt yuv420p \
  -c:a copy \
  -movflags +faststart \
  output_legendado.mp4
```

---

## Customizações comuns

### Cor de highlight diferente

`COLOR_HIGHLIGHT` é em formato BGR ASS (`&H00BBGGRR`).
- Verde neon: `&H0050E5A8`
- Amarelo: `&H0000F5FF`
- Vermelho: `&H001818E1`

### Fonte alternativa

Listar fontes do sistema: `fc-list | grep -i "bold\|black"`. Trocar `FONT` no script.

Pra Montserrat Black:
```bash
brew install --cask font-montserrat
```

### Posição vertical

Ajustar `MARGIN_V` no script. Padrão `0.18` = 18% do bottom (terço inferior). `0.30` = mais alto.

### 1 palavra por vez (estilo TikTok agressivo)

Trocar `WORDS_PER_BLOCK = 3` por `WORDS_PER_BLOCK = 1`.

---

## Pré-requisitos

```bash
pip install mlx-whisper          # Apple Silicon
# OU
pip install openai-whisper       # CPU/CUDA

# Verificar libass no ffmpeg
ffmpeg -filters 2>&1 | grep -i ass
```

---

## Quando NÃO usar

- Vídeo já tem legendas queimadas → primeiro extrair áudio limpo
- Vídeo muito longo (>10min) → processar em chunks ou usar `large-v3` em GPU
- Áudio com música alta sobre voz → diarização prévia ou separação (Demucs)
- Vídeo horizontal 16:9 → ajustar `MARGIN_V` (legenda fica grande demais)

---

## Anti-Patterns

| Evitar | Correção |
|--------|----------|
| Usar modelo `tiny` em PT-BR | `small` mínimo, `medium` recomendado |
| Word block de 5+ palavras | Mantém atenção: 1-3 palavras |
| Fundo preto opaco em legenda muito grande | Reduzir `FONT_SIZE` ou usar semi-transparente |
| Highlight em TODA palavra | Quebra hierarquia — só palavra-chave |
| Burn-in sem `-c:a copy` | Re-encoda áudio sem necessidade, perde qualidade |

---

## Referência de execução real (Abr/2026)

Aplicado em `IMG_2522_final.MOV` (89s, 1080x1920) — pipeline completo levou ~3min:
- Whisper small mlx: 70s
- ASS gen: <1s
- ffmpeg burn-in (videotoolbox): 50s

Resultado equivalente ao OpusClip Captions, sem watermark.
