---
name: video-to-pdf
description: "Pipeline completo de transcrição de vídeos e geração de PDFs educacionais profissionais. Use quando precisar transcrever vídeos de Vimeo, YouTube ou qualquer plataforma, gerar material didático em PDF, ou converter aulas/cursos em documentos formatados."
tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
arguments:
  - name: url
    description: URL do vídeo, playlist ou canal
    required: false
  - name: platform
    description: "Plataforma: vimeo | youtube | url (default: url)"
    required: false
  - name: brand
    description: Nome do instituto/marca para o PDF
    required: false
  - name: whisper_model
    description: "Modelo Whisper: base | small | medium (default: base)"
    required: false
  - name: output_dir
    description: "Pasta de saída (default: ~/Downloads)"
    required: false
---

# Video to PDF Pipeline

Transcreve vídeos de qualquer plataforma e gera PDFs educacionais profissionais com layout editorial.

## Parâmetros

| Param | Default | Opções |
|-------|---------|--------|
| `platform` | url | vimeo, youtube, url |
| `credentials` | - | usuário:senha (quando necessário) |
| `videos` | - | URLs, IDs, ou "all" |
| `brand` | - | Nome do instituto/marca |
| `language` | pt | Código ISO do idioma |
| `whisper_model` | base | base, small, medium |
| `output_dir` | ~/Downloads | Qualquer caminho absoluto |

---

## Fase 0: Pre-Flight (Dependências)

Verificar e instalar TODAS as dependências antes de começar. Executar este script Bash:

```bash
#!/bin/bash
set -e
TEMP_DIR="$HOME/Downloads/video_temp"
mkdir -p "$TEMP_DIR"

echo "=== Verificando dependências ==="

# 1. yt-dlp
if ! command -v yt-dlp &>/dev/null; then
  echo "Instalando yt-dlp..."
  if [[ "$(uname)" == "Darwin" ]]; then
    brew install yt-dlp 2>/dev/null || pip3 install yt-dlp
  else
    pip3 install yt-dlp
  fi
fi
echo "yt-dlp: $(yt-dlp --version)"

# 2. ffmpeg
if ! command -v ffmpeg &>/dev/null; then
  if [[ -f "$HOME/ffmpeg" ]]; then
    export PATH="$HOME:$PATH"
  elif [[ -f "$HOME/ffmpeg/ffmpeg" ]]; then
    export PATH="$HOME/ffmpeg:$PATH"
  else
    echo "Instalando ffmpeg..."
    if [[ "$(uname)" == "Darwin" ]]; then
      brew install ffmpeg
    else
      sudo apt-get install -y ffmpeg
    fi
  fi
fi
echo "ffmpeg: $(ffmpeg -version 2>&1 | head -1)"

# 3. whisper (openai-whisper)
if ! command -v whisper &>/dev/null; then
  echo "Instalando whisper..."
  pip3 install openai-whisper
fi
echo "whisper: instalado"

# 4. PyMuPDF (fitz)
python3 -c "import fitz" 2>/dev/null || {
  echo "Instalando PyMuPDF..."
  pip3 install PyMuPDF
}
echo "PyMuPDF: $(python3 -c 'import fitz; print(fitz.version)')"

echo "=== Todas dependências OK ==="
```

**Se qualquer instalação falhar:** reportar o erro e sugerir instalação manual antes de prosseguir.

---

## Fase 1: Acesso à Plataforma

### Opção A: yt-dlp direto (preferencial)

Para YouTube, Vimeo público, e qualquer URL compatível:

```bash
# Listar vídeos de uma playlist/canal
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(duration_string)s" "URL_AQUI"

# Com credenciais (Vimeo privado)
yt-dlp --username "EMAIL" --password "SENHA" --flat-playlist --print "%(id)s | %(title)s" "URL_AQUI"
```

### Opção B: Playwright (quando yt-dlp falha com login)

Usar APENAS se yt-dlp retornar erro de autenticação:

```bash
# Instalar Playwright se necessário
pip3 install playwright && playwright install chromium
```

Fluxo Playwright:
1. Abrir browser com `playwright.chromium.launch(headless=False)`
2. Navegar até a página de login da plataforma
3. Preencher credenciais e submeter
4. Navegar até a biblioteca de vídeos
5. Extrair URLs dos vídeos via DOM
6. Fechar browser
7. Passar URLs para yt-dlp

### Decisão de Roteamento

```
URL fornecida?
  SIM -> yt-dlp direto (tentar sem login primeiro)
    Falhou com 403/401?
      Credenciais fornecidas?
        SIM -> yt-dlp --username --password
          Falhou novamente?
            SIM -> Playwright login -> extrair URLs -> yt-dlp
        NÃO -> Solicitar credenciais ao usuário
  NÃO -> Solicitar URL ao usuário
```

