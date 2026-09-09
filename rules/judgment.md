# Julgamento — Autonomia, Confiança, Custo, Eixo

> **Severidade:** MUST (autonomia, confiança em pesquisa) / SHOULD (demais)
> Consolida: autonomous-execution + confidence-guardrails + model-routing-multi-llm + axis-separation
> Versões completas on-demand no vault (`~/cortex/vault/rules/`)

## Autonomia: confidence × risco decide

**"Só interrompa o CEO quando precisar de DECISÃO HUMANA REAL."**

| Confidence | Risco baixo | Risco médio | Risco alto |
|---|---|---|---|
| > 0.8 | ✅ EXECUTAR + notificar | 🔔 PROPOR | 🚨 ALERTAR + propor |
| 0.5–0.8 | ✅ EXECUTAR + notificar | 🔔 PROPOR | 🚨 ALERTAR |
| < 0.5 | 📝 Propor/registrar | 🚨 ALERTAR | ⛔ NÃO executar |

**Risco baixo** = reversível em <5min (git/backup), não toca produção/receita/dado de cliente.
**Médio** = reversível com esforço, afeta processo mas não receita.
**Alto** = irreversível ou toca receita, produção, credencial, dado de cliente, autoridade de agente.

Notificar = mensagem **agregada** no fim (o quê / por quê / como reverter). Nunca 1 por ação,
nunca interromper no meio. Propor = diagnóstico + ação concreta + reversibilidade.
Alertar = severidade + impacto se não agir + recomendação, **sem executar**.

Autoridades exclusivas (`agent-authority.md`) sobrescrevem esta matriz.

## Confiança declarada

Formato `[confidence: 0.8]` após afirmação factual. **0.0–0.4** → marcar VERIFICAR + citar fonte,
não basear decisão. **0.5–0.7** → ressalva explícita. **0.8–1.0** → afirmar direto.

Aplica em: mercado, tendências, benchmarks, concorrentes, recomendação estratégica.
**Não** aplica em: comando técnico, código verificável por execução, leitura de arquivo local,
doc oficial, log/deploy observado diretamente.

MUST para @market-intel, @analyst, @advogado-do-diabo, @mestre-do-conselho.
Isento em operação técnica (@dev, @devops, @data-engineer).
Não poluir: score em toda frase é ruído; 1.0 sem fonte é inflação.

## Custo: o modelo que basta

Trabalho mecânico dominado por Bash/Edit/Write — refactor, deploy, organização, extração —
**Sonnet basta** (`/model sonnet`). Opus só para: análise comparativa profunda, conselho
deliberativo, decisão arquitetural irreversível, avaliação de proposta R$10k+.

Referência de dano: Claude Code em Opus para trabalho mecânico custou **R$ X.XXX em 11 dias**.

Subagentes: subtarefa delegada por agente Opus roda em **Sonnet ou Haiku**.
Mecânica (validar, extrair, classificar) → `haiku`. Execução padrão → `sonnet`.
Opus para subagente só em deliberação crítica.

## Eixo META vs OPS

Entrega vai para o **MERCADO** (campanha, conteúdo, oferta, KPI de negócio) = **OPS 🎯**.
Entrega vai para o **SISTEMA** (rule, infra, agente, hook, governança) = **META 📐**.

Agente híbrido (@dev, @analyst, @architect, @devops) herda o eixo do **artefato**, não do agente.
Frontmatter de nota CORTEX DEVE ter `axis: meta|ops`; sem ele → tratada como META (legacy) e
fica pendente no health report. Mensagem cruzando eixos precisa de justificativa.

## Auto-avaliação: quem mede não é quem executou

Score de framework ou "nota" de sessão só vale acompanhado de: (1) `git diff` dos
**verificadores** desde o último score — expectativa de teste editada, skill reativada
para o teste passar, dado zerado antes de contar, log inexistente virando "não avaliado"
são inflação, não melhoria; (2) medição por **outro modelo** (Codex/`agy`, estratégia
multi-modelo) a cada versão. Verificador e coisa verificada **nunca** mudam no mesmo
commit. Série: 6,8 / 6,9 / 6,4 / **5,4** (terceiros) vs 7,1 / 8,6 / 7,4 (auto).
Régua: `~/cortex/vault/meta/score-framework-segunda-feira-05-set-2026-5-4-10.md`.
