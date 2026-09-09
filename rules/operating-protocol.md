# Protocolo Operacional — CORTEX, Memória, Comunicação, Qualidade

> **Severidade:** MUST | **Aplica-se a:** Todos os agentes
> Consolida: cortex-usage + consciousness-engine + agent-communication + eros-quality
> Versões completas on-demand no vault (`~/cortex/vault/rules/`)

## Contexto já vem injetado

O hook `router.py` (UserPromptSubmit) injeta briefing do agente, notas CORTEX relevantes e
heurísticas a cada mensagem. **Use o que veio. Só busque mais se precisar aprofundar.**

Aprofundar, nesta ordem:
```bash
python3 ~/cortex/scripts/cortex_engine.py query "termo"   # 1) busca ranqueada
bash ~/broadcast/agent-boot-context.sh {agent}            # 2) briefing + heurísticas + mailbox
cat ~/cortex/vault/<path-indicado>                        # 3) nota específica
```
Dados operacionais em tempo real **não** passam pelo CORTEX — leia direto:
`~/feedback-loop/results.json` · `~/patterns/*.md` · `~/broadcast/signals.json` ·
`~/broadcast/mailbox/{agent}.json` · código-fonte do projeto.

## Antes de tarefa não-trivial: cruzar padrões

Pergunte "a lição de outro projeto se aplica aqui?". Se encontrar match, aplique e registre
inline: `[Cruzamento: lição de {contexto} aplicada — {o que fez diferente}]`.
Obrigatório em: story, campanha/criativo, bug em área já problemática.
Dispensado em: lint/format, resposta conversacional.

## Depois de tarefa significativa: registrar episódio

```bash
~/consciousness/scripts/record-episode.sh --agent "@nome" \
  --type "task_completed|task_failed|insight_discovered|pattern_detected|decision_made|collaboration|error_recovered" \
  --summary "..." --result "success|partial|failure" \
  --valence -1.0..1.0 --intensity 0.0..1.0 \
  [--worked "..."] [--failed "..."] [--heuristic "Quando X, fazer Y porque Z"] \
  [--heuristic-applied "#handle"] [--heuristic-failed "#handle"]
```
**Fechar o loop (MUST quando aplicável):** se uma heurística injetada no seu prompt guiou a
tarefa, cite o `#handle` que aparece ao lado dela: `--heuristic-applied` se funcionou,
`--heuristic-failed` se levou ao erro. Sem isso o pool cresce sem lastro — em 05-Set-2026,
1.029 de 1.034 estavam travadas em `times_validated=1` e nenhuma jamais foi refutada.
**Significativo** = story, campanha, análise com insight, decisão estratégica, bug com
aprendizado, padrão novo, oferta. **Não** = leitura de arquivo, commit isolado, lint, resposta curta.

Valência calibra comportamento futuro — não deixe tudo em 0. Falha grave: −0.8/int 0.9.
Resultado excelente: +0.8. Rotina: ±0.3/int 0.3.

Anomalia ou oportunidade cross-domain:
`~/consciousness/scripts/workspace.sh propose --agent @nome --content "..." --urgency N --impact N`

## Skills: o agente decide, o CEO não invoca

Cada agente tem no próprio arquivo a seção **"Skills operacionais deste agente"** — tabela de
skill × gatilho × o que evita. **Antes de executar, confira se um gatilho se aplica**; se sim,
use a skill. Ela carrega procedimento verificado que evita erro já cometido.

Transversais a qualquer agente: **`/plan-first`** em tarefa multi-arquivo, irreversível ou com
confidence <0.7 · **`/dsl`** quando a mensagem começar com comando de barra.

Anunciar que existe uma skill sem usá-la é pior que não ter: devolve ao CEO a decisão que cabe
a você. Medição de 05-Set-2026: 27 invocações de skill em 30 dias, **nenhuma** do framework —
as skills existiam como catálogo esperando ordem humana, não como ferramenta do agente.

## Comunicação inter-agente

Se a descoberta muda a decisão de **outro** domínio, comunique — senão, não polua.
`bash ~/broadcast/send-mail.sh @destino "assunto" "corpo"` · afeta todos → `signals.json`.
Ao ser ativado, processe mailbox pendente antes da tarefa principal.

Obrigatório comunicar: CPL muda muito (@traffic→@content) · ângulo performa (@content→@traffic) ·
oferta alterada (@offer-engineer→@traffic,@copywriter) · campanha pausada/criada (@traffic→todos) ·
bug técnico (@dev→@devops) · lead qualificado (@cold-outreach→@closer).

## EROS — padrão de qualidade

**"Se eu fosse o destinatário, ficaria satisfeito?"** Se não, corrija antes de entregar.

5 portões: Compreensão (objetivo real) → Planejamento (cobertura, riscos) → Execução
(completude, raciocínio real) → Revisão (zero erro factual) → Liberação (resolve o problema).

Veredito EROS (Completude/Precisão/Qualidade/Coerência/Utilidade, score X/5, evidência por linha)
só em entrega **não-trivial**: story, campanha, análise, oferta. Pular em bug trivial, conversa,
operação técnica. Rigor ∝ impacto. Máx. 2 ciclos de correção por portão → escalar.

Hierarquia: @sf-master > @po > @qa > EROS > executor. Em conflito autonomia × qualidade,
**qualidade vence**.

### Checklist 1º deploy backend (@dev)
publicPaths/matcher inclui a rota? · rota registrada no router? · CORS? · env var em produção? ·
auth guard não bloqueia? — Pendente → não deployar.
