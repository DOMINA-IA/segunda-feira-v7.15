---
id: visual-rendering-safety
title: Visual Rendering Safety — Regra Bloqueante para Geração de Conteúdo Visual
type: rule
domain:
- ops
triggers:
- png
- imagem
- criativo
- carrossel
- reel
- pillow
- render
- instagram
- glifo
- acento
- legenda
- post
- thumbnail
- copy
- conteúdo
- conteudo
- material
- anúncio
- anuncio
- arte
- stories
- story
- landing
- lp
- email
- blog
- site
- banner
- texto
- domina
- feed
- design
links:
- target: axis-separation-full
  type: auto-linked
- target: cross-collaboration-mandate
  type: auto-linked
- target: rules-instagram-posts
  type: auto-linked
---

# Visual Rendering Safety — Regra Bloqueante para Geração de Conteúdo Visual

> **Severidade:** MUST | **Aplica-se a:** @content, @copywriter, @creative-director, e qualquer agente que gere PNG/JPG renderizado para Instagram/Meta Ads
> **Origem:** 4 incidentes consecutivos de acentuação + 1 incidente Unicode + 1 incidente nomenclatura (sessão DOMINA.IA newsroom 09-Mai-2026)

## Princípio

Erros recorrentes em rendering visual (acentuação, glifos faltantes, nomes proibidos) são bloqueados **por código**, não por disciplina humana ou memória de agente. Se uma regra falhou 3+ vezes, vira **build gate**.

**Regra de ouro:** "Memória esquece. Código não."

---

## 3 Camadas de Defesa Obrigatórias

### Camada 1 — Pre-flight de Acentuação (BLOQUEANTE)

Todo script Python que renderiza PNG via Pillow DEVE começar com:

```python
import subprocess, sys
r = subprocess.run(
    ["python3", "$HOME/cortex/scripts/validate-pt-accents.py", __file__],
    capture_output=True, text=True
)
if r.returncode != 0:
    print(r.stdout, file=sys.stderr)
    print("\nBLOQUEADO: corrija acentos antes de renderizar.", file=sys.stderr)
    sys.exit(1)
```

Sem isso, o script NÃO RODA. Validador detecta:
- ~120 palavras PT-BR conhecidas sem acento (você, não, ações, automação, gestão, começar, etc.)
- 19 caracteres Unicode complexos que fontes não renderizam (☒ ⚠ 🔒 📊 emojis bandeira, etc.)

Localização do validador: `~/cortex/scripts/validate-pt-accents.py`
Manutenção: adicionar palavras novas ao dict `WORDS_FORBIDDEN` quando aparecerem em produção.

### Camada 2 — Glifos Seguros por Fonte

Use APENAS caracteres que a fonte renderiza. Tabela de compatibilidade:

| Categoria | Bebas Neue | Montserrat | Georgia |
|-----------|-----------|------------|---------|
| ASCII A-Z, 0-9 | ✓ | ✓ | ✓ |
| Acentos PT-BR (á à â ã é ê í ó ô õ ú ç) | ✓ | ✓ | ✓ |
| Pontuação básica (. , ; : ? !) | ✓ | ✓ | ✓ |
| Setas → ← | ✗ (vira X) | ✓ | ✓ |
| Box drawing (─ ━ ┃) | ✗ | ✗ | ✗ |
| Emojis (🚀 ⚡ 📊) | ✗ | ✗ | ✗ |
| Bandeiras (🇺🇸 🇧🇷) | ✗ | ✗ | ✗ |

**Substitutos ASCII universais:** `>` `<` `|` `+` `-` `=` `*` `#` `@`

**Para desenhar separadores/setas:** usar `draw.line()` ou `draw.polygon()` em vez de glifos.

### Camada 3 — Auditoria Visual Pós-Render

Após cada `Image.save()`, abrir o PNG e verificar pixel-a-pixel:

