---
title: LP Estática — Pacote Completo de Otimização de Performance
type: playbook
domain: dev
tags:
- performance
- landing-page
- lcp
- webp
- lazy-loading
- intersection-observer
- scroll-reveal
- sips
- pillow
- sftp
- hostinger
agents:
- dev
- cro-specialist
- traffic
created: 2026-05-12
verified: 2026-05-12
source: implementação real LPs seudominio.com.br/f1 e /r1 (12-Mai-2026)
status: validated-in-production
links:
- target: scroll-reveal-calibration
  type: companion
- target: image-format-decision-png-jpg-webp
  type: companion
- target: local-image-toolkit-sips-pillow
  type: companion
- target: feedback-lp-performance
  type: feedback-source
axis: ops
---

# LP Estática — Pacote Completo de Otimização de Performance

> **Aplica-se a:** qualquer LP servida do Hostinger (LiteSpeed) ou similar, HTML estático com pixels de tracking.
> **Ganho típico:** first paint -90% (de ~2.5 MB para ~120 KB em browsers modernos), worst-case scroll reveal -57%.

## Princípio

"LP lenta" não é um sintoma único — tem **3 camadas distintas** que precisam ser diagnosticadas separadamente:

1. **Tempo de chegar (LCP/FCP):** servidor → HTML → assets do hero.
2. **Tempo de aparecer ao scroll:** animações reveal-on-scroll mal calibradas.
3. **Tempo de virar interativo (TTI):** JavaScript de tracking bloqueando main thread.

Tratar tudo como "peso de imagem" é o erro mais comum — e mascara a causa raiz quando o sintoma é scroll travado.

---

## Diagnóstico — 4 passos rápidos (10 minutos)

### Passo 1: TTFB e compressão
```bash
curl -w "TTFB: %{time_starttransfer}s | Total: %{time_total}s | Size (br): %{size_download} bytes\n" \
     -H "Accept-Encoding: br" -o /dev/null -s "https://URL/"
```
- **TTFB < 200 ms** = backend OK; gargalo é frontend.
- **Sem `content-encoding: br|gzip`** = ativar Brotli no servidor é o primeiro passo.

### Passo 2: Peso dos assets
```bash
curl -s --compressed "https://URL/" -o /tmp/lp.html
python3 -c "
import re
html = open('/tmp/lp.html').read()
imgs = set(re.findall(r'<img[^>]+src=\"([^\"]+)\"', html))
bgs = set(re.findall(r\"url\(['\\\"]?([^)'\\\"]+)['\\\"]?\)\", html))
for u in sorted(imgs | bgs):
    if any(u.lower().endswith(e) for e in ['.jpg','.png','.webp']):
        print(u)
"
# Em seguida pesa cada uma com curl -sI
```

### Passo 3: Render-blocking
```bash
# Conta CSS/JS inline e externos
grep -cE '<script[^>]*src=' /tmp/lp.html
grep -cE '<link[^>]*rel="stylesheet"' /tmp/lp.html
grep -cE 'rel="(preload|preconnect)"' /tmp/lp.html
```
- **CSS inline > 50 KB** = candidate para split em critical-path.
- **`<script>` sem `async`/`defer` no `<head>`** = bloqueia parser.
- **0 preload do hero** = LCP atrasado.

### Passo 4: Reveal-on-scroll
```bash
grep -nE "threshold:|rootMargin:|transition: opacity 0\\.[5-9]s" /tmp/lp.html
```
- `threshold > 0` ou `rootMargin` negativo no bottom = reveal tarde demais.
- `transition` ≥ 0.8s = animação longa demais para scroll mobile.

---

## Pacote de Otimização — 7 ações cirúrgicas

### 1) Hero: PNG → JPG → WebP com fallback

Foto grande em PNG é o erro mais comum. **Sempre** converter para JPG + WebP, mantendo PNG original como safety net no servidor (não referenciado no HTML).

**Comandos locais (sem brew):**
```bash
# JPG via sips nativo macOS (resize + recompress)
sips -Z 1280 -s format jpeg -s formatOptions 75 hero.png --out hero.jpg

# WebP via Pillow do Python (já vem no sistema)
python3 -c "
from PIL import Image
img = Image.open('hero.png')
ratio = 1280 / img.width
img.resize((1280, int(img.height * ratio)), Image.LANCZOS) \\
   .convert('RGB').save('hero.webp', 'WebP', quality=78, method=6)
"
```

**Ganho típico:** PNG 2 MB → JPG 200 KB → WebP **80 KB (-96%)**.

### 2) CSS: `image-set()` para backgrounds

Sempre dobrar com `-webkit-image-set()` (Safari/iOS pré-padrão) **antes** da declaração standard:

