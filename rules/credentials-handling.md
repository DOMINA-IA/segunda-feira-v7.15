# Credentials Handling (resumo)
> Severidade: MUST | Todos os agentes | Versão completa on-demand (triggers: credencial, senha, token, api key, secret, 1password, ssh, chmod, vazamento, .env)

**Regra de ouro:** "Em arquivo Markdown, nota, MEMORY ou briefing — só REFERÊNCIA, nunca o segredo." Credencial em texto plano = bomba-relógio (senha muda, arquivo não acompanha, agente futuro confia e falha).

## Hierarquia de armazenamento (preferência decrescente)

| # | Local | Quando usar |
|---|-------|-------------|
| 1 | **1Password** (vault DOMINA) | Senha root VPS, API keys premium, recovery codes |
| 2 | **`.env` chmod 600** | Tokens que scripts/apps consomem em runtime |
| 3 | **`~/.ssh/` chmod 600** | Chaves SSH privadas |
| 4 | **`~/_secrets/` (700 dir/600 file)** | Credenciais soltas sem categoria acima |
| 5 | **`~/projetos/clientes/<nome>/`** | Credenciais específicas de cliente |

**NUNCA texto plano em:** MEMORY.md, notas/briefings/sessões CORTEX, episódios consciousness, mailbox, scripts versionados em git, mensagens Telegram/Discord/Slack, comentários em código.

## Busca Obrigatória Antes de Pedir Credencial ao CEO (MUST — crítico)

> Origem: incidente 04-Mai-2026 — agente pediu senha que já estava no CORTEX vault. Episódio -0.8.

Antes de perguntar ao CEO qualquer credencial, executar OBRIGATORIAMENTE:
```bash
python3 ~/cortex/scripts/cortex_engine.py query "credenciais <serviço>"
grep -ri "<serviço>" ~/cortex/vault/infra/ ~/_secrets/ ~/.env ~/projetos/utm-manager/.env 2>/dev/null
```
Só após confirmar ausência em TODAS as fontes, perguntar ao CEO — depois ingerir a resposta no CORTEX como ponteiro (nunca o segredo em texto).

## Chmod obrigatório

`~/_secrets/` e `~/.ssh/` → `700` (dir). `.env*`, chaves privadas, credenciais de cliente → `600`. Chave pública `.pub` → `644`.

Detalhe completo (anti-patterns reais, template de nota correta, protocolo de resgate em incidente, validação automática futura) na versão on-demand.
