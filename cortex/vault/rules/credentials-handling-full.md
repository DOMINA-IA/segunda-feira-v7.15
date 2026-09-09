---
id: credentials-handling-full
title: Credentials Handling (completo)
type: rule
domain:
- meta
agents:
- sf-master
tags:
- credenciais
- segurança
- 1password
- secrets
triggers:
- credencial
- senha
- token
- api key
- secret
- 1password
- ssh
- chmod
- vazamento
- .env
status: active
created: '2026-05-24'
last_verified: '2026-07-07'
decay_rate: 0.01
on_demand: true
axis: meta
links:
- target: autonomous-execution-full
  type: auto-linked
- target: evolution-scorecard
  type: auto-linked
- target: axis-separation-full
  type: auto-linked
- target: vps-principal
  type: auto-linked
---

# Credentials Handling — Onde Senha, Token e Chave Vivem (e Onde NÃO Vivem)

> **Severidade:** MUST | **Aplica-se a:** Todos os agentes
> **Origem:** Incidente 22-Mai-2026 — senha VPS texto plano em MEMORY (credenciais-vps-CLIENTE_EXEMPLO-2026-05-09.md) desatualizou silenciosamente, gastou tempo de sessão tentando senha errada. Decisão: NUNCA mais texto plano fora de cofres dedicados.

## Princípio

**Credencial em texto plano = bomba-relógio.** Senha pode mudar; arquivo não acompanha; agente futuro confia no que está escrito e falha. Solução: credenciais vivem em **um lugar autoritativo**, tudo mais é **ponteiro**.

**Regra de ouro:** "Em arquivo Markdown, nota, MEMORY ou briefing — só REFERÊNCIA, nunca o segredo."

---

## Hierarquia de armazenamento (preferência decrescente)

| # | Local | Quando usar | Quem acessa |
|---|-------|-------------|-------------|
| 1 | **1Password** (vault DOMINA) | Senha root VPS, API keys premium, recovery codes humanos | CEO via desktop/CLI 1Password |
| 2 | **`.env` com chmod 600** | Tokens de API que scripts/apps consomem (Meta, Telegram, OpenAI, Anthropic) | apps/scripts em runtime |
| 3 | **`~/.ssh/` (chmod 600)** | Chaves SSH privadas | ssh-agent / paramiko |
| 4 | **`~/_secrets/` (chmod 700 dir + 600 file)** | Credenciais "soltas" que não cabem nas categorias acima (recovery codes baixados, etc) | acesso manual CEO |
| 5 | **Diretório-cliente** (`~/clientes/<nome>/`) | Credenciais específicas de cliente (logins de plataforma do cliente, dados de acesso) | trabalho com aquele cliente |

## NUNCA armazenar texto plano em

- `MEMORY.md` ou qualquer arquivo em `~/.claude/projects/.../memory/`
- Notas CORTEX (`~/cortex/vault/*`)
- Briefings (`~/cortex/briefings/*`)
- Episódios consciousness (`~/consciousness/memory/episodic/*`)
- Mensagens broadcast/mailbox (`~/broadcast/mailbox/*`)
- Sessões CORTEX (`~/cortex/sessions/*`)
- Scripts versionados em git (incluir `.env` no `.gitignore`)
- Mensagens Telegram, Discord, Slack
- Comentários em código

## Anti-Patterns reais detectados

| Anti-pattern | Risco | Correção |
|--------------|-------|----------|
| `**Senha:** \`S3nh4Ant1g4@Ex3mpl0\`` em nota MEMORY | Senha trocada — nota mente — agente perde tempo | Substituir por "ver 1Password sob `<chave>`" |
| `password="hardcoded"` em script Python | Script versionado vaza segredo | `os.environ["PASSWORD"]` + `.env` |
| `.git-credentials` com token em texto plano | Push acidental para repo público | Usar `gh auth login` (token criptografado) ou SSH deploy keys |
| Token Meta API no body de mensagem Telegram | Histórico Telegram não criptografado entre fronteiras | Token só em `.env` server-side |
| Recovery codes baixados em `~/Downloads/` | Esquecidos + acesso de qualquer processo | Mover para `~/_secrets/` (chmod 600) ou 1Password |
| Credencial cliente em `~/Documents/` ou `~/Desktop/` | Misturada com pessoal, sem chmod | `~/clientes/<nome>/credenciais.env` (chmod 600) |

## Como uma NOTA CORRETA fica

