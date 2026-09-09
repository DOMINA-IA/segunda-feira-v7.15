---
name: lp-audit
description: "Audita landing page em duas trilhas — estrutura (link morto, JS órfão, meta tag, CTA) e performance (peso, LCP, render-blocking). Use antes de publicar LP ou quando estiver lenta. NOT for: LP no ar com sintoma — é /lp-live-debug."
axis: ops
harnesses:
  claude-code: full
  codex: full
---

# /lp-audit — Auditoria de Landing Page

> **Funde `lp-audit` + `lp-performance-audit` (05-Set-2026).** Mesma finalidade — garantir que a
> LP funciona antes de gastar tráfego nela — em duas dimensões que sempre foram consultadas juntas.

**Escolha a trilha pela dor:** página **quebrada ou suspeita** → Trilha A. Página **lenta ou
pesada** → Trilha B. Antes de publicar algo com verba atrás → **as duas**.

---

## Trilha A — Estrutura

Rode na ordem; o item 2 é o que mais morde.

**1. Links âncora.** Grep `href="#[id]"` → confirmar que existe `id="X"` correspondente.
FAIL = link aponta para id inexistente.

**2. Dependências JS mortas** *(o defeito mais caro)*. Grep no `<script>` por `lenis`,
`locomotiveScroll`, `barba`, `swiper` que não estejam carregados no `<head>`.

> **Padrão crítico:** `e.preventDefault()` seguido de chamada a objeto inexistente deixa o
> botão **completamente morto** — sem erro visível. Foi assim que um CTA parou sem ninguém notar.

**3. Meta tags.** `viewport`, `description`, `og:title`, `og:description`, `link rel="icon"`.

**4. CTAs.** Todo botão leva a destino existente. Conferir `onclick` **e** `href` — divergência
entre os dois já mandou tráfego para o checkout errado.

**5. Acentuação PT-BR.** Grep por `Ã`, `Â`, `nao`, `voce`, `sera` — encoding quebrado ou texto
sem acento em página de venda destrói credibilidade.

**6. Formulários.** `action`, `method`, `name` em cada campo, e destino que aceita o POST.

---

## Trilha B — Performance

**Fase 1 — Diagnóstico.** Medir antes de mexer: peso total, maior asset, render-blocking no
`<head>`, imagens sem `width`/`height` (causam layout shift), fontes sem `display=swap`.

**Fase 2 — Plano por ROI.** Ordenar por KB economizado ÷ esforço. Quase sempre: converter PNG
para WebP > adiar script de terceiro > subsetting de fonte > minificar.

**Fase 3 — Execução.** Uma mudança por vez, medindo entre elas — senão você não sabe qual ganhou.

**Fase 4 — Validação em produção.** `curl` não detecta cache de asset: se o HTML é `no-store` e
o JS fica cacheado, o app quebra em silêncio. **Bumpar `?v=` sempre.**

### Métricas alvo (mobile, 4G simulado)

| Métrica | Bom | Ótimo |
|---|---|---|
| TTFB | < 200 ms | < 100 ms |
| LCP | < 2,5 s | < 1,5 s |
| Transferido no first paint | < 500 KB | < 200 KB |

---

## Saída

Tabela por item: `PASS` / `FAIL` / `N/A`, com localização exata (`arquivo:linha`) e o ganho
estimado quando for performance. Sem localização, o achado não é acionável.

## Anti-patterns

Auditar performance com a estrutura quebrada (otimiza página que não funciona) · confiar em
`curl` para validar cache · trocar 5 coisas e medir uma vez · reportar "está lento" sem o número.
