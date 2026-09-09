---
name: pattern-harvest
description: "Engenharia reversa de padrões replicáveis a partir de uma referência externa (LP, site, imagem ou vídeo que você admira) — extrai arquitetura de página, design system, frameworks de copy e padrões de UX/conversão e gera um blueprint (harvest/<slug>/blueprint.md) para aplicar nos projetos DOMINA.IA sem copiar literalmente. Use quando quiser entender COMO uma referência foi construída e reconstruir a lógica. NOT for: extrair a identidade de marca (cores/voz/arquétipo) — isso é /brand-reverse; NOT for: validar se um criativo próprio passa nos portões de qualidade — isso é /creative-validator."
user-invocable: true
context_fork: true
axis: ops
harnesses:
  - claude-code: full
  - codex: native
  - cursor: limited (sem leitura nativa de imagem — usar descrição textual)
  - aider: limited (sem multimodal)
  - gemini-cli: full (multimodal nativo, ideal para vídeo/imagem)
provider-fallback:
  - anthropic/claude-sonnet-4-6        # primário (visão + raciocínio)
  - google/gemini-3.5-flash            # fallback multimodal barato (via agy) — vídeo/imagem em escala
  - openai/gpt-5.5                      # fallback de raciocínio (via codex) — sem visão no fluxo crítico
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - WebFetch
  - WebSearch
---

# /pattern-harvest — Colheita e Modelagem de Padrões

> **Tipo:** Skill de engenharia reversa aplicada | **Agente padrão:** @creative-director (apoio: @cro-specialist, @copywriter, @dev)
> **Input:** URL de LP/site, screenshot, imagem de criativo, ou vídeo (arquivo/URL)
> **Output:** Blueprint replicável (`harvest/<slug>/blueprint.md`) + ativos extraídos + entrada em `~/patterns/`

## Objetivo

Pegar QUALQUER referência boa que você admira — uma landing page que converte, um anúncio que prende, um site com design forte, um Reel com edição que retém — e **decompor em padrões reutilizáveis** que a equipe consegue aplicar nos projetos sem copiar literalmente. Não é cópia: é destilação de *princípios estruturais*.

**Diferença de skills vizinhas (rule IDS):**

| Skill | Pergunta que responde | Quando usar |
|-------|----------------------|-------------|
| `/brand-reverse` | "Qual é a alma da marca?" (cores, voz, arquétipo) | Replicar identidade |
| `/creative-validator` | "Meu criativo passa nos 7 portões?" | Validar entrega própria |
| **`/pattern-harvest`** | "Como isso foi CONSTRUÍDO e como reconstruo?" | Modelar arquitetura/design/copy/UX de uma referência |

Use `/pattern-harvest` para captar a engenharia; encadeie com `/brand-reverse` quando também quiser a identidade de marca da mesma referência.

---

## Regras Invioláveis

1. **Destilar, nunca plagiar.** O output são *princípios e estruturas* ("hero com prova social acima da dobra + 1 CTA único"), não texto/arte copiados verbatim. Plágio de copy ou arte é proibido.
2. **Acentuação PT-BR correta** em todo blueprint (ã, é, ç, ô, í, ú, â, ê, õ). Rule `visual-rendering-safety`.
3. **Toda colheita alimenta o feedback loop** — registrar o padrão em `~/patterns/` e ingerir no CORTEX. Rule `feedback-loop`.
4. **Confidence score** em afirmações inferidas ("a fonte parece ser Inter [confidence: 0.6]"). Rule `confidence-guardrails`.
5. **Multi-IA honesto** — a etapa de visão usa Claude (`Read` de imagem) ou Gemini (`agy`); declarar quando um harness não consegue ver a referência.

---

## Eixos de Captura (o que extrair)

A skill varre a referência por **6 eixos**. Cada um vira uma seção do blueprint.

### Eixo 1 — Arquitetura de Página / Estrutura
- Sequência de seções (hero → prova → problema → solução → oferta → objeções → CTA → rodapé)
- Hierarquia de informação e ordem de persuasão
- Densidade (long-form vs. enxuta), número de CTAs e onde aparecem
- CLIENTE_EXEMPLO/below the fold: o que ganha a atenção nos primeiros 600px