```markdown
## VPS Principal — Credenciais

- **Acesso default:** SSH key id_ed25519 (Mac) autorizada em /root/.ssh/authorized_keys da VPS
- **Senha root:** ver 1Password sob "${REDIGIDO}"
- **Senha last-rotated:** 2026-05-09 (manter campo, atualizar quando trocar)
- **CLIENTE_EXEMPLO password:** referenciada em /opt/CLIENTE_EXEMPLO/.env (chmod 600) — variável CLIENTE_EXEMPLO_PASSWORD
```

NUNCA assim:
```markdown
## VPS Principal
- **Senha:** S3nh4Ant1g4@Ex3mpl0  ← VAZAMENTO
```

## Validação automática (futuro — não implementado ainda)

Hook `pre-commit` ou `router.py` deveria scanear texto novo em notas/MEMORY contra patterns:
- `password\s*[:=]\s*["\'`]?[A-Za-z0-9@!#$%&]+`
- `token\s*[:=]\s*["\'`]?[A-Za-z0-9_-]{20,}`
- `api[_-]?key\s*[:=]\s*["\'`]?[A-Za-z0-9_-]{20,}`

Bloqueia commit/write se match. Implementar quando o sistema crescer.

## Chmod obrigatório

| Item | Permissão |
|------|-----------|
| `~/_secrets/` (diretório) | `700` |
| `~/_secrets/*` (arquivos) | `600` |
| `~/.ssh/` | `700` |
| `~/.ssh/id_*` (chave privada) | `600` |
| `~/.ssh/*.pub` (chave pública) | `644` |
| `.env*` em qualquer lugar | `600` |
| Credenciais em `~/clientes/<nome>/` | `600` |

Comando para auditar e corrigir:
```bash
find ~/_secrets ~/clientes -name "*.env*" -o -name "credenc*" -o -name "*-secret*" | xargs chmod 600 2>/dev/null
chmod 700 ~/_secrets ~/.ssh
```

## Busca Obrigatória Antes de Pedir Credencial ao CEO (MUST)

> **Origem:** Incidente 04-Mai-2026 — agente pediu senha Hostinger ao CEO; credencial estava no CORTEX vault. Confronto público, episódio -0.8. Promovido de heurística a rule constitucional em 24-Mai-2026.

**Antes de perguntar ao CEO qualquer credencial, executar OBRIGATORIAMENTE:**

```bash
# 1. Busca no CORTEX (ampla)
python3 ~/cortex/scripts/cortex_engine.py query "credenciais <serviço>"

# 2. Busca direta no vault de infra
grep -ri "<serviço>" ~/cortex/vault/infra/ 2>/dev/null

# 3. Busca no diretório de secrets
grep -ri "<serviço>" ~/_secrets/ 2>/dev/null

# 4. Busca no .env local
grep -ri "<serviço>" ~/.env ~/projetos/utm-manager/.env 2>/dev/null
```

Só após confirmar que NÃO existe em nenhuma dessas fontes, pedir ao CEO.

**Fluxo correto:**
```
Preciso de credencial X
  → Buscar CORTEX + vault/infra + _secrets + .env
  → Encontrou? → Usar diretamente
  → Não encontrou? → Perguntar ao CEO + depois ingerir no CORTEX como ponteiro
```

**Custo de não seguir:** interrupção desnecessária do CEO + vergonha pública (incidente 04-Mai). Confiança do CEO no sistema diminui cada vez que agente pede o que já existe.

---

## Integração com outras rules

| Rule | Como interage |
|------|---------------|
| `axis-separation.md` | Credenciais são META (infra), nunca OPS (campanha não precisa de senha bruta) |
| `cortex-usage.md` | Notas CORTEX nunca contêm segredo, só ponteiro para vault; seção "Cruzamento Obrigatório de Padrões" — validar com fonte autoritativa (1Password ou .env atual) antes de assumir credencial cacheada |

---

## Resgate em incidente

Se você (agente futuro) encontrar credencial em texto plano em arquivo onde não deveria estar:

1. **NÃO citar o segredo** em response
2. **NÃO escrever** o segredo em outro arquivo (propagaria o vazamento)
3. Avisar CEO no momento da detecção
4. Sugerir migração para local correto (1Password preferencial)
5. Após migração: substituir conteúdo da nota original por ponteiro
6. Registrar episódio (`@security-auditor`) com heurística

**Não delete o arquivo unilateralmente** — o CEO precisa saber para girar a credencial se houver suspeita de vazamento prévio.
