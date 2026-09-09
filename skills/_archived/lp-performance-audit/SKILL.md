---
name: lp-performance-audit
description: "Auditoria e otimização de performance de LP/landing page estática — Use quando a página estiver lenta, carregando devagar ou pesada: diagnostica peso de assets, velocidade de carregamento, render-blocking e reveal-on-scroll. Entrega plano de ação com ganho estimado. Para LPs no Hostinger ou similar. NOT for: bugs estruturais/copy/CRO (links quebrados, JS morto, CTAs, acentuação) — isso é /lp-audit."
context_fork: true
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# LP Performance Audit — Skill de Auditoria e Otimização de Landing Page

## Quando usar

Invocar `/lp-performance-audit` quando o usuário relatar:
- "LP está lenta"
- "demora pra abrir"
- "trava ao rolar / scroll engasgado"
- "vídeo/imagem demora pra aparecer"
- Antes de iniciar campanhas Meta Ads (LCP afeta CPM no leilão)

## Pré-requisito: separar o sintoma

ANTES de tocar em arquivo, perguntar **especificamente** qual é a percepção:

1. **"Demora pra aparecer (tela em branco)"** → LCP/FCP — atacar peso de assets + render-blocking
2. **"Trava ao rolar / engasga"** → INP/animation — atacar reveal-on-scroll + canvas animations
3. **"Demora pra clicar e algo acontecer"** → TTI — atacar JS de tracking (GTM/Pixel)
4. **"Lenta só no mobile"** → CPU-bound — atacar animações + JS pesado

Cada sintoma tem causa raiz diferente. Nunca aplicar otimização sem separar — o erro mais comum é tratar tudo como peso de imagem.

## Pipeline padrão (4 fases)

### Fase 1 — Diagnóstico (10 min)

```bash
# 1. TTFB + Brotli
curl -w "TTFB: %{time_starttransfer}s | Total: %{time_total}s | Size: %{size_download} bytes\n" \
     -H "Accept-Encoding: br" -o /tmp/lp.html.br -s "https://URL/"

# 2. Headers
curl -sI -H "Accept-Encoding: br, gzip" "https://URL/" | grep -iE "content-|cache-|server"

# 3. HTML descomprimido pra análise
curl -s --compressed "https://URL/" -o /tmp/lp.html

# 4. Mapeamento de assets, scripts, CSS
python3 -c "
import re
html = open('/tmp/lp.html').read()
styles = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html, re.DOTALL)
imgs = set(re.findall(r'<img[^>]+src=\"([^\"]+)\"', html))
bgs = set(re.findall(r\"url\(['\\\"]?([^)'\\\"]+)['\\\"]?\)\", html))
print(f'CSS inline: {sum(len(s) for s in styles)//1024} KB')
print(f'JS inline: {sum(len(s) for s in scripts)//1024} KB em {len(scripts)} blocos')
print('Assets:', sorted({u for u in imgs|bgs if any(u.lower().endswith(e) for e in [\".jpg\",\".png\",\".webp\"])}))
"

# 5. Pesar cada asset
for img in ASSETS_AQUI; do
  curl -sI "$BASE/$img" | grep -i content-length
done

# 6. Render-blocking + reveal
grep -nE "rel=\"(preload|preconnect)\"" /tmp/lp.html
grep -nE "loading=\"lazy\"|<picture>" /tmp/lp.html
grep -nE "threshold:|rootMargin:|transition:.*0\.[5-9]s" /tmp/lp.html
```

### Fase 2 — Plano de ação (em ordem de ROI)

Sempre apresentar ANTES de executar:

| # | Ação | Esforço | Ganho |
|---|---|---|---|
| 1 | Otimizar imagens > 200 KB (PNG→JPG, WebP) | 5 min/img | -60 a -95% |
| 2 | Adicionar `loading="lazy"` em imagens abaixo da dobra | 2 min | -50 a -80% no first paint |
| 3 | Adicionar `<link rel="preload">` no hero | 1 min | -300 a -800 ms LCP |
| 4 | Adicionar `<link rel="preconnect">` para checkouts/tracking | 1 min | -100 a -200 ms |
| 5 | Recalibrar reveal-on-scroll | 3 min | -50 a -60% sensação de lentidão |
| 6 | Defer Meta Pixel / GTM / Clarity | 5 min | -500 a -1000 ms TTI mobile |
| 7 | Remover canvas particles | 1 min | -5 a -15% CPU mobile constante |

### Fase 3 — Execução

Aplicar receitas dos playbooks no CORTEX:
- Imagens: ver [[local-image-toolkit-sips-pillow]] em CORTEX
- HTML edits: ver [[lp-static-performance-optimization]] em CORTEX
- Reveal: ver [[scroll-reveal-calibration]] em CORTEX

**Sempre antes do upload:** backup remoto via SFTP rename. Padrão DOMINIA.IA:
```bash
# Hostinger SFTP — host ${VPS_HOST}:65002, user ${HOSTINGER_USER}, senha em ~/.claude/projects/-HOME-/memory/${REDIGIDO}.md
expect -c "
spawn sftp -P 65002 -o StrictHostKeyChecking=no ${HOSTINGER_USER}@${VPS_HOST}
expect \"*assword*\"; send \"SENHA_AQUI\r\"
expect sftp>
send \"rename PATH/index.html PATH/index-prev-$(date +%Y%m%d-%H%M%S).html\r\"
expect sftp>
send \"put /tmp/index.html PATH/index.html\r\"
expect sftp>; send \"bye\r\"
expect eof
"
```

### Fase 4 — Validação em produção

```bash
# HTTP 200 + content-type + peso
for asset in HERO_WEBP HERO_JPG HTML; do
  curl -sI "https://URL/$asset" | head -3
done

# Picture/lazy/preload no HTML servido
curl -s --compressed "https://URL/" | grep -cE "<picture>|loading=\"lazy\"|rel=\"preload\""
```

## Métricas alvo (mobile, 4G simulado)

| Métrica | Bom | Ótimo |
|---|---|---|
| TTFB | < 200 ms | < 100 ms |
| LCP | < 2.5 s | < 1.5 s |
| Total transferido (first paint) | < 500 KB | < 200 KB |
| Worst-case reveal | < 800 ms | < 500 ms |

## Anti-Patterns (não fazer)

- Otimizar antes de medir
- Aplicar lazy loading no hero
- Deletar PNG original ao criar WebP
- Mexer em tracking sem checar com @traffic (pode quebrar attribution)
- Cantar vitória antes do usuário testar

## Quando escalar para outro agente

- Decisão sobre defer/lazy de Meta Pixel → consultar **@traffic** primeiro
- Reestruturação de HTML (não só performance) → escalar para **@dev** com story
- Otimização de funil completo (CRO, não só perf) → **@cro-specialist**
