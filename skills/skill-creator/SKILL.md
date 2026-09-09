---
name: skill-creator
description: "Cria novas skills reutilizáveis para Claude Code seguindo padrões AntiGravity e Segunda-feira. Use quando precisar criar, refatorar ou documentar uma skill modular."
tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
harnesses:
  - claude-code: full
  - codex: native
  - cursor: limited
  - aider: limited
---

# Skill Creator

Cria skills modulares e reutilizáveis seguindo o padrão AntiGravity + Segunda-feira.

## Processo (6 Etapas)

### 1. Understanding
Entenda o caso de uso concreto:
- Quais são 3 exemplos reais de uso desta skill?
- Qual o trigger natural? ("quando o usuário pede X")
- Qual o output esperado?

### 2. Planning
Defina os recursos reutilizáveis:
- Scripts executáveis necessários?
- Referências de documentação?
- Templates ou assets?

### 3. Initialize
Crie o arquivo da skill em `~/.claude/skills/`:
```markdown
---
name: nome-em-gerundio (max 64 chars, lowercase, hyphens)
description: "3ª pessoa, triggers específicos, max 1024 chars"
tools: [ferramentas necessárias]
---

# Título da Skill

[Instruções concisas — assuma que o agente é inteligente]
```

### 4. Edit & Implement
- SKILL.md < 500 linhas (progressive disclosure)
- Grau de liberdade adequado:
  - **Alta** (bullets): heurísticas
  - **Média** (templates): padrões preferenciais
  - **Baixa** (scripts): operações frágeis

### 5. Validate
- [ ] Nome em gerúndio, lowercase com hyphens?
- [ ] Description com triggers específicos?
- [ ] Tools listados corretamente?
- [ ] Instruções concisas (sem explicar o óbvio)?
- [ ] Forward slashes nos caminhos?
- [ ] < 500 linhas?

### 6. Register
Adicione à lista de skills disponíveis se necessário.

### 7. Auditoria
Antes de finalizar, audite frontmatter e ferramentas com este checklist (absorvido de skill-builder.md, adaptado ao schema canônico Segunda-feira):

**Frontmatter**
- [ ] `name` corresponde ao nome do arquivo (sem `.md`), lowercase-com-hifens?
- [ ] `description` usa palavras-chave que o usuário realmente diria e segue o formato `"Faz X — Use quando Y. NOT for: Z"` (o "NOT for" evita falso-positivo com skills vizinhas)?
- [ ] `user-invocable: true` está setado se a skill pode ser chamada via `/nome`?
- [ ] `allowed-tools` é uma lista YAML (não array inline) e restringe apenas às ferramentas realmente necessárias?
- [ ] `harnesses` declarado se a skill precisa rodar fora do Claude Code (`claude-code: full`, `codex: native/limited`, `cursor: full/limited`, `aider: full/limited`)?
- [ ] `axis: meta` ou `axis: ops` declarado conforme o artefato produzido (sistema vs mercado)?
- [ ] `context_fork: true` setado se a skill é autocontida e produz output verboso?
- [ ] `model-routing` setado apenas se a skill precisa de modelos diferentes por etapa?
- [ ] `disable-model-invocation: true` setado se a skill tem efeitos colaterais (custo, escrita externa) e não deve ser auto-invocada pelo modelo?
- [ ] Nenhum campo desnecessário setado (menos é mais)?

**Conteúdo**
- [ ] Arquivo da skill com menos de 500 linhas?
- [ ] Fluxo passo a passo numerado e específico, sem instrução vaga?
- [ ] Formato de saída especificado (templates, caminhos, exemplos)?
- [ ] Caminhos de arquivo documentados (entrada, saída, scripts, referências)?
- [ ] Seção de notas cobre edge cases e o que NÃO fazer?

**Integração**
- [ ] Chaves de API (se houver) em variável de ambiente, nunca hardcoded?
- [ ] Arquivos de apoio referenciados a partir do arquivo principal, não órfãos?
- [ ] Skill documentada onde for relevante (CLAUDE.md ou glossário do framework)?

## Regras
- Skills são **genéricos e reutilizáveis** — NUNCA atrelados a campanhas/produtos específicos
- Use caminhos com `/` (nunca `\`)
- Padrão Plan-Validate-Execute em loops de validação
- Metadata (name + description) deve ser suficiente para decidir se ativar a skill
