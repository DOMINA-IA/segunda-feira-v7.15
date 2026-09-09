---
name: lp-live-debug
description: "Diagnostica e corrige LP em produção com comportamento errado (redirect, CTA trocado, fluxo quebrado) via fetch do HTML, análise do JS e correção por SSH na Hostinger. Use quando 'a LP vai direto pro checkout' ou 'o botão não faz nada'. NOT for:…"
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - WebFetch
  - mcp__fetch__fetch
harnesses:
  - claude-code: full
  - codex: native
  - cursor: limited
  - aider: limited
---

# LP Live Debug — Diagnóstico e Correção de LP em Produção

## Contexto

Skill para quando o usuário relata que uma LP está se comportando errado em produção.
Exemplos de sintomas que disparam esta skill:

- "A LP está indo direto para o checkout"
- "O quiz não abre, vai para outra página"
- "O botão não faz nada"
- "A página redireciona sozinha"
- "Cliquei no CTA e foi para o lugar errado"

**Origem:** Quiz AI FIRST (08/Abr/2026) — botão "QUERO PARAR DE PERDER DINHEIRO" na
tela intro chamava `goToCheckout()` quando deveria chamar `startQuiz()`.

---

## Execução

### Passo 1 — Receber URL e sintoma

Pedir (se não fornecido):
- URL completa da LP
- Sintoma exato ("vai para X quando deveria fazer Y")

### Passo 2 — Fetch do HTML ao vivo

```
mcp__fetch__fetch(url, raw=true, max_length=50000)
Se truncado: buscar offset 50000 para pegar o bloco JS
```

### Passo 3 — Checklist de Diagnóstico

#### A. Redirecionamento automático (sem clique)
```
Grep por:
- window.location.href =
- window.location.replace(
- window.location.assign(
- <meta http-equiv="refresh"
```
Se encontrado **fora de uma função** (código de nível superior): é o redirect automático.

#### B. CTA com função errada
```
Grep por:
- onclick="[FUNÇÃO]()"  em elementos button/a na tela inicial (screen0, #intro, #hero)
```
Mapear cada CTA → função chamada → o que essa função FAZ no código:
- Se vai para checkout mas deveria iniciar quiz → trocar para startQuiz()
- Se não faz nada → função não definida (ver item C)
- Se redireciona para URL errada → verificar a variável CHECKOUT_URL ou o href

**Padrão crítico Quiz/Funil multi-step:**
```
Tela 0 (intro)     → botão deve chamar: startQuiz() / goToScreen(1) / nextStep()
Tela resultado     → botão deve chamar: goToCheckout() / goToPurchase()
```
Se essas duas funções estiverem trocadas = bug desta sessão.

#### C. Função chamada mas não definida
```
Para cada onclick="funcX()" encontrado:
- Verificar se "function funcX" OU "const funcX" OU "var funcX" existe no JS
- Se não existe → erro silencioso no console, botão morto
```

#### D. window.open vs window.location
```
Grep por window.open e window.location no bloco goToCheckout/redirect:
- window.open(url, '_blank')  → abre em nova aba (ok para checkout)
- window.location.href = url  → substitui a página atual (perda de UTMs no histórico)
```

#### E. Variável de URL incorreta
```
Grep por CHECKOUT_URL, REDIRECT_URL, TARGET_URL
Verificar se o valor aponta para o destino correto
```

---

### Passo 4 — Relatório de Diagnóstico

```markdown
## Diagnóstico LP — [URL]

**Sintoma relatado:** [o que o usuário disse]
**Causa raiz identificada:** [descrição]
**Localização:** linha [N] — `[trecho do código]`
**Correção necessária:** [de X para Y]
```

---

### Passo 5 — Correção via SSH Hostinger

Após confirmação (ou autonomia ativa), aplicar fix:

```bash
# Identificar linha exata
expect -c "
spawn ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${HOSTINGER_USER}@${VPS_HOST} \
  \"grep -n '[PADRÃO]' ~/domains/seudominio.com.br/public_html/[PASTA]/[ARQUIVO]\"
expect \"*assword*\"
send \"${SFTP_PASS}\r\"
expect eof
"

# Aplicar correção com sed
expect -c "
spawn ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${HOSTINGER_USER}@${VPS_HOST} \
  \"sed -i 's/[TEXTO_ANTIGO]/[TEXTO_NOVO]/g' ~/domains/seudominio.com.br/public_html/[PASTA]/[ARQUIVO] && \
   grep -n '[CONFIRMAÇÃO]' ~/domains/seudominio.com.br/public_html/[PASTA]/[ARQUIVO]\"
expect \"*assword*\"
send \"${SFTP_PASS}\r\"
expect eof
"
```

**Caminhos Hostinger disponíveis:**
- `/ai-first/` — Quiz/LP AI FIRST
- `/desafio/` — LP Desafio
- `/funcionarios/` — LP Funcionários Invisíveis
- `/clienteexemplo/` — CLIENTE_EXEMPLO Dr. CLIENTE_EXEMPLO
- `/CLIENTE_EXEMPLO/` — CLIENTE_EXEMPLO_4

### Passo 6 — Verificação ao vivo

Fazer novo fetch da URL para confirmar que a correção está refletida no HTML servido.

---

## Casos Conhecidos

| Sintoma | Causa mais comum | Fix |
|---------|-----------------|-----|
| LP vai direto ao checkout | CTA intro com `goToCheckout()` em vez de `startQuiz()` | Trocar onclick |
| Botão não faz nada | Função chamada não definida (JS morto) | Definir função ou usar nativa |
| Página redireciona sozinha ao carregar | `window.location` fora de função, no top-level | Envolver em condição ou remover |
| Quiz pula etapas | selectOption() chama goToScreen(N+2) em vez de N+1 | Corrigir incremento |
| Checkout vai para URL errada | CHECKOUT_URL apontando para produto errado | Atualizar variável |
| **Filtro/regex não acha o que claramente existe** (sistema monólito Node) | **Backslash perdido em template literal** (`\d` → `d`) | **Skill `/template-literal-audit` — duplicar barra: `\\d`** |
| **DELETE/UPDATE retorna `no such column: 'now'`** | **Aspas duplas em SQLite literal** | **Trocar `datetime("now")` por `datetime('now')`** |

---

## Output Final

```
✅ Bug encontrado e corrigido
Arquivo: [PASTA]/[ARQUIVO]
Linha: [N]
De: onclick="[ANTIGO]()"
Para: onclick="[NOVO]()"
Verificado ao vivo: [URL] — HTML atualizado confirmado
```
