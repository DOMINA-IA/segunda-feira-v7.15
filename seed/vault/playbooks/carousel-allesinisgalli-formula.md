---
type: playbook
domain: content
agents:
- content
- creative-director
- copywriter
tags:
- instagram
- carrossel
- design-system
- mcp
- claude
- b2b-tech
source_url: https://www.instagram.com/p/${POST_ID}/
reference_images: ~/cortex/vault/references/carousel-CLIENTE_EXEMPLO-mcp/
verified_at: 2026-05-11
links:
- target: CLIENTE_EXEMPLO-identidade-visual
  type: auto-linked
- target: catalogo-modelos-instagram
  type: auto-linked
- target: video-editing
  type: auto-linked
- target: design-system-lp-f1
  type: auto-linked
axis: ops
status: active
---

# Fórmula Carrossel — @CLIENTE_EXEMPLO (MCP Meta x Claude)

Carrossel educacional B2B-tech, 6 slides, ~estrutura "Capa → 3 Passos → Contraponto → CTA".
Adotado como modelo visual de referência para próximas demandas DOMINA.IA (decisão CEO 11-Mai-2026).

---

## 1. Formato técnico

| Item | Valor |
|------|-------|
| Proporção | 4:5 (vertical premium) |
| Resolução | 1122 x 1402px |
| N de slides | 6 (sweet spot Instagram: 5-8) |
| Peso médio | ~250KB/slide |
| Indicador slide N/6 | Pill outline azul canto superior direito |

## 2. Sistema cromático

**Paleta principal**
- `#0F1F8E` Azul royal/Claude (CTA, hooks de destaque, ícones, pills)
- `#FF6F36` Laranja-ferrugem Claude (sparkle/asterisco, glows, accents)
- `#0A1A4A` Azul-marinho profundo (background capa + CTA)
- `#F5F2EA` Off-white/creme (background slides de conteúdo)
- `#0F0F12` Preto absoluto (tipografia hook)

**Regra de uso**
| Slide | BG | Hook color | Accent |
|-------|----|-----------|---------|
| 1 (capa) | azul-marinho profundo | branco | glows laranja+ciano nos cantos |
| 2-4 (conteúdo) | creme | preto+azul royal (alternados) | sparkle laranja canto inferior |
| 5 (contraponto) | creme | preto+azul royal | aspas laranja+azul + sparkle |
| 6 (CTA) | azul-marinho profundo | branco | glows orbitais laranja+ciano |

Capa e CTA formam **"sandwich cromático"** — abrem e fecham no mesmo registro visual escuro/3D, criando senso de unidade.

## 3. Sistema tipográfico (3 famílias)

| Função | Tipo | Estilo | Tamanho relativo |
|--------|------|--------|------------------|
| **Display/Hook** | Sans condensada bold (Bebas Neue, Anton ou Druk Wide) | UPPERCASE, peso 900 | 90-130pt |
| **Sublabel/citações** | Serif italic (Playfair Display ou Domine Italic) | itálico | 24-32pt |
| **Corpo/listas** | Sans humanista (Inter, Manrope) | regular/medium | 16-22pt |
| **Mockup interno** | Mono (Roboto Mono ou IBM Plex Mono) | regular | 12-14pt |

**Bicromia no hook**: o título é dividido em 2-3 partes — primeira metade preta + segunda metade azul royal. Cria **leitura em pulso visual** (preto = setup, azul = punchline).

## 4. Módulos reutilizáveis (componentes do design system)

### A. Header de passo
```
passo N.       ← serif fina, número em color azul royal bold
[ pill outline | label italic descritivo ]
```

### B. Contador slide
```
( N/6 )   ← pill outline azul, canto superior direito, fixo em todos slides
```

### C. Hook bicromático
```
[METADE 1 EM PRETO]
[METADE 2 EM AZUL ROYAL]   ← display sans condensada uppercase
```

### D. Card mockup escuro (lado direito)
- Fundo: preto absoluto (`#0F0F12`)
- Header: ícone Meta + título "Meta Marketing API (MCP Server)" + ícone Meta direita
- Body: lista de tools com ícone linear branco + nome em mono + descrição em sans cinza claro
- Footer: badge verde `✓ CONECTADO` com sublabel "Claude + Meta MCP"
- **Sempre presente em slides técnicos** — sustenta credibilidade "isto é real"

### E. Lista de bullets numerada
- Número grande azul royal (Display, 40-48pt) à esquerda
- Texto em sans humanista preto + key terms em azul royal bold
- Separadores: linha fina horizontal cinza claro

