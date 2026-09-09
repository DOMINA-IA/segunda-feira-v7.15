---
name: autodream
description: "Consolida a sessão atual sob demanda — varre trabalho criado/editado, extrai heurísticas e gera um dream digest (one-shot manual, escopo de sessão atual). Use quando terminar uma sessão produtiva, antes de trocar de contexto/projeto, ou após um plano complexo (auditoria+fixes+deploy). NOT for: sessões curtas com 1-2 edits triviais ou logo após o consolidate.sh do cron noturno (redundante, escopo 24h automático)."
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# /autodream — Skill de Sono e Assimilação

> **Conceito:** o agente "dorme" sobre o trabalho recente, assimila padrões, consolida memórias e entrega um relatório do que aprendeu enquanto sonhava.
>
> **Diferente de `consolidate.sh`:** aquele roda 23:30 BRT automático, escopo 24h, escala completa. `autodream` é **sob demanda, escopo de sessão atual, mais cirúrgico**.

## Quando usar

Invocar `/autodream` quando:

- Fim de sessão produtiva (vários sprints, muitos commits/edits) e quer fechar limpo
- Antes de mudar de contexto/projeto — pra não perder aprendizados da sessão anterior
- Após executar um plano complexo (auditoria + fixes + deploy) — consolida o que ficou solto
- "Antes de dormir" — deixar a memória organizada pra próxima sessão acordar com contexto

**NÃO usar:**
- Sessão curta com 1-2 edits triviais (não há o que assimilar)
- Trabalho em andamento ainda — espere terminar antes de consolidar
- Logo após `consolidate.sh` do cron noturno (redundante)

## Subcomandos

| Subcomando | O que faz |
|-----------|-----------|
| `/autodream` | Execução completa: coleta → análise → consolidação → digest |
| `/autodream dry` | Dry-run — mostra o que faria sem aplicar (revisão antes do --apply) |
| `/autodream digest` | Lê o último dream digest gerado (`~/.claude/projects/<proj>/dreams/`) |
| `/autodream prune` | Limpa memórias duplicadas/obsoletas detectadas em runs anteriores (requer confirmação humana) |

## Pipeline padrão (4 fases · timeout 5min)

### Fase 1 — Coleta (matéria-prima do sonho)

Identifica TUDO que mudou nesta sessão:

```bash
SESSION_START="${SESSION_START:-$(date -u -v-4H -Iseconds)}"  # padrão: últimas 4h
DREAM_DIR="$HOME/.claude/projects/$(basename $(pwd))/dreams"
mkdir -p "$DREAM_DIR"

# 1.1 Arquivos editados na sessão (se em git repo)
if [ -d .git ]; then
  echo "=== Git working tree ===" > /tmp/autodream-raw.md
  git status --short >> /tmp/autodream-raw.md
  echo "" >> /tmp/autodream-raw.md
  git log --since="$SESSION_START" --oneline >> /tmp/autodream-raw.md
fi

# 1.2 Episódios novos no Consciousness Engine
echo "=== Episódios desde $SESSION_START ===" >> /tmp/autodream-raw.md
for f in ~/consciousness/memory/episodic/*.jsonl; do
  agent=$(basename "$f" .jsonl)
  count=$(awk -F'"ts":"' -v cutoff="$SESSION_START" '$2 >= cutoff' "$f" | wc -l)
  [ "$count" -gt 0 ] && echo "@${agent}: $count episódios novos" >> /tmp/autodream-raw.md
done

# 1.3 Tasks concluídas/criadas (via TaskList — colocar no contexto manual)

# 1.4 Mailboxes modificadas nas últimas 4h
echo "=== Mailbox activity ===" >> /tmp/autodream-raw.md
find ~/broadcast/mailbox -name "*.json" -mmin -240 -exec basename {} .json \; >> /tmp/autodream-raw.md

# 1.5 CORTEX vault notes editadas
echo "=== CORTEX notes editadas ===" >> /tmp/autodream-raw.md
find ~/cortex/vault -name "*.md" -mmin -240 -type f 2>/dev/null | head -20 >> /tmp/autodream-raw.md

cat /tmp/autodream-raw.md
```

### Fase 2 — Análise (durante o sonho)

Identificar:

- **Padrões repetidos** — algo apareceu 3+ vezes na sessão? candidato a heurística.
- **Erros + recuperações** — algo deu errado e foi resolvido? heurística com **valência negativa** (peso -, intensidade alta).
- **Decisões sem doc** — algo importante decidido em conversa mas não documentado em CORTEX/MEMORY/CHANGELOG.
- **Conflitos entre memórias** — uma feedback memory contradiz outra? marcar pra revisão.
- **Estimativas vs real** — algo demorou muito menos/mais que estimado? calibrar.
- **Heurísticas duplicadas** — comparar novas com `~/consciousness/memory/procedural/heuristics.jsonl` por similarity de conteúdo.

Output desta fase: lista estruturada em memória do agente (não escrever ainda).

### Fase 3 — Consolidação (assimilação)

