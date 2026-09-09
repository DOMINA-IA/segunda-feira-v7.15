---
name: particulaslp
description: "Aplica o efeito PARTICULASLP em uma landing page — partículas reativas ao cursor com explosão dourada no clique do CTA. Use quando o usuário quiser transformar o hero de uma LP em algo dramático estilo wearebrand.io. Suporta Next.js, HTML puro, WordPress, Webflow e qualquer stack que aceite ESM + canvas."
---

# PARTICULASLP — Skill

> Efeito WebGL custom: foto vira partículas que reagem ao cursor (repulsão dourada) e explodem ao clicar no CTA. Componente em `~/dev/particulaslp/`.

## Quando usar

- Usuário pediu efeito tipo "wearebrand.io", "particle disintegration", "thanos snap", "foto explodindo"
- LP nova ou refresh do hero de LP existente
- Captação de mentoria/desafio/lançamento (alta retenção visual = mais conversão)
- Cliente quer LP "premium" ou "memorável"

**NÃO use** quando: a página precisa de SEO crítico (efeito é client-side), conexão alvo é muito lenta (Three.js + textura ~600KB), ou acessibilidade rígida é requisito.

## Arquivos do componente

```
~/dev/particulaslp/
├── particulaslp.js        # classe ParticulasLP, ESM, ~12KB
├── particulaslp.css       # opcional (estilos canvas + cursor crosshair)
├── README.md              # API completa
├── examples/
│   └── basic.html         # exemplo standalone
└── assets/
    └── sample.jpg
```

## Workflow de aplicação

### 1. Inteligência inicial

Antes de tocar em qualquer arquivo, descubra:

| Pergunta | Como descobrir |
|----------|---------------|
| LP target existe? Onde? | Pergunta ao usuário ou inspeciona repo |
| Stack? (Next.js, HTML puro, WordPress, Webflow...) | `find . -name "*.html" -o -name "package.json"` |
| Foto principal? | Inspeciona LP via `WebFetch` ou `curl` |
| Paleta da LP? | `grep -oE '#[0-9a-fA-F]{3,8}' index.html` |
| CTA principal? | Procura `class="cta"`, `<button>`, `href="#form"` |

### 2. Decisões de design

Antes de aplicar:

- **emberColor** — escolha alinhada à paleta da LP. Dourado padrão (`0xfbbf24`) funciona em 80% dos casos. Se a LP tem ciano/azul forte, considere `0x06b6d4`. Se rosa/magenta, `0xec4899`.
- **hotColor** — sempre uma cor "quente" complementar à ember. Dourado → laranja (`0xff8a00`). Ciano → branco (`0xffffff`). Rosa → vermelho (`0xff3366`).
- **planeWidth/Height** — proporção da foto. Se foto é retrato, mantenha 1.6×1.6. Se é paisagem, ajuste pra 2.0×1.2.

### 3. Integração (HTML puro)

```html
<section class="hero">
  <canvas id="particles-canvas"></canvas>
  <div class="hero-content">
    <h1>...</h1>
    <a href="#inscricao" class="cta-primary">CTA →</a>
  </div>
</section>

<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.183.2/build/three.module.js",
    "particulaslp": "/path/to/particulaslp.js"
  }
}
</script>

<script type="module">
  import { ParticulasLP } from 'particulaslp';
  new ParticulasLP({
    canvas: document.getElementById('particles-canvas'),
    image: '/assets/foto.jpg',
    clickSelector: '.cta-primary',
    clickScrollTo: '#inscricao',
    emberColor: 0xfbbf24,
    hotColor: 0xff8a00,
  });
</script>
```

CSS mínimo do hero:
```css
.hero { position: relative; height: 100vh; overflow: hidden; }
.hero canvas { position: absolute; inset: 0; width: 100%; height: 100%; cursor: crosshair; }
.hero .hero-content { position: absolute; inset: 0; z-index: 2; pointer-events: none; }
.hero .hero-content > * { pointer-events: auto; }
```

### 4. Integração (Next.js / React)

```tsx
'use client';
import { useEffect, useRef } from 'react';
import { ParticulasLP } from '@/lib/particulaslp';

export function HeroParticles({ image }: { image: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    if (!canvasRef.current) return;
    const lp = new ParticulasLP({
      canvas: canvasRef.current,
      image,
      clickSelector: '.cta-primary',
      clickScrollTo: '#form',
    });
    return () => lp.destroy();
  }, [image]);

  return <canvas ref={canvasRef} className="absolute inset-0" />;
}
```