### Eixo 2 — Design System
- **Cores** — hex + proporção de uso (ex.: "fundo dark #0A0A0A 80%, accent verde #00E676 15%, branco 5%")
- **Tipografia** — famílias de título/corpo/accent, escala de tamanhos, peso, tracking
- **Espaçamento e grid** — ritmo vertical, largura de container, breakpoints aparentes
- **Componentes** — estilo de botões, cards, badges, bordas, sombras, glows, cantos
- **Imagética** — estilo fotográfico/ilustrativo, tratamento, mood

### Eixo 3 — Copy & Mensagem
- Framework dominante (AIDA / PAS / BAB / 4U) — ver `/copywriting`
- Big idea / promessa central e mecanismo único
- Headline + subheadline (estrutura, não texto literal)
- Padrões de hook, prova (números, depoimentos, logos), CTA (verbo + urgência)
- Tom de voz e nível de consciência do público alvejado

### Eixo 4 — UX & Conversão
- Padrões de CRO: âncora de preço, escassez, garantia, risk-reversal
- Fricção de formulário (campos, etapas), microcopy
- Fluxo de navegação e pontos de decisão
- Acessibilidade aparente e mobile-first

### Eixo 5 — Movimento & Mídia (vídeo/Reel/animação)
- Estrutura de roteiro (hook 0-3s → desenvolvimento → CTA)
- Ritmo de cortes, padrão de legendas, b-roll, transições
- Curva de retenção inferida (o que muda a cada 3-5s)
- Áudio: trilha, ducking, padrão de fala

### Eixo 6 — Stack & Implementação (quando inferível)
- Tecnologia provável (React/Next, Tailwind, Framer Motion, Webflow…) [confidence:]
- Como reconstruir: componentes-chave e dependências
- Esforço estimado para replicar o padrão internamente

---

## Fluxo de Execução

### PASSO 0 — Cruzamento (rule cortex-usage.md, seção Cruzamento Obrigatório)
Antes de colher, checar se já modelamos algo parecido:
```bash
python3 ~/cortex/scripts/cortex_engine.py query "padrão <tema da referência>"
grep -ri "<tema>" ~/patterns/ 2>/dev/null
ls ~/.claude/skills/../harvest/ 2>/dev/null   # colheitas anteriores
```
Se já existe blueprint próximo → estender, não recriar.

### PASSO 1 — Ingestão da Referência

**Site / LP (URL):**
```bash
# Conteúdo + estrutura textual
```
Use `WebFetch` para extrair copy, estrutura de headings e CTAs.
Para o design real (cores/layout pixel-a-pixel), capturar screenshot:
```bash
# Screenshot full-page headless (se Chrome disponível)
# Alternativa: pedir ao usuário um print, ou usar a skill /claude-in-chrome
```
> Se houver browser MCP (`claude-in-chrome`), navegar e capturar a página inteira rende o design system com muito mais fidelidade que só o HTML.

**Imagem (criativo/screenshot):**
```bash
# Basta Read da imagem — Claude lê nativamente
```
`Read({file_path: "/caminho/criativo.png"})` → analisar pelos eixos 2, 3, 4.

**Vídeo (arquivo ou URL):**
```bash
# Extrair frames-chave para análise visual (1 frame a cada 2s)
mkdir -p /tmp/harvest-frames
ffmpeg -i "<arquivo.mp4>" -vf "fps=0.5,scale=720:-1" /tmp/harvest-frames/f_%03d.png -hide_banner -loglevel error
# Extrair áudio para transcrição (se relevante para roteiro)
ffmpeg -i "<arquivo.mp4>" -vn -ar 16000 -ac 1 /tmp/harvest-audio.wav -hide_banner -loglevel error
```
Depois `Read` dos frames para mapear estrutura, ritmo e legendas (eixo 5).

> **Fallback multimodal (provider-fallback):** para lote grande de imagens/vídeos, delegar a visão ao Gemini Flash (mais barato em escala):
> ```bash
> OVERLAY=$(cat ~/.claude/model-overlays/gemini.md 2>/dev/null)
> agy "$OVERLAY"$'\n\n'"Descreva o design system e a estrutura destes frames: /tmp/harvest-frames/*.png"
> ```

### PASSO 2 — Análise por Eixos
Varrer a referência pelos 6 eixos relevantes ao tipo de input.
- LP/site → eixos 1, 2, 3, 4, 6
- Imagem/criativo → eixos 2, 3, 4
- Vídeo/Reel → eixos 1, 3, 5
Marcar inferências com `[confidence: X.X]`.