Aplicar mudanças. **NUNCA deletar memórias sem `/autodream prune` explícito.**

```bash
# 3.1 Registrar heurísticas novas (1 por insight)
~/consciousness/scripts/record-episode.sh \
  --agent "@AGENT" --type "insight_discovered" \
  --summary "Padrão observado N vezes nesta sessão" \
  --result "success" --valence X.X --intensity Y.Y \
  --heuristic "QUANDO X, FAZER Y, PORQUE Z"

# 3.2 Criar notas CORTEX pra decisões sem doc
~/cortex/scripts/ingest.sh --title "Decisão XYZ" \
  --type project --domain DOMÍNIO --agents AGENTS \
  --tags TAGS

# 3.3 Atualizar MEMORY.md se houver memória nova de usuário (preferência forte, feedback novo)
# (editar manualmente via Edit tool — não sobrescrever)

# 3.4 Rebuild briefings se ≥3 episódios novos pra algum agente
python3 ~/cortex/scripts/cortex_engine.py build-briefings

# 3.5 Registrar o próprio autodream como episódio
~/consciousness/scripts/record-episode.sh \
  --agent "@claude" --type "task_completed" \
  --summary "Autodream session - assimilou N heurísticas, M notas CORTEX, K conflitos detectados" \
  --result "success" --valence 0.5 --intensity 0.4
```

### Fase 4 — Dream digest (relatório acordado)

Escrever `$DREAM_DIR/$(date -u -Iminutes).md`:

```markdown
# Dream Digest · YYYY-MM-DD HH:MM UTC

## O que assimilei
- N heurísticas novas (lista com sumário de cada)
- M notas CORTEX criadas/atualizadas
- K decisões documentadas pela primeira vez

## Conflitos detectados (precisam de você decidir)
- [conflito]: memory A diz X, memory B diz Y. Recomendação: ...

## Padrões observados
- [padrão repetido N vezes]: ... → heurística candidata: ...

## Sugestões pra próxima sessão
- Continuar: ... (frequência observada: ...)
- Evitar: ... (registrado como negative valence)

## Estado da memória pós-autodream
- Heurísticas totais: N
- Notas CORTEX: N
- Episódios processados: N
- Memórias flat: N

## Stats da execução
- Wall-clock: Xs (limite 300s)
- Arquivos lidos: N
- Conflitos não resolvidos: N
```

Apresentar resumo do digest ao usuário (≤150 palavras) e link pro arquivo completo.

## Constraints de segurança

| Regra | Por quê |
|-------|---------|
| **NÃO deletar memórias** sem `/autodream prune` explícito | Autonomia controlada — deletar é irreversível |
| **NÃO criar feedback memory** com judgement negativo sobre o usuário | Memory de feedback deve ser sobre o trabalho, não juízo |
| **Dedup por nome+hash** antes de criar heurística | Senão polui rapidamente |
| **Timeout hard 5min** | Senão vira maratona noturna que trava a sessão |
| **Logar como episódio "consolidation"** | Rastreabilidade — todo autodream fica registrado |
| **Branchear `[[link]]`** pra notas relacionadas mesmo que não existam | Marca trabalho futuro sem quebrar |

## Diferenças vs outros mecanismos do framework

| Mecanismo | Quando roda | Escopo | Quem chama |
|-----------|-------------|--------|------------|
| `consolidate.sh` cron | 23:30 BRT diário | 24h passadas | Sistema |
| `auto-link-orphans` cron | 23:33 BRT diário | CORTEX vault inteiro | Sistema |
| `build-briefings` cron | 23:35 BRT diário | Todos os agentes | Sistema |
| `/consciousness reflect` | Sob demanda | 1 agente, 7 dias | Usuário |
| **`/autodream`** | **Sob demanda** | **Sessão atual** | **Usuário** |

`autodream` complementa, não substitui. É a peça que estava faltando entre "evento individual" (record-episode) e "consolidação massiva" (cron noturno).

## Anti-patterns

| Evitar | Por quê |
|--------|---------|
| Rodar `/autodream` no meio do trabalho | Consolidar inacabado vira heurística errada |
| Criar 10 heurísticas por sessão | Sinaliza ruído — qualidade > quantidade |
| Ignorar conflitos detectados | Conflito não resolvido vira problema crônico |
| Pular a fase de análise (Fase 2) | Aplicação cega = poluição de memória |
| Usar autodream pra debugar projeto | Skill é meta, não operacional |

## Integração com outras rules

| Rule | Como interage |
|------|---------------|
| `consciousness-engine.md` | Fonte primária de episódios para assimilação |
| `cortex-usage.md` | Destino primário das notas geradas; seção Cruzamento Obrigatório cobre padrões cruzados entre projetos detectados aqui |
| `evolution-scorecard.md` | Métricas do autodream alimentam o scorecard |

---

*Skill criada 2026-05-13 sob inspiração do CEO ${CEO_NAME}. Conceito: "skill que dorme e assimila tudo que criou."*