Copie `particulaslp.js` pra `lib/` e ajuste o import.

### 5. Integração (WordPress / Elementor / outros builders)

1. Faz upload do `particulaslp.js` pro WP via plugin tipo "Code Snippets" ou tema custom
2. Adiciona `<script type="importmap">` no `<head>` (Elementor → Custom Code → Header)
3. Adiciona `<canvas>` no hero via widget HTML
4. Inicializa via `<script type="module">` no rodapé do hero

### 6. Validação

Antes de declarar pronto:

```bash
# Servir local
cd /path/to/lp && python3 -m http.server 8765

# Abrir e verificar visualmente
open -a "Google Chrome" "http://localhost:8765/"

# Capturar screenshot
sleep 4 && screencapture -x /tmp/particulas-test.png
```

Use Read no screenshot pra confirmar:
- ✓ Foto sólida visível no estado idle
- ✓ Cursor crosshair visível ao mover
- ✓ Click no CTA dispara explosão (capturar em t=500ms via Quartz mouse click)
- ✓ Scroll smooth pra `clickScrollTo` após explosão

## Trade-offs por stack

| Stack | Facilidade | Performance | Cuidados |
|-------|-----------|-------------|----------|
| HTML puro | Fácil | Boa | Importmap precisa Chrome 89+ ou Safari 16.4+ |
| Next.js | Médio | Boa | Deve usar `'use client'` + `useEffect` |
| Webflow | Difícil | Boa | Tem que injetar via Custom Code, sem importmap → use bundler externo |
| WordPress | Médio | Boa | Conflitos com plugins de cache (purge após deploy) |
| Framer | Médio | Boa | Code component embutido |

## Personalizações comuns

```js
// Cor da brand do cliente (ex: roxo DOMINA.IA)
new ParticulasLP({ ..., emberColor: 0x7c3aed, hotColor: 0xa78bfa });

// Mais agressivo (raio maior)
new ParticulasLP({ ..., cursorRadius: 0.7, cursorForce: 1.0 });

// Explosão mais rápida (urgência)
new ParticulasLP({ ..., explosion: { ramp: 250, hold: 150, fall: 1000 } });

// Performance — mobile-first
new ParticulasLP({ ..., particleCount: 15000, particleSize: 5 });

// Sem cursor (só click — pra LPs serias/B2B)
new ParticulasLP({ ..., triggers: ['click'], clickSelector: '.cta' });
```

## Anti-patterns

| Erro | Por quê dói |
|------|-------------|
| Aplicar em LP de 3 segundos de attention span | Carregamento de Three.js (~500ms) já gastou metade do tempo |
| Usar foto com fundo transparente | Filtro de luminância descarta a maioria dos pixels — fica vazio |
| Foto com >50% de áreas escuras | Mesmo problema — luminância < 0.04 vira buraco |
| `cursorRadius` > 0.8 | Tela inteira reage ao mouse — perde foco |
| Esquecer `pointer-events: none` no overlay | Cursor não chega no canvas, efeito não dispara |

## Fluxo expedito ("aplica isso na minha LP")

```
1. WebFetch URL → identifica foto + paleta + CTAs
2. Baixa foto (curl ou wget)
3. Cria/edita HTML/CSS pra incluir <canvas> + importmap + script init
4. Copia particulaslp.js pro projeto (ou referencia via CDN se for futuro)
5. Sobe http server local na porta 8765
6. Open Chrome + screencapture pra validar:
   - estado idle
   - cursor hover (Quartz move mouse)
   - click CTA (Quartz click) + 3 capturas em t=300/500/800ms
7. EROS Veredito 5/5 antes de declarar pronto
```

## Links rápidos

- README: `~/dev/particulaslp/README.md`
- Exemplo: `~/dev/particulaslp/examples/basic.html`
- Componente: `~/dev/particulaslp/particulaslp.js`
- Primeira aplicação real: (pipeline segunda-feira-jarvis descontinuado — auditoria 2026-07-07) — LP do desafio Mercado Invisível em IA
- Inspiração: https://www.instagram.com/p/${POST_ID}/ (wearebrand.io)
