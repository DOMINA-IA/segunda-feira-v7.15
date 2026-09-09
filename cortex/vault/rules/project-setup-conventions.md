---
id: project-setup-conventions
title: Project Setup — Convenções para Criar Projetos com Perfeição
type: rule
domain:
- meta
triggers:
- novo projeto
- criar projeto
- iniciar projeto
- começar projeto
- comecar projeto
- setup do projeto
- estruturar projeto
- scaffold
- montar o projeto
- criar sistema
- construir sistema
- iniciar app
links:
- target: token-economy
  type: auto-linked
- target: claude-opus-4-7-launch-2026-04
  type: auto-linked
- target: eros-quality-full
  type: auto-linked
---

# Project Setup — Convenções para Criar Projetos com Perfeição

> Severidade: SHOULD | Complementa o SDC (`~/.sf-core/development/workflows/`). Origem: lições do Encontro INEMA + constituição SF.

**Regra de ouro:** "Planejar antes de codar. MVP antes de floreio. Estrutura antes de escala."

## 1. Antes da primeira linha (planejamento domina)
- Definir **usuário**, **problema**, **como resolve**, **MVP** (o mínimo vendável/útil).
- Listar V1/V2/V3 no início; entregar V1, evoluir. "Não existe produto final, existe produto em evolução."
- Peça o **plano** à IA e **aprove** antes de executar. Use modo plano (só leitura) para diagnóstico.

## 2. Estrutura e nomenclatura (a IA só acha "para baixo")
- Todo projeto sob `~/projetos/<nome>` ou `~/projetos/clientes/<cliente>/`.
- Nomes **minúsculos, sem acento, sem espaço, sem caractere especial**.
- Padrão de pastas consistente → a IA localiza sem varrer (economiza token). Ver `~/HOME.md (mapa) + ~/ARCHITECTURE.md (arquitetura)`.

## 3. Higiene técnica obrigatória
- `git init` + `.gitignore` desde o início; commits atômicos (conventional: feat/fix/docs/chore).
- Chaves **nunca no código** → `.env` (chmod 600) + `.env.example` como template. Ver rule `credentials-handling`.
- Primeiro deploy backend: checklist do EROS (publicPaths/rota/CORS/env var/auth guard).

## 4. Modelo por etapa (custo)
- Planejar/arquitetar = modelo forte; **executar/refatorar = Sonnet**; mecânico/extração = Haiku/Tier 0.
- Subagentes de um agente Opus rodam em Sonnet/Haiku. Ver rule `model-routing`.

## 5. Qualidade (EROS)
- Auto-checagem antes de entregar; Veredito EROS em entregas não-triviais.
- 45% do código de IA tem vulnerabilidade sem revisão → skill de revisão separada, chamada sob demanda.
- Nunca confiar cego no código gerado; testar; versionar.

## 6. Segurança ao delegar
- "Delegar ≠ repassar" — validar que a IA entendeu antes de soltar execução.
- Configurar confirmação antes de ações destrutivas (delete/overwrite/deploy). Nunca dar escrita a modelo desconhecido sem sandbox.

## Anti-patterns
| Evitar | Correção |
|--------|----------|
| Codar sem plano | 4h de 6h no planejamento |
| Nomes com acento/espaço | minúsculo, sem acento, sem espaço |
| Chave no código | `.env` + `.gitignore` |
| Opus para build mecânico | Sonnet (`/model sonnet`) |
| Escopo infinito na V1 | MVP + versionamento |
| Entregar sem revisar | auto-checagem + Veredito EROS |
