---
name: lp-audit
description: "Auditoria estrutural de landing page HTML antes do deploy — links quebrados, JS morto, meta tags, CTAs funcionais, acentuação PT-BR, formulários. Foco em bugs de estrutura/copy/CRO que travam o funil. NOT for: análise de performance/velocidade (LCP, TTFB, peso de assets) — isso é /lp-performance-audit."
user-invocable: true
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
---

# LP Audit — Auditoria Pré-Deploy

## Contexto

Verifica problemas comuns em LPs antes do deploy. Evita bugs silenciosos como links quebrados, bibliotecas JS removidas, e CTAs que não funcionam.

**Origem:** Bug Lenis na LP Funcionários Invisíveis (06/Abr/2026) — botão "QUERO MINHA VAGA" parou de funcionar porque Lenis foi removido mas o JS ainda referenciava `lenis.scrollTo()`.

---

## Execução

Receber caminho do arquivo HTML como argumento. Se não fornecido, perguntar.

### Checklist de Auditoria (10 itens)

#### 1. Links Âncora
```
Grep por href="#[id]" → verificar se existe elemento com id correspondente
```
- PASS: Todos os href="#X" têm um `id="X"` correspondente
- FAIL: Link aponta para id inexistente

#### 2. Dependências JS Mortas
```
Grep no bloco <script> por: lenis, locomotiveScroll, barba, swiper (se não carregados no <head>)
```
- PASS: Toda variável/objeto referenciada no JS está definida ou importada
- FAIL: Referência a biblioteca removida (causa erro silencioso + e.preventDefault bloqueia ação nativa)

**Padrão crítico:** Se encontrar `e.preventDefault()` seguido de chamada a objeto inexistente, o link/botão fica completamente morto.

#### 3. Meta Tags
Verificar presença de:
- `<meta name="viewport">`
- `<meta name="description">`
- `<meta property="og:title">`
- `<meta property="og:description">`
- `<link rel="icon">`

#### 4. Meta Pixel
```
Grep por fbq.*init e fbq.*PageView
```
- PASS: fbq init + PageView presentes
- FAIL: Pixel ausente ou incompleto

#### 5. CTAs Funcionais
```
Grep por class=".*btn" ou role="button" → verificar href ou onclick
```
- PASS: Pelo menos 1 CTA com ação funcional
- FAIL: Botões sem href ou com href="#" sem handler

**Check adicional — Função correta por posição (funis multi-step):**
```
Tela intro/screen0   → onclick deve chamar startQuiz() / goToScreen(1) / nextStep()
Tela resultado/final → onclick deve chamar goToCheckout() / goToPurchase()
```
Se o botão da tela intro chamar `goToCheckout()`, o funil está invertido (bug silencioso).
Grep por: `onclick="goToCheckout"` em elementos com id="ctaStart" ou na screen0/intro → FAIL se encontrado.

**Origem deste check:** Quiz AI FIRST (08/Abr/2026) — botão intro com `goToCheckout()` em vez de `startQuiz()` fazia usuários irem direto ao checkout sem passar pelo quiz.

#### 6. Responsividade
```
Grep por @media
```
- PASS: Pelo menos 1 media query para mobile (max-width: 640px ou 768px)
- FAIL: Sem media queries

#### 7. Performance
Verificar:
- Iframes pesados (Sketchfab, YouTube sem lazy load)
- Imagens sem `loading="lazy"`
- Scripts bloqueantes no `<head>` sem `async` ou `defer`

#### 8. Acentuação PT-BR
Buscar palavras comuns sem acentuação correta usando regex:
- `\bvoce\b` → deveria ser `você`
- `\bnao\b` → deveria ser `não`
- `\bacao\b` → deveria ser `ação`
- `\btambem\b` → deveria ser `também`
- `\bnegocio\b` → deveria ser `negócio`
- `\bfuncionario\b` → deveria ser `funcionário`
- `\bautomatico\b` → deveria ser `automático`
- `\bpagina\b` → deveria ser `página`

- PASS: Sem palavras sem acento
- FAIL: Lista de palavras a corrigir

#### 9. Scroll Behavior
Se usa smooth scroll:
- Verificar se a lib está carregada (Lenis, Locomotive, etc.)
- OU se usa `scrollIntoView({ behavior: 'smooth' })` nativo
- OU se tem `scroll-behavior: smooth` no CSS

#### 10. Formulário
Se tem `<form>`:
- Verificar `action` ou handler JS
- Verificar campos `required`
- Verificar botão submit

---

## Output

```markdown
## Auditoria LP — [nome do arquivo]

| # | Check | Status | Detalhe |
|---|-------|--------|---------|
| 1 | Links âncora | PASS/FAIL | ... |
| 2 | JS morto | PASS/FAIL | ... |
| 3 | Meta tags | PASS/FAIL | ... |
| 4 | Meta Pixel | PASS/FAIL | ... |
| 5 | CTAs | PASS/FAIL | ... |
| 6 | Responsividade | PASS/FAIL | ... |
| 7 | Performance | PASS/WARN/FAIL | ... |
| 8 | Acentuação | PASS/FAIL | ... |
| 9 | Scroll | PASS/FAIL | ... |
| 10 | Formulário | PASS/FAIL/N/A | ... |

**Veredicto:** APROVADO / BLOQUEADO (se qualquer FAIL nos itens 1, 2 ou 5)
```

Se BLOQUEADO, listar as correções necessárias antes de prosseguir com deploy.