---

## Fase 2: Download de Áudio

```bash
TEMP_DIR="$HOME/Downloads/video_temp"
mkdir -p "$TEMP_DIR"

# Download áudio MP3 128kbps — um vídeo
yt-dlp -x --audio-format mp3 --audio-quality 128K \
  --ffmpeg-location "$(which ffmpeg)" \
  -o "$TEMP_DIR/%(title)s.%(ext)s" \
  "URL_DO_VIDEO"

# Download de múltiplos vídeos (playlist)
yt-dlp -x --audio-format mp3 --audio-quality 128K \
  --ffmpeg-location "$(which ffmpeg)" \
  -o "$TEMP_DIR/%(playlist_index)02d - %(title)s.%(ext)s" \
  "URL_DA_PLAYLIST"

# Com credenciais
yt-dlp -x --audio-format mp3 --audio-quality 128K \
  --username "EMAIL" --password "SENHA" \
  --ffmpeg-location "$(which ffmpeg)" \
  -o "$TEMP_DIR/%(playlist_index)02d - %(title)s.%(ext)s" \
  "URL"
```

**Verificação pós-download:**
```bash
# Contar arquivos baixados
ls -la "$TEMP_DIR"/*.mp3 | wc -l
# Verificar tamanhos (nenhum deve ser 0 bytes)
find "$TEMP_DIR" -name "*.mp3" -size 0 -print
```

---

## Fase 3: Transcrição com Whisper

### Transcrição individual
```bash
whisper "$TEMP_DIR/arquivo.mp3" \
  --model base \
  --language pt \
  --output_format txt \
  --output_dir "$TEMP_DIR"
```

### Transcrição em lote (paralelo)
```bash
#!/bin/bash
TEMP_DIR="$HOME/Downloads/video_temp"
MODEL="base"  # ou small, medium
LANG="pt"
MAX_PARALLEL=3

process_file() {
  local file="$1"
  local basename=$(basename "$file" .mp3)
  echo "Transcrevendo: $basename"
  whisper "$file" --model "$MODEL" --language "$LANG" \
    --output_format txt --output_dir "$TEMP_DIR"
  echo "Concluído: $basename"
}

export -f process_file
export TEMP_DIR MODEL LANG

# Processar em paralelo (máximo 3 simultâneos)
find "$TEMP_DIR" -name "*.mp3" -print0 | \
  xargs -0 -P "$MAX_PARALLEL" -I {} bash -c 'process_file "{}"'

echo "=== Transcrição concluída ==="
ls -la "$TEMP_DIR"/*.txt | wc -l
```

### Modelos Whisper — Guia de Escolha

| Modelo | VRAM | Velocidade | Qualidade PT | Quando Usar |
|--------|------|-----------|-------------|-------------|
| base | ~1GB | Rápido | Boa | Vídeos claros, áudio limpo |
| small | ~2GB | Médio | Muito boa | Padrão recomendado |
| medium | ~5GB | Lento | Excelente | Áudio ruim, sotaques fortes |

---

## Fase 4: Geração do PDF

### REGRA CRÍTICA: Fonte com Suporte a Acentos

O PDF DEVE renderizar corretamente: ã é í ó ú ç Ã É Í Ó Ú Ç ñ

**Estratégia de fonte (em ordem de preferência):**

1. macOS: `/System/Library/Fonts/Helvetica.ttc` ou `/Library/Fonts/Arial Unicode.ttf`
2. Linux: `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
3. Fallback: baixar NotoSans de `https://fonts.google.com/noto/specimen/Noto+Sans`

**Teste obrigatório antes de gerar:**
```python
import fitz
doc = fitz.open()
page = doc.new_page()
font = fitz.Font(fontfile="/System/Library/Fonts/Helvetica.ttc")
page.insert_font(fontname="helvttf", fontbuffer=font.buffer)
tw = fitz.TextWriter(page.rect)
tw.append(
    (72, 100),
    "Teste: ação, educação, você, saúde, único",
    fontsize=14,
    font=font,
)
tw.write_text(page)
doc.save("/tmp/test_acentos.pdf")
doc.close()
print("Verificar /tmp/test_acentos.pdf — acentos OK?")
```

### Script Python Completo para Geração do PDF

Script completo (classe `PDFGenerator` + função `generate_pdf_from_transcriptions`) extraído para reduzir o tamanho deste arquivo. Implementa: capa com header escuro + barra de stats, sumário numerado, corpo de capítulo com word-wrap e callout boxes (DICA verde / ATENÇÃO vermelho), checklist final, rodapé paginado. Ver:

