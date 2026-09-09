---
name: deploy-hostinger
description: "Publica landing page ou site estático no servidor Hostinger via SFTP e valida no ar com curl. Use ao publicar ou atualizar uma landing page. NOT for: app com backend na VPS — isso é /deploy-orchestra."
user-invocable: true
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
harnesses:
  - claude-code: full
  - codex: native
  - cursor: limited
  - aider: limited
---

# Deploy Hostinger — Sites Estáticos

> **Credenciais (05-Set-2026):** host, porta, usuário e senha vivem em `~/_secrets/hostinger.env` (chmod 600), fonte única.
> `SFTP_PASS=$(grep '^SFTP_PASS=' ~/_secrets/hostinger.env | cut -d= -f2-)`
> Nunca colar a senha aqui — ela já vazou em 44 arquivos por esse caminho.

## Contexto

**Servidor:** Hostinger (LiteSpeed)
**IP:** `${VPS_HOST}` | **Porta SSH:** `65002`
**Usuário:** `${HOSTINGER_USER}` | **Senha:** `${SFTP_PASS}`
**Root:** `~/domains/seudominio.com.br/public_html/`
**Domínio:** `seudominio.com.br`
**Método:** SCP via `expect` (sshpass não instalado no Mac)

---

## Diretórios Mapeados

| Pasta | Projeto | URL |
|-------|---------|-----|
| `funcionarios/` | LP Funcionários Invisíveis | seudominio.com.br/funcionarios/ |
| `desafio/` | LP Desafio MI | seudominio.com.br/desafio/ |
| `ai-first/` | LP AI FIRST | seudominio.com.br/ai-first/ |
| `clienteexemplo/` | CLIENTE_EXEMPLO Dr. CLIENTE_EXEMPLO | seudominio.com.br/clienteexemplo/ |
| `CLIENTE_EXEMPLO/` | CLIENTE_EXEMPLO_4 | seudominio.com.br/CLIENTE_EXEMPLO/ |
| `dominantes/` | Plataforma DOMINA.IA | seudominio.com.br/dominantes/ |
| `CLIENTE_EXEMPLO/` | CLIENTE_EXEMPLO | seudominio.com.br/CLIENTE_EXEMPLO/ |
| `selecao/` | Seleção | seudominio.com.br/selecao/ |
| `presencial/` | Presencial | seudominio.com.br/presencial/ |

---

## Execução

### Passo 1: Identificar o que deploiar

Se o usuário passou um argumento, usar como caminho. Caso contrário, perguntar:
- Qual arquivo/diretório local?
- Qual pasta na Hostinger? (sugerir da tabela acima)

### Passo 2: Auditoria rápida pré-deploy

Antes de enviar, verificar no HTML:
- Links `href="#id"` têm elemento com `id` correspondente
- Não há referências a bibliotecas removidas (grep por `lenis`, `locomotiveScroll` etc. no JS)
- Meta Pixel presente (`fbq`)
- Acentuação correta em PT-BR

Se encontrar problemas CRÍTICOS (links quebrados, JS morto), BLOQUEAR deploy e reportar.

### Passo 3: Upload via SCP

**Arquivo único:**
```bash
expect -c "
spawn scp -P 65002 -o StrictHostKeyChecking=no [ARQUIVO_LOCAL] ${HOSTINGER_USER}@${VPS_HOST}:~/domains/seudominio.com.br/public_html/[PASTA]/[ARQUIVO]
expect \"*assword*\"
send \"${SFTP_PASS}\r\"
expect eof
"
```

**Diretório inteiro:**
```bash
expect -c "
spawn scp -r -P 65002 -o StrictHostKeyChecking=no [DIR_LOCAL]/* ${HOSTINGER_USER}@${VPS_HOST}:~/domains/seudominio.com.br/public_html/[PASTA]/
expect \"*assword*\"
send \"${SFTP_PASS}\r\"
expect eof
"
```

### Passo 4: Verificar deploy

```bash
curl -s -o /dev/null -w "%{http_code}" https://seudominio.com.br/[PASTA]/
```

- **200** = Deploy OK
- **403/404/500** = Falha — investigar

### Passo 5: Reportar

Formato:
```
Deploy concluído!
URL: https://seudominio.com.br/[PASTA]/
Status: HTTP [código]
Arquivos: [lista]
```

---

## Comandos SSH úteis

```bash
# Listar diretórios
expect -c "
spawn ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${HOSTINGER_USER}@${VPS_HOST} {ls ~/domains/seudominio.com.br/public_html/}
expect \"*assword*\"
send \"${SFTP_PASS}\r\"
expect eof
"

# Criar novo diretório
expect -c "
spawn ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${HOSTINGER_USER}@${VPS_HOST} {mkdir -p ~/domains/seudominio.com.br/public_html/[NOVA_PASTA]}
expect \"*assword*\"
send \"${SFTP_PASS}\r\"
expect eof
"
```

---

## Para apps Next.js (export) ou SPA atrás de nginx

LPs estáticas usam o fluxo SCP+expect acima. Mas quando o deploy é de uma **app Next.js export** ou **SPA atrás de nginx em VPS**, consultar antes:

- `~/cortex/vault/infra/nginx-proxy-patterns.md` — port_in_redirect, Cache-Control diferenciado, locations de compat
- `~/patterns/frontend-deploy-checklist.md` — checklist completo (build → nginx → smoke test)
- `~/cortex/vault/patterns/frontend-debug-cascade.md` — diagnóstico em camadas se algo quebrar

Pontos críticos que NUNCA aparecem em LP estática mas são fatais em SPA:
1. Build precisa de `NEXT_PUBLIC_*` env vars (não basta no .env runtime)
2. nginx em porta interna sem `port_in_redirect off` vaza `:8080` em redirects
3. Cache-Control deve ser diferenciado: HTML no-store, chunks immutable, /api no-store, sw.js no-store
4. Service Worker antigo cacheado precisa ser desregistrado ou substituído por SW limpo
5. `systemctl enable` após `start` ou 502 no próximo reboot
6. `rsync --exclude` para não sobrescrever artifacts (uploads, db files) no destino

Edit local primeiro, depois deploy. NUNCA editar direto no servidor — próximo deploy reverte.
