# create-landing-v3

## Purpose
Criar landing page premium com design dark (template V3) para produtos, fichas de seleção, eventos ou captação.

---

## Task Definition

```yaml
task: create-landing-v3()
responsável: Content (Luna)
responsavel_type: Agente
atomic_layer: Organism

Entrada:
  - campo: nome
    tipo: string
    obrigatório: true
  - campo: objetivo
    tipo: string (captação | seleção | venda | evento)
    obrigatório: true
  - campo: conteudo
    tipo: objeto (título, subtítulo, benefícios, CTA)
    obrigatório: true

Saída:
  - campo: arquivo_html
    tipo: file
    destino: ~/
```

---

## Design System V3

### Paleta base
```css
--p: #6c3aed;     /* roxo principal */
--p-l: #8b5cf6;   /* roxo claro */
--gold: #d4a053;  /* dourado */
--gold-l: #ecc888;
--bg: #09070d;    /* fundo escuro */
--bg2: #0f0b15;
--r: 12px;        /* border-radius */
```

### Componentes disponíveis
- **Marquee** animado (topo)
- **Hero** com badge, título gradiente, stats, CTA shimmer
- **Benefits grid** (2 cols desktop, 1 col mobile)
- **Form** com validação, radio groups, máscaras
- **Price box** com destaque dourado
- **FAQ** acordeão
- **Scroll reveal** com IntersectionObserver + fallback 2s
- **Footer** minimalista

### Fontes
- Inter (400, 500, 600, 700, 900) via Google Fonts

### Responsivo
- Breakpoint principal: 640px
- Breakpoint grid: 600px
- Mobile-first em tipografia (clamp)

### Regras
- SEMPRE acentos e cedilha nos textos
- Formulários: mask no WhatsApp, validação visual
- Webhook: fetch POST para API do CLIENTE_EXEMPLO
- Fallback reveal: `setTimeout 2s` para garantir visibilidade

---

## Metadata
```yaml
version: 1.0.0
tags: [landing, html, design, v3, dark]
updated_at: 2026-03-15
```
