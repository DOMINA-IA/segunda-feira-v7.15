---
name: slop-scan
description: "Detecta 'AI slop' — clichês visuais (gradiente violeta, system-ui, bordas bubbly), de código (catch vazio, nomes genéricos, any) e de copy (buzzwords PT/EN) — contra uma blacklist editável em ~/.claude/slop-blacklist.json. 100% determinístico, custo zero. Use antes de publicar uma landing page/criativo, ou com --diff para revisar só os achados novos de um commit."
axis: meta
harnesses:
  claude-code: full
  codex: full
  cursor: full
  aider: full
model-routing:
  primary: local  # 100% determinístico — regex sobre blacklist, sem LLM
---

# /slop-scan — Detector de AI Slop ($0)

## O que faz

Escaneia arquivos contra uma blacklist de padrões clichê de IA — visuais
(gradiente violeta, system-ui, bubbly radius), de código (catch vazio, nomes
genéricos, `any`) e de copy (buzzwords PT/EN, "nesse mundo cada vez mais").

A política vive em **dado editável** (`~/.claude/slop-blacklist.json`) — mudar o
que conta como slop é editar o JSON, não o código. Mesma filosofia da
`visual-rendering-safety.md`: "memória esquece, código não".

## Uso

```bash
python3 ~/.claude/skills/scripts/slop-scan.py <arquivo>        # um arquivo
python3 ~/.claude/skills/scripts/slop-scan.py <diretório>      # recursivo
python3 ~/.claude/skills/scripts/slop-scan.py --diff           # só git diff, só NEW
python3 ~/.claude/skills/scripts/slop-scan.py <alvo> --severity alto   # filtra
python3 ~/.claude/skills/scripts/slop-scan.py <alvo> --strict         # exit 1 se houver 'alto'
```

## Quando usar

| Contexto | Por quê |
|----------|---------|
| Antes de publicar landing page / criativo | pega clichê visual de IA antes do mercado ver |
| Copy de Instagram / ads (@content, @copywriter) | mata buzzword genérica (destrave, potencialize) |
| Review de código gerado por IA | catch vazio, `any`, nomes genéricos |
| Gate no `/ship` ou pre-commit | `--diff --strict` bloqueia slop novo |

## Saída

```
🔴 arquivo:linha [alto] id — descrição
🟡 ... [medio] ...
⚪ ... [baixo] ...
N achado(s): X alto, Y medio, Z baixo
```

## Manutenção (igual ao validador de acentos)

A cada slop que escapar em produção: adicionar o padrão em
`~/.claude/slop-blacklist.json` (categorias `design_slop`, `code_slop`,
`copy_slop`). Re-rodar para confirmar a detecção. É um dicionário vivo.

## Origem

Absorvido do `/slop-scan` do gstack v1.58.5.0 (Garry Tan), 26-Jun-2026.
Adaptado: blacklist com clichês em **português** (foco DOMINA.IA) além de inglês.
A página do mapa de absorção (`gstack-absorcao-site`) foi feita passando neste scan.