**`$HOME/.claude/skills/_reference/video-to-pdf-scripts.md`**

### Uso do Script

Salvar o script acima como `~/Downloads/video_temp/generate_pdf.py` e executar:

```bash
python3 ~/Downloads/video_temp/generate_pdf.py
```

Ou importar a função diretamente via Bash:

```bash
python3 -c "
from generate_pdf import generate_pdf_from_transcriptions
generate_pdf_from_transcriptions(
    transcription_dir='$HOME/Downloads/video_temp',
    brand='NOME_DO_INSTITUTO',
    title='Título do Material',
    subtitle='Subtítulo opcional',
    output_dir='$HOME/Downloads'
)
"
```

---

## Fase 5: Limpeza

```bash
TEMP_DIR="$HOME/Downloads/video_temp"

# Verificar PDFs gerados
echo "=== PDFs gerados ==="
ls -lh "$HOME/Downloads/"*.pdf 2>/dev/null

# Limpar temporários
echo "=== Limpando temporários ==="
rm -f "$TEMP_DIR"/*.mp3
rm -f "$TEMP_DIR"/*.txt
rm -f "$TEMP_DIR"/*.py
rm -f "$TEMP_DIR"/*.ttf 2>/dev/null
rmdir "$TEMP_DIR" 2>/dev/null

echo "=== Limpeza concluída ==="
```

---

## Pipeline Completo — Sequência de Execução

```
FASE 0: Pre-Flight
  +-- Verificar/instalar: yt-dlp, ffmpeg, whisper, PyMuPDF
       |
FASE 1: Acesso
  +-- Identificar plataforma -> listar vídeos -> seleção
       |
FASE 2: Download
  +-- yt-dlp -x --audio-format mp3 -> ~/Downloads/video_temp/
       |
FASE 3: Transcrição
  +-- whisper --model {model} --language {lang} -> .txt
       |
FASE 4: PDF
  +-- Teste acentos -> gerar PDF educacional -> ~/Downloads/
       |
FASE 5: Limpeza
  +-- Remover MP3, TXT temporários -> manter apenas PDFs
```

## Tratamento de Erros

| Erro | Causa | Solução |
|------|-------|---------|
| `ERROR: 403 Forbidden` | Vídeo privado sem login | Adicionar --username/--password ou usar Playwright |
| `ERROR: unable to extract` | URL inválida ou plataforma não suportada | Verificar URL, tentar copiar do browser |
| `whisper: command not found` | Whisper não instalado | `pip3 install openai-whisper` |
| `ffmpeg: command not found` | ffmpeg não no PATH | Verificar ~/ffmpeg ou instalar via brew/apt |
| Acentos quebrados no PDF | Fonte built-in sem suporte UTF-8 | Usar fonte TrueType do sistema (ver Fase 4) |
| PDF com páginas em branco | Transcrição vazia | Verificar .txt antes de gerar — pular vazios |
| `MemoryError` no Whisper | Modelo grande demais | Usar modelo `base` em vez de `medium` |

## Organização com Claude (Fase 3.5 — Opcional)

Após a transcrição bruta, usar Claude para organizar o conteúdo antes de gerar o PDF:

**Prompt para organização:**
```
Você é um editor educacional. Organize a transcrição abaixo em formato didático:

1. Divida em seções lógicas com títulos descritivos
2. Converta fala informal em texto fluido e claro
3. Mantenha 100% do conteúdo original — NÃO invente nada
4. Adicione marcadores "DICA:" para insights importantes
5. Adicione marcadores "ATENÇÃO:" para alertas/cuidados
6. Use bullets para listas de itens
7. Mantenha todos os acentos corretos (português brasileiro)

Transcrição:
[COLAR CONTEÚDO DO .TXT AQUI]
```

Isso melhora significativamente a qualidade do PDF final.

## Exemplos de Uso

### Exemplo 1: Curso no Vimeo (privado)
```
/video-to-pdf
  url: https://vimeo.com/showcase/12345678
  platform: vimeo
  credentials: email@exemplo.com:senha123
  brand: Instituto Paulo CLIENTE_EXEMPLO
  whisper_model: small
```

### Exemplo 2: Playlist YouTube (pública)
```
/video-to-pdf
  url: https://www.youtube.com/playlist?list=PLxxxx
  platform: youtube
  brand: Canal Educacional XYZ
  whisper_model: base
```

### Exemplo 3: Vídeo único
```
/video-to-pdf
  url: https://www.youtube.com/watch?v=xxxxx
  brand: Meu Curso
```