### F. Card item (slide 5)
- Container creme com sombra suave
- Círculo azul claro com ícone linear azul royal à esquerda
- Linha vertical fina separadora
- Título uppercase azul royal + descrição sans humanista preto

### G. Citação/quote
- Container outline azul royal
- 2 aspas grandes coloridas (1 azul + 1 laranja)
- Texto em italic serif
- Sparkle laranja Claude no final como assinatura

### H. Rodapé
```
[ pill outline | @handle ]   ← centralizado, sempre presente
sparkle laranja canto inferior esquerdo + linha curva orbital
```

### I. Glow rays (capa/CTA)
- Raio laranja saindo do canto inferior esquerdo
- Raio azul ciano saindo do canto inferior direito
- Curvatura orbital fina conectando os dois — sensação de "portal/futuro"

## 5. Estrutura narrativa (3-act)

| Slide | Ato | Função | Padrão |
|-------|-----|--------|--------|
| 1 | Hook | Curiosity gap | Visual 3D antropomorfizado (Meta+Claude se beijando) + título bicromático |
| 2 | Setup/contexto | Quebra de objeção | "Não era X, era Y" — invalida o vilão antigo |
| 3 | Tutorial | Como fazer | 4 passos numerados + screenshot do produto |
| 4 | Prova | Demonstração | "Eu fiz X em Y segundos" + lista de capacidades |
| 5 | Honestidade | Contraponto | "Mas aqui está o porém" — limites + minha leitura |
| 6 | CTA | Conversão | "Comente PALAVRA-CHAVE" |

**Padrão de copy do hook por slide:**
- Slide 1: TEMA × TEMA (relação inesperada)
- Slide 2: NEGAÇÃO. AFIRMAÇÃO. (quebra de premissa)
- Slide 3: DO X AO Y EM Z (transformação concreta)
- Slide 4: 3 FRASES CURTAS. PONTO. PONTO. PONTO. (ritmo staccato)
- Slide 5: MAS AQUI ESTÁ O PORÉM (vulnerabilidade calculada)
- Slide 6: COMENTE "PALAVRA" (gatilho automação)

## 6. Mecânica de conversão

| Elemento | Por quê |
|----------|---------|
| CTA via comentário (não DM/link) | Algoritmo Meta favorece comentários; automação ${USER}/InstAuto envia conteúdo via DM após comentário detectado |
| Palavra-chave 3 letras ("MCP") | Fricção zero em mobile, evita typo |
| "Faz menos de 24h. Dá tempo ao tempo" no slide 5 | Cria urgência sem hype + posiciona o autor como early-adopter cuidadoso |
| Antropomorfismo na capa | Stop scroll guaranteed — 3D render personificado é pattern interrupt em feed de fotos/selfies |

## 7. Adaptação para DOMINA.IA

Quando reutilizar essa fórmula:

| Substituir | Por |
|-----------|-----|
| Azul royal/Claude (#0F1F8E) | Azul DOMINA.IA (validar com brand guide) |
| Laranja-ferrugem Claude | Cor secundária DOMINA (manter contraste alto) |
| Asterisco/sparkle Claude | Assinatura visual DOMINA (logo mark, símbolo IA) |
| Antropomorfismo Meta+Claude | Antropomorfismo "Empresário+IA" (3D render gerado por gpt-image-2/Flux) |
| Card mockup MCP escuro | Card mockup CLIENTE_EXEMPLO / WhatsApp Bot escuro |
| Italic serif (Playfair) | Manter — adiciona "premium editorial" ao tom B2B-tech |

**Não copiar**: handle, paleta azul/laranja exata, asterisco Claude. Manter: estrutura narrativa, sistema modular, hook bicromático, sandwich cromático capa+CTA.

## 8. Validação visual (regra `visual-rendering-safety.md`)

Todos os slides desse modelo passam:
- ✅ Acentos PT-BR corretos em todas as palavras (`não`, `automação`, `instáveis`, `porém`)
- ✅ Zero emoji renderizado por glifo (apenas ✓ em verde, dentro de badge)
- ✅ Ícones lineares desenhados (lock, wrench, globe), não font icons
- ✅ Sparkle laranja é shape vetorial, não emoji

## Links relacionados

- [[playbook-reels-instagram]] — Reels (formato vídeo)
- [[playbook-criativos-meta-ads]] — Story 9:16 ads
- [[feedback-sem-nome-agente-posts]] — Nomenclatura B2B (sem persona-mascote)
- [[visual-rendering-safety]] — Regras de rendering

## Referências visuais arquivadas

`~/cortex/vault/references/carousel-CLIENTE_EXEMPLO-mcp/slide-01.jpg ... slide-06.jpg`