```css
background-image: url('hero.jpg'); /* fallback ultra-antigo */
background-image: -webkit-image-set(url('hero.webp') type('image/webp'), url('hero.jpg') type('image/jpeg'));
background-image: image-set(url('hero.webp') type('image/webp'), url('hero.jpg') type('image/jpeg'));
```

### 3) HTML: `<picture>` para todas as `<img>`

Padrão único, browser escolhe sozinho:
```html
<picture>
  <source srcset="case.webp" type="image/webp">
  <img loading="lazy" decoding="async" src="case.jpg" alt="..." style="...">
</picture>
```

### 4) Hero: preload com fetchpriority

Adicionar no `<head>`, após meta tags principais:
```html
<link rel="preload" as="image" href="hero.webp" type="image/webp" fetchpriority="high">
```

Como preload e WebP têm o mesmo suporte (browsers modernos), pode preloadar **só o WebP** — browsers antigos ignoram o preload e pegam o JPG via `<picture>`/`image-set()`.

### 5) Preconnect para serviços de terceiros

```html
<link rel="preconnect" href="https://chk.eduzz.com" crossorigin>
<link rel="preconnect" href="https://connect.facebook.net" crossorigin>
<link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>
<link rel="dns-prefetch" href="https://chk.eduzz.com">
```

### 6) Lazy loading nativo nos `<img>` abaixo da dobra

```html
<img loading="lazy" decoding="async" src="..." alt="...">
```

Nunca aplicar no hero (atrasa LCP). Regra: lazy só em imagens fora do viewport inicial.

### 7) Reveal-on-scroll: calibração snappy

Ver `[[scroll-reveal-calibration]]` para detalhes. Resumo:
- `threshold: 0` (era 0.12)
- `rootMargin: '0px 0px 250px 0px'` (positivo no bottom, era -60px)
- `transition: 0.4s` (era 0.9s)
- `translateY(14px)` (era 40px)
- Stagger delays 0.04s–0.20s (era 0.1s–0.5s)
- Manter `@media (prefers-reduced-motion: reduce)` para acessibilidade

---

## Deploy seguro — Hostinger via SFTP+expect

`sshpass` não está instalado no Mac. Usar `expect` como alternativa:

```bash
cat > /tmp/sftp.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 60
spawn sftp -P 65002 -o StrictHostKeyChecking=no ${HOSTINGER_USER}@${VPS_HOST}
expect "*assword*"
send "[REMOVIDA 05-Set-2026 — ver ~/_secrets/hostinger.env (chmod 600) ou 1Password vault DOMINA]\r"
expect "sftp>"

# Backup remoto SEMPRE antes de sobrescrever
send "rename .../public_html/SUBDOMINIO/index.html .../public_html/SUBDOMINIO/index-prev-$(date +%Y%m%d-%H%M%S).html\r"
expect "sftp>"

# Upload
send "put /tmp/index.html .../public_html/SUBDOMINIO/index.html\r"
expect "sftp>"

send "bye\r"
expect eof
EOF
chmod +x /tmp/sftp.exp && /tmp/sftp.exp
```

**Regras de segurança:**
- **Renomear** índice atual ANTES de subir o novo (backup remoto timestampado).
- **Não deletar** versões originais de assets — manter PNG original como fallback.
- **Validar pós-deploy** com curl: HTTP 200, content-type correto, tamanho dentro do esperado.

---

## Resultados validados em produção

| LP | Estado inicial | Estado final | Redução first paint |
|---|---|---|---|
| `/f1` | 1.305 KB imagens, sem lazy | 219 KB WebP, lazy, preload | **-91%** |
| `/r1` | 2.728 KB imagens (PNG 2MB hero) | 117 KB WebP, lazy, preload | **-96%** |
| Reveal-on-scroll | worst-case 1.400 ms | worst-case 600 ms | **-57%** |

---

## Quando NÃO aplicar este playbook

- LPs com tráfego < 500 visitas/mês: ROI baixo, foco em conversão estrutural primeiro.
- LPs em plataformas SaaS (Klickart, Hotmart Pages, Leadlovers): você não controla o HTML.
- LPs já com PageSpeed Insights > 85 em mobile: provável que esteja OK.

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| Otimizar antes de medir | Adivinhar gargalo = perder tempo. Mede TTFB + assets + reveal antes. |
| Aplicar `loading="lazy"` no hero | Atrasa LCP — o navegador adia o download justo da imagem que vai aparecer primeiro. |
| Trocar PNG sem manter fallback | Risco de imagem quebrada. Sempre referencie JPG no `src` e mantenha PNG no servidor. |
| Mexer em tracking sem alinhar com @traffic | Defer/lazy do Meta Pixel pode quebrar attribution de campanhas ativas. |
| Não criar backup remoto antes do upload | LP em produção, qualquer mexida sem rollback é risco alto. |
| `rootMargin` negativo no bottom do IntersectionObserver | Faz reveal disparar TARDE — exato oposto do desejado para sensação de velocidade. |
