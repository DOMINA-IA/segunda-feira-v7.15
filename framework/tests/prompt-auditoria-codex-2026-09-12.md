Você é auditor independente do framework Segunda-feira, um sistema de orquestração de
agentes de IA que vive neste Mac (~/.claude, ~/cortex, ~/consciousness, ~/framework,
~/broadcast, ~/brain) e, desde 05-Set-2026, tem runtime 24/7 numa VPS Ubuntu
(`ssh CLIENTE_EXEMPLO`, diretório /opt/segunda-feira, user ${RUN_USER}). Seu trabalho NÃO é
elogiar nem confirmar: é achar o que está errado, incompleto ou só parecendo certo.
Você é um modelo diferente do que fez o trabalho, de propósito.

CONTEXTO
Em 05-Set-2026 uma auditoria independente deu 5,4/10 (série de terceiros: 6,8 → 6,9 →
6,4 → 5,4; auto-avaliações: 7,1, 8,6, 7,4). No mesmo dia, o MESMO modelo que auditou
executou o plano de correção: reescreveu verificadores, moveu segredos, rotacionou senhas,
podou heurísticas, criou um hook e migrou o runtime para a VPS. Quem conserta e quem mede
não pode ser o mesmo, por isso você está aqui. Presuma que o executor foi otimista sobre
o próprio trabalho e prove onde.

Leia primeiro, sem confiar:
  ~/cortex/vault/meta/score-framework-segunda-feira-05-set-2026-5-4-10.md   (régua + série)
  ~/cortex/vault/meta/plano-correcao-framework-05-set-2026.md              (o que foi feito)
  ~/.claude/rules/judgment.md  seção "Auto-avaliação"                        (a regra nova)

REGRA DE OURO
Documentação não é estado. Nunca aceite um número porque um .md afirma. Rode o comando,
leia o arquivo, confira o path. Todo verificador abaixo foi reescrito em 05-Set pelo
executor: leia o código ANTES de aceitar o resultado. Use só Bash e Python padrão; não
dependa de ferramentas específicas de um harness.

MEÇA (Mac)
  python3 ~/framework/scripts/framework_health_check.py --json
  python3 ~/framework/tests/run-routing-battery.py
  python3 ~/framework/scripts/secret-scan.py
  python3 ~/consciousness/scripts/heuristic-stats.py
  crontab -l
  for d in ~/.claude ~/framework ~/consciousness ~/cortex ~/brain ~/broadcast; do
    echo "== $d"; git -C $d log --format='%h %ad %s' --date=short -8; git -C $d status --short | wc -l; done
  tail -50 ~/logs/sf-sync.log

MEÇA (VPS)
  ssh CLIENTE_EXEMPLO 'systemctl list-timers --all --no-pager "sf-*"; systemctl --no-pager --plain list-units "sf-*.service" --all;
    journalctl -u "sf-*" --since "7 days ago" --no-pager | grep -cE "Failed with"; ls -la /opt/segunda-feira/logs/;
    wc -l /opt/segunda-feira/consciousness/memory/procedural/heuristics.jsonl; find /opt/segunda-feira/cortex/vault -name "*.md" -newermt "-7 days" | wc -l;
    sudo -u ${RUN_USER} HOME=/opt/segunda-feira /opt/segunda-feira/.venv/bin/python3 /opt/segunda-feira/framework/scripts/framework_health_check.py'

INVESTIGUE ESPECIFICAMENTE (o que o executor mudou e pode ter calibrado em si mesmo)
1. Verificadores. `git -C ~/framework log -p -- scripts/framework_health_check.py tests/` desde
   o commit "baseline". Cada check novo (secret-scan, env-perms, skill-usage,
   heuristic-feedback, vps-timers) mede o que diz? Há check que só devolve OK? A bateria de
   roteamento ganhou 4 "controles negativos" e uma regra "score >= 2": isso mede assertividade
   ou foi desenhado para dar 28/28? Reproduza 3 casos à mão.
2. Runtime na VPS. Os 22 timers RODARAM na última semana? Cruze `journalctl` com o mtime e o
   TAMANHO de cada log em /opt/segunda-feira/logs/. `Persistent=true` e `OnFailure` existem
   nas units geradas? Provoque uma falha controlada (ex.: `systemctl start sf-log-rotate`
   com o script temporariamente sem permissão de execução) e verifique se o alerta chega à
   fila do dispatcher. Reverta. O heartbeat consolida na VPS às 23:30 BRT E o Mac não
   consolida mais? (`crontab -l`, `pgrep -f heartbeat` no Mac.)