```python
from PIL import Image
img = Image.open(saved_path)
# Procurar zonas suspeitas: blocos pretos vazios em áreas de texto = placeholder
# Se detectado → glifo falhou; substituir por equivalente ASCII e regenerar
```

Capas críticas (slide 1 de carrossel, capa de Reel) DEVEM passar por auditoria humana antes de upload.

---

## Nomenclatura de Agentes (Regra Adicional)

Em conteúdo de marketing DOMINA.IA, agentes IA aparecem APENAS por função:

- ✅ "AGENTE DE TRÁFEGO", "AGENTE DE FOLLOW-UP", "AGENTE COMERCIAL"
- ✅ "OS 3 SISTEMAS", "AS 4 AÇÕES AUTÔNOMAS"
- ❌ "Sobral", "Atlas", "Aurora", "Íris" — qualquer nome próprio

Razão: posicionamento "ferramenta > prompt" = sistema corporativo B2B, não persona-coach com mascote.

---

## Camada 4 — Anti-Slop de Design e Copy (slop-scan, absorvido do gstack 26-Jun-2026)

As Camadas 1-3 atacam erro técnico (acento, glifo). A Camada 4 ataca **falta de gosto** — os clichês visuais e de copy que denunciam "feito por IA": gradiente violeta/indigo, `system-ui` como fonte primária, border-radius bubbly, buzzword genérica (destrave, potencialize, "nesse mundo cada vez mais"), emoji em excesso.

A política é **dado editável** (`~/.claude/slop-blacklist.json`), não código — mesma filosofia desta rule. Rodar antes de publicar qualquer visual ou copy:

```bash
python3 ~/.claude/skills/scripts/slop-scan.py <arquivo|dir>     # relatório
python3 ~/.claude/skills/scripts/slop-scan.py --diff --strict   # gate: exit 1 se slop 'alto'
```

Skill: `/slop-scan`. A cada slop que escapar em produção, adicionar o padrão à blacklist (igual ao `WORDS_FORBIDDEN` da Camada 1).

## Hierarquia de Aplicação

| Contexto | Regra aplicada |
|----------|---------------|
| Geração de PNG via Pillow | Camadas 1, 2, 3 + Nomenclatura |
| Geração de copy/legenda (texto) | Camada 1 + 4 + Nomenclatura |
| Geração de prompt para image2 (gpt-image-2) | Camada 1 (no script Python) — image2 não usa fonte local |
| Conteúdo de email/blog/site | Camadas 1 + 4 + Nomenclatura |
| Landing page / HTML / criativo web | Camada 4 (slop-scan) antes de publicar |

---

## Anti-Patterns

| Evitar | Por quê |
|--------|---------|
| "Vou lembrar de colocar acento" | Memória falha sob pressão. Use validador. |
| "Esse emoji vai funcionar" | Sem testar fonte específica = quadrado X em produção |
| "Vou dar nome humano para a IA" (Aurora, Íris) | Quebra posicionamento corporativo + risco de colisão com criadores existentes |
| "Auditoria visual da thumbnail" | Thumbnail mascara typos pequenos. Auditar pixel-a-pixel em alta resolução. |
| "Substitution regex no PNG renderizado" | Render é destrutivo — substituir antes de renderizar. |

---

## Integração com Outras Regras

| Regra relacionada | Como interage |
|-------------------|---------------|
| `eros-quality.md` | Portão 5 (Liberação) inclui validação visual via este pipeline |
| `agent-authority.md` | @content é o executor padrão; @creative-director audita |
| `feedback-loop.md` | Falhas em produção alimentam o `WORDS_FORBIDDEN` do validador |
| `consciousness-engine.md` | Cada falha vira heurística e atualiza dicionário |

---

## Manutenção

A cada falha visual em produção:
1. Adicionar palavra/glifo ofensor ao validador
2. Re-rodar validador para confirmar detecção
3. Registrar episódio no Consciousness Engine com heurística específica
4. Atualizar esta regra se for padrão novo (não apenas palavra nova)