### PASSO 3 — Gerar o Blueprint
Escrever `harvest/<slug>/blueprint.md` (ver template abaixo).
Salvar ativos: screenshots em `harvest/<slug>/refs/`, paleta extraída, frames relevantes.

### PASSO 4 — Plano de Aplicação
Traduzir os padrões para o contexto DOMINA.IA:
- Quais seções/elementos adotar nos nossos projetos
- O que adaptar à nossa marca (cruzar com `/brand-identity`)
- Próximo passo concreto (ex.: "gerar LP com `/empire-landing` usando a arquitetura do eixo 1")

### PASSO 5 — Alimentar Patterns + CORTEX (rule feedback-loop)
```bash
# Padrão validado vai para a base reutilizável
~/cortex/scripts/ingest.sh --title "Padrão: <nome>" --type playbook --domain content \
  --agents creative-director copywriter cro-specialist --tags pattern harvest <tema>
# Anexar o padrão destilado ao arquivo de patterns adequado
# ~/patterns/{angles,hooks,formats,offers}.md conforme o eixo dominante
```

### PASSO 6 — Veredito EROS
Fechar com o bloco de veredito (rule eros-quality) — ver final.

---

## Template do Blueprint

```markdown
# Blueprint: <Nome da Referência>
**Fonte:** <URL/arquivo>  |  **Tipo:** LP | site | imagem | vídeo  |  **Data:** <data>
**Por que esta referência:** <o que a torna digna de modelar>

## 1. Arquitetura
<sequência de seções + ordem de persuasão>

## 2. Design System
- Cores: <hex + proporção>
- Tipografia: <famílias + escala> [confidence:]
- Espaçamento/grid: <ritmo>
- Componentes: <botões, cards, efeitos>

## 3. Copy & Mensagem
- Framework: <AIDA/PAS/BAB>
- Big idea: <promessa>
- Padrões de hook/prova/CTA: <...>

## 4. UX & Conversão
<padrões de CRO, fricção, microcopy>

## 5. Movimento & Mídia (se vídeo)
<estrutura de roteiro, ritmo, retenção>

## 6. Stack & Implementação
<tech provável + como reconstruir> [confidence:]

## Plano de Aplicação DOMINA.IA
- Adotar: <...>
- Adaptar: <...>
- Próximo passo: <skill/ação concreta>

## Padrões extraídos (→ ~/patterns/)
- <padrão 1 reutilizável>
- <padrão 2 reutilizável>
```

---

## Encadeamento com Outras Skills

| Depois de colher, encadear com | Para |
|-------------------------------|------|
| `/extract-design-system` | Automatizar o eixo 2 — extrair tokens CSS/JSON reais de uma URL (importada do skills.sh) |
| `/web-design-guidelines` | Auditar conformidade UX/acessibilidade do que for reconstruído |
| `/frontend-design` | Aplicar direção visual distintiva ao recriar a UI colhida |
| `/brand-identity` | Adaptar o padrão à identidade DOMINA.IA |
| `/brand-reverse` | Extrair também a identidade de marca da referência |
| `/empire-landing` | Construir LP aplicando a arquitetura colhida |
| `/ad-creative` | Gerar criativos com os padrões de design/copy |
| `/copywriting` | Reescrever a copy com o framework identificado |
| `/cro-specialist` (agente) | Aprofundar os padrões de conversão |

---

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| Copiar copy/arte literalmente | Plágio + não é replicável com nossa marca |
| Blueprint genérico ("design moderno e limpo") | Sem hex, sem escala, sem estrutura = inútil |
| Afirmar stack sem marcar confidence | Inferência de tecnologia raramente é certa |
| Não salvar em ~/patterns/CORTEX | Colheita morre na sessão; viola feedback-loop |
| Ignorar mobile na análise de LP | Maioria do tráfego é mobile; padrão incompleto |

---

## EROS VEREDITO (preencher ao entregar)
```
Completude:  [ok/falhou] — todos os eixos relevantes ao input cobertos?
Precisão:    [ok/falhou] — hex/escala/estrutura concretos, inferências com confidence?
Qualidade:   [ok/falhou] — padrões realmente reutilizáveis, não genéricos?
Coerência:   [ok/falhou] — plano de aplicação conecta com nossos projetos?
Utilidade:   [ok/falhou] — equipe consegue aplicar sem retrabalho?
Score: X/5 | AUTORIZADO / CONDICIONAL / BLOQUEADO
```
