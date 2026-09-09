---
id: catalogo-modelos-instagram
title: catalogo-modelos-instagram
type: meta
domain:
- content
agents:
- content
tags:
- instagram
- modelos
- posts
- visual
status: active
created: '2026-04-12'
last_verified: '2026-04-12'
decay_rate: 0.01
links:
- target: carousel-CLIENTE_EXEMPLO-formula
  type: auto-linked
- target: design-system-lp-f1
  type: auto-linked
- target: rules-criativos
  type: auto-linked
- target: video-editing
  type: auto-linked
- target: rules-instagram-posts
  type: auto-linked
migrated_from: $HOME/.claude/projects/-HOME-/memory/catalogo-modelos-instagram.md
old_description: Catálogo completo dos 8 modelos visuais para posts Instagram DOMINA.IA
  — referência obrigatória para geração de conteúdo
axis: meta
---

Catálogo de modelos visuais aprovados pelo CEO. Toda geração de conteúdo DEVE variar entre estes modelos.

**How to apply:** Nunca mais de 2 posts seguidos com o mesmo modelo. Consultar este catálogo antes de gerar qualquer post.

---

## 8 MODELOS APROVADOS

### 1. MODELO D — White Clean
- **Script:** `carousel-template-d.py`
- **Fundo:** branco limpo
- **Header:** profile pic ${CEO_NAME} + "${CEO_NAME} @${CEO_INSTAGRAM}" top-left
- **Headline:** preta bold GRANDE (Georgia Bold)
- **Destaque:** ícone de app roxo centralizado
- **CTA:** "Salva pra não perder." em ROXO
- **Slides:** bullet points com ícones coloridos em fundo branco
- **Uso ideal:** listas, ferramentas, educativo
- **Exemplo:** "5 FERRAMENTAS DE IA QUE TODO EMPRESÁRIO PRECISA"
- **Instagram:** https://www.instagram.com/p/${POST_ID}/

### 2. MODELO E — Dark Teal
- **Script:** `carousel-template-e.py`
- **Fundo:** dark teal/navy gradiente
- **Header:** @${CEO_INSTAGRAM} + DOMINA.IA top-left
- **Headline:** bold grande, última linha em COR TEAL
- **Foto:** ${CEO_NAME} em círculo na parte inferior
- **Subtítulo:** cinza abaixo da headline
- **CTA:** "Salva. Aplica. Domina." em teal
- **Slides:** numerados com ícones teal + bullet points em fundo dark
- **Uso ideal:** automações, agentes, tech, provocação
- **Exemplo:** "5 AUTOMAÇÕES QUE FAZEM MEU NEGÓCIO RODAR SOZINHO"
- **Instagram:** https://www.instagram.com/p/${POST_ID}/

### 3. VARIAÇÃO A — Dark + Foto Stock
- **Script:** `generate-week.py` Var A
- **Fundo:** foto stock escurecida (blur + overlay 65% preto) OU tech grid
- **Header:** DOMINA.IA top-left em cinza
- **Headline:** bold branca, palavra-chave em VERMELHO ou VERDE
- **Dados:** vermelho para custo/problema, verde para solução
- **Uso ideal:** dados de mercado, urgência, comparações com números
- **Exemplo:** "R$ X.XXX/mês em funcionário vs R$100/mês em IA"

### 4. VARIAÇÃO B — Clean Dados
- **Script:** `generate-week.py` Var B
- **Fundo:** off-white/claro
- **Header:** DOMINA.IA top-left em cinza
- **Número fantasma:** "01" grande em cinza claro no top-right
- **Headline:** bold preta com dado numérico em destaque
- **Frase impacto:** em COR TEAL/VERDE
- **Uso ideal:** estatísticas, pesquisas, dados chocantes
- **Exemplo:** "78% das empresas não conseguem integrar IA."
- **Instagram:** https://www.instagram.com/p/${POST_ID}/

### 5. VARIAÇÃO C — Green Escuro
- **Script:** `generate-week.py` Var C
- **Fundo:** verde escuro (0, 45, 35) gradiente
- **Header:** DOMINA.IA top-left
- **Headline:** bold branca, última palavra em AMARELO/DOURADO
- **Uso ideal:** processos, automação, educativo com profundidade
- **Exemplo:** "5 Processos que todo empresário deveria automatizar."

### 6. NEWS DARK — Breaking News
- **Script:** `generate-week.py` Var A + cards
- **Fundo:** escuro gradiente
- **Badge:** "BREAKING NEWS" vermelho top-left + data
- **Header:** DOMINA.IA top-right
- **Headline:** bold branca com palavra destaque em VERMELHO
- **Cards:** escuros com ícones ROXOS à esquerda + título bold + descrição
- **Uso ideal:** notícias, vazamentos, dados urgentes de mercado
- **Exemplo:** "ANTHROPIC VAZA MODELO CLAUDE MYTHOS"
- **Instagram:** https://www.instagram.com/p/${POST_ID}/

### 7. NEWS GREEN — Notícia Verde
- **Script:** `generate-week.py` variante
- **Fundo:** verde escuro gradiente
- **Badge:** "NOTÍCIA DE ÚLTIMA HORA" amarelo/dourado
- **Headline:** bold branca com palavra em AMARELO
- **Uso ideal:** vazamentos, novidades do setor, notícias quentes
- **Exemplo:** "Vazou o código da principal IA do mercado."

### 8. EVENTO — Foto Background
- **Script:** `generate-week.py` variante
- **Fundo:** foto real de ambiente (escritório, evento) escurecida
- **Header:** DOMINA.IA top-left
- **Headline:** bold branca com nome do evento em TEAL
- **Data:** grande e destacada
- **Uso ideal:** eventos, desafios, datas importantes
- **Exemplo:** "Desafio AI FIRST — 14 a 19 de Abril de 2026."

---

## REGRA DE ROTAÇÃO

Para 7 posts na semana, exemplo de distribuição:
D → E → A → B → C → News → Evento

Nunca repetir o mesmo modelo em posts consecutivos no feed.