3. Sincronização Mac↔VPS (`~/framework/runtime/sync/sf-sync.sh`, `sf-merge-jsonl.py`). Leia
   o código. Teste a união por id: grave um episódio de teste no Mac e outro na VPS com ids
   distintos, rode `sf-sync.sh quick`, confira que ambos existem nos dois lados sem
   duplicata. Depois um MESMO id com conteúdo diferente: quem vence? O vault com `--update`
   nos dois sentidos pode perder edição? Demonstre ou descarte. Apague os dados de teste.
4. Heurísticas. O executor restaurou o decay de 229 heurísticas, mudou a ordem do guard e
   podou 57. Compare `heuristics.jsonl.bak-audit-20260904`, `.bak-pre-prune-20260905` e o
   atual. O `heuristic_validator.py` recalibrado preserva decay sem evidência? Rode o
   ciclo duas vezes seguidas (`heuristic-lifecycle-guard.sh` em dry-run se houver) e prove
   que confidence não volta a 0,5. `times_failed` continua 0 em tudo? Então o loop de
   contra-evidência ainda não fecha, diga isso.
5. Hook `~/.claude/hooks/heuristic-loop-stop.py`. Ele bloqueia uma vez por sessão. Nos
   transcripts de ~/.claude/projects (jsonl), quantas sessões desde 05-Set tiveram o
   bloqueio e em quantas o agente respondeu registrando `--heuristic-applied` de verdade
   versus dizendo "nenhuma se aplicou"? Se a resposta padrão virou "nenhuma", o hook virou
   ritual, não loop.
6. Skills. `skill-usage` no health check conta invocações reais do Skill tool nos transcripts.
   Conte você mesmo (tool_use name=Skill) nos últimos 7 dias e separe skills do framework
   das vendidas pela Anthropic (impeccable, frontend-design, web-design-guidelines). 11
   agentes ganharam "Skill" em `tools:`: algum subagente invocou skill desde então?
7. Segredos. `secret-scan.py` diz 0. Verifique com SEUS próprios padrões (token Meta EAA…,
   bot Telegram, URL com senha, `pass=`) em ~/cortex, ~/.claude (fora de projects/),
   ~/consciousness, ~/framework, ~/broadcast e em /opt/segunda-feira na VPS. Reporte LOCAL e
   TIPO, nunca o valor. A senha antiga do Postgres consta no commit baseline de ~/.claude
   (skills inativas): foi purgada antes de qualquer remote? Existe remote?
8. Paths. Para rules (~/.claude/rules e ~/cortex/vault/rules), agentes (~/.claude/agents e
   ~/.claude/commands/segunda-feira/agents) e skills ativas (~/.claude/skills/*/SKILL.md),
   extraia os caminhos `~/...` e `/Users/...` e meça o percentual que não existe. Em 05-Set
   era 5% (34/585).
9. CLAUDE.md e MEMORY.md (~/.claude/projects/-HOME-/memory/MEMORY.md)
   batem com a máquina? Contadores, o que "roda na VPS", o que "fica no Mac".

ENTREGUE
Nota 0-10 em cada dimensão da régua, com o comando e a saída que sustentam cada uma:
Visão & Arquitetura · Cultura de governança · Aprendizado (conceito) · Aprendizado
(execução) · Consistência estrutural · Performance/Observabilidade · Assertividade ·
Segurança. Média simples = nota geral.

Depois: os 5 problemas mais graves ainda abertos, em ordem de impacto, com caminho do
arquivo. E, separado: o que a sessão de 05-Set corrigiu mas ficou frágil, pela metade ou
calibrado em si mesmo.

Grave o resultado em
  ~/cortex/vault/meta/score-framework-segunda-feira-<DD-mmm-2026>-<nota>-10.md
com o mesmo frontmatter das notas anteriores da série (copie de
score-framework-segunda-feira-05-set-2026-5-4-10.md e ajuste id/title/created/tags), e
rode `python3 ~/cortex/scripts/cortex_engine.py build-index` ao final.

CRITÉRIO DA SUA PRÓPRIA AUDITORIA
Uma auditoria que não encontra nada é uma auditoria ruim. O executor de 05-Set registrou
ele mesmo pendências que não conseguiu fechar (seção "Execução" do plano). Se todas
estiverem fechadas E você não achar nada novo, diga isso explicitamente, mas saiba que é o
resultado menos provável. Não use o número 5,4 como âncora: meça do zero.
