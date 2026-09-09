# Changelog — Segunda-feira

Registro público das versões distribuídas. Detalhes operacionais internos
(incidentes, dados de cliente, números do negócio) não entram aqui.

---

## v7.15 — "Contexto é orçamento" (setembro/2026)

Versão de **subtração**. O framework aprendeu que crescer somando componentes
piora o resultado, e cortou.

### Context engineering

- **Regras always-loaded: 11 → 5** (−39% em palavras). Auditoria encontrou a
  mesma instrução repetida em até 7 arquivos: "mailbox" em 5, "confidence" em 4,
  "Anti-Pattern" em 7. Instrução duplicada compete por atenção em vez de somar.
  As substituídas viraram on-demand com `triggers:`, sem perda de cobertura.
- **Skills: formato corrigido e catálogo podado.** Descoberta que motivou a
  mudança: no Claude Code uma skill só carrega em `skills/<nome>/SKILL.md` — um
  `.md` solto **não é carregado**, mas sua `description` continua pesando no
  contexto de toda sessão. O catálogo tinha mais de 100 skills nesse estado.
  Corrigido o formato e podado o que não era invocado: ~58% menos custo de
  descriptions.
- Critério adotado: antes de criar uma skill, pergunte se o gatilho é **verbal**
  (alguém digita) ou **automático** (então é hook ou agendamento, não skill).

### Menos fricção para instalar e usar

- `settings.template.json` com permissões e hooks já registrados — o usuário
  para de aprovar cada chamada manualmente
- **Autonomy gate** (`autonomy-gate.py`): allow/ask/deny por classe de ação, com
  livro-razão do que foi executado
- **Session bootstrap** (`session-bootstrap.py`): a sessão sobe com o contexto do
  projeto (git, arquivos-chave, stories abertas)
- Instalador reescrito: instala a partir do clone local (não de repo remoto
  hardcoded), cria `settings.json` a partir do template, faz backup do que já
  existe e nunca sobrescreve sem aviso

### O agente cobra contexto

- Nova regra `context-quality` + hook `context-coach.py` (UserPromptSubmit):
  quando o pedido chega com menos de 2 dos 5 elementos que o tornam executável,
  o agente **pergunta antes de chutar**. Chamadas automatizadas são ignoradas.

### Verificação e anti-teatro

- `framework_health_check.py` confronta 14 afirmações da constituição contra o
  estado real da máquina e falha alto na divergência
- Princípio adotado: **quem mede não é quem executou**; verificador e coisa
  verificada nunca mudam no mesmo commit
- Gate de publicação (`tools/validate-publish.py`) ampliado de 30 para 44 checks,
  agora cobrindo chave privada em bloco, documentos fiscais, telefone formatado,
  e-mail de terceiro e certificados
- Sanitizador determinístico (`tools/sanitize-v715.py`) com ordem de precedência
  explícita, para que a distribuição seja reproduzível e não dependa de revisão
  manual

### Segurança do processo de release

- Lição incorporada ao processo: **sanitizar o arquivo não sanitiza o
  repositório**. O Git guarda cada versão como objeto imutável, então o gate
  passa a ser rodado também contra o commit-base (`git archive <sha> | gate`),
  não apenas contra o working tree
- Pacote publicado com histórico virgem, não como continuação de histórico antigo

---

## v7.14 — "Narrativa → Medição" (maio/2026)

Auditoria crítica do framework por três revisores paralelos.

- **Achado-raiz:** a constituição documentava correções que nunca haviam sido
  aplicadas. Uma versão anterior alegava por escrito uma configuração de modelo
  padrão que jamais existiu no arquivo de settings — com efeito direto no custo.
  Origem do princípio "documentação não é estado"
- Heurísticas passaram a ser recuperadas em runtime (antes eram gravadas e nunca
  lidas de volta)
- `framework_health_check.py` criado como validador anti-teatro
- Limpeza física: repositórios de pesquisa arquivados, agendamentos mortos
  documentados, contadores corrigidos

---

## v7.13 — Trajectory Eval (maio/2026)

Blocos de expectativa de trajetória nas stories e logging de desvio de ferramenta
em tempo real. Correção de sinais acumulados e nós órfãos no grafo de conhecimento.

## v7.12 — Independence Day (maio/2026)

O framework deixou de ser customização de um core de terceiros e passou a ser
independente: diretório próprio, manifesto próprio, CLI de terceiros removido.

## v7.11 — Audit & Hardening (maio/2026)

Primeira curadoria do pool de heurísticas em produção; promoção de regras a partir
de incidentes reais; credenciais hardcoded migradas para `.env`.

## v7.10 — Controle de custo (maio/2026)

Modelo padrão declarado explicitamente no settings, e watchdog que detecta sessão
de trabalho mecânico rodando em modelo caro. Origem da regra de model routing.

## v7.7–v7.9 — Absorções (maio/2026)

Estudo de frameworks de referência e absorção seletiva: fases de especificação e
teste no ciclo de story, criação automática de skills a partir de padrões
repetidos, busca full-text no histórico de sessões, modelo vivo do usuário.
Anti-absorções declaradas explicitamente — o que foi recusado, e por quê.

## v7.6 e anteriores

Pre-flight entre sessões, ferramentas de auditoria sem dependência externa,
knowledge system indexado, memória episódica com valência.
