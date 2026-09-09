---
name: template-literal-audit
description: 'Audita server.js monolítico com HTML+JS+SQL em template literal: escapes de regex perdidos (barra-d, barra-s, barra-n) e aspas duplas em SQL que quebram no SQLite. Use antes de deploy ou quando "filtro não funciona". NOT for: código sem template lite'
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Grep
  - WebFetch
harnesses:
  - claude-code: full
  - codex: native
  - cursor: limited
  - aider: limited
---

# Template Literal Audit — Caça-bugs em Monólitos Node

## Quando usar

Sintomas que disparam esta skill:
- "Filtro do sistema não acha nada que claramente existe" (regex perdeu `\`)
- "DELETE/UPDATE retorna `no such column: 'now'`" (aspas SQL erradas)
- "Funciona local mas em prod não" (template literal interpretou escape)
- Antes de qualquer deploy de mudança em `server.js` que toque template literal multiline

**Origem:** CLIENTE_EXEMPLO `server.js` (06/Mai/2026) — 2 bugs em 1 sessão por escapes mal cuidados em template de ~3700 linhas.

---

## Contexto técnico

### O problema

Quando código JS é escrito DENTRO de um template literal (` `...` ` com backticks) que serializa o frontend inteiro:

```js
function getHTML() {
  return `<!DOCTYPE html>
<html>
<head>...</head>
<body>
<script>
  // Esse JS aqui passa pela engine de template literal antes de chegar ao browser
  var digitsOnly = term.replace(/\D/g, '');  // ❌ \D → D no output
  db.query("UPDATE x SET t = datetime(\"now\")");  // ❌ "" interpretado em SQLite
</script>
</body>
</html>`;
}
```

**O que acontece:**
- `\d`, `\D`, `\s`, `\n`, `\t` em regex → backslash descartado, vira só `d`, `D`, `s`, etc.
- `\\d` no source → `\d` no output (correto)
- Aspas duplas em SQL embutido → SQLite interpreta como identificador (não é template literal mas é mesmo arquivo)

### Caracteres safe (não precisam escape duplo)

- Unicode literais: `/[̀-ͯ]/` (diacríticos NFD) — não usa `\`
- Aspas simples e backticks dentro de strings em outros contextos

---

## Execução

### Passo 1 — Identificar o(s) template literal(s)

```bash
grep -n "return \`<!DOCTYPE\|res.send(\`<!DOCTYPE\|return \`<html" <FILE>
```

Note linhas de início e fim (procurar `\`\)` ou `\`;` próximo).

### Passo 2 — Auditar regex problemáticas

```bash
# Procurar regex que DEVERIAM ter \d/\D/\s mas estão sem o backslash duplicado
grep -nE "replace\(/[^\\\\][dDsSnt]/|match\(/[^\\\\][dDsSnt]/|test\(/[^\\\\][dDsSnt]/" <FILE> | head -20
```

Se aparecer algo como `replace(/D/g` sem barra dupla antes do D → bug em potencial. Verificar se está dentro do template literal (entre as linhas mapeadas no Passo 1).

### Passo 3 — Auditar SQL com aspas duplas

```bash
# datetime("now") e similares
grep -nE "datetime\(\"now\"|date\(\"now\"|strftime\(\"" <FILE>
```

Se achar → trocar para aspas simples: `datetime('now')`.

```bash
# WHERE x = "literal" (em SQLite vira erro)
grep -nE "WHERE [a-z_]+ = \"[a-z]" <FILE>
```

### Passo 4 — Validar HTML servido (pós-deploy)

```bash
# Para CLIENTE_EXEMPLO
curl -s -u '${APP_USER}:${APP_PASS}' https://seudominio.com.br/ -o /tmp/page.html

# Para outros sistemas: ajustar credenciais/URL

# Confirmar que regex novas chegaram intactas
grep -E "replace\(/\\\\[dDsS]/|match\(/\\\\[dDsS]/" /tmp/page.html | head -10
```

Se `\d` virou `d`, `\D` virou `D`, etc → bug confirmado, redeploy com fix.

### Passo 5 — Simular template literal em node

```bash
# Testar como o JavaScript engine interpreta seu source
node -e "const html = \`var x = /\\\\d/g;\`; console.log('Output:', html);"
# Esperado: var x = /\d/g;

node -e "const html = \`var x = /\\d/g;\`; console.log('Output:', html);"
# Esperado: var x = /d/g; (BUG — backslash sumiu)
```

### Passo 6 — Aplicar fixes

```js
// Em regex
term.replace(/\D/g, '')      // ❌ no template literal
term.replace(/\\D/g, '')     // ✅ source dobrado, vira /\D/g no output

// Em SQL
db.prepare('SET t = datetime("now")')   // ❌ SQLite reclama
db.prepare("SET t = datetime('now')")   // ✅ aspas simples no SQL
```

### Passo 7 — Re-deploy + smoke test

Seguir protocolo de `feedback-deploy-pm2-monolith.md`:
1. `node -c <file>`
2. Backup remoto timestampado
3. `scp` + `pm2 restart`
4. `pm2 logs --lines 10 | grep -E 'rodando|Erro|Error'`
5. `curl` o HTML servido + grep do token corrigido
6. Smoke test do endpoint específico (ex: o filtro que estava quebrado)

---

## Sistemas conhecidos vulneráveis

Todos os monólitos Node que serializam frontend dentro do mesmo arquivo:

| Sistema | Path no servidor | Linha do template literal |
|---------|------------------|--------------------------|
| **CLIENTE_EXEMPLO Dashboard** | `/opt/clienteexemplo-project/dashboard/server.js` | ~2972 a ~6700 |
| **CLIENTE_EXEMPLO Dashboard** | `/opt/CLIENTE_EXEMPLO-dashboard/...` | (auditar) |
| **plataforma-orquestrador** | `/opt/plataforma-orquestrador/server.js` | (auditar) |
| **dominantes** | (verificar) | (auditar) |
| **segunda-feira-daemon** | (verificar) | (auditar) |

Antes de mexer em qualquer um, rodar Passo 1 + Passo 2 desta skill.

---

## Anti-patterns

| Erro | Sintoma | Fix |
|------|---------|-----|
| `replace(/\d/g, '')` no template | Filtro acha letra "d", não dígito | `/\\d/g` |
| `match(/\D+/)` no template | Acha letra "D", não non-digit | `/\\D+/` |
| `datetime("now")` no SQL | "no such column 'now'" | `datetime('now')` |
| `WHERE stage = "novo"` no SQL | Erro de coluna | `WHERE stage = 'novo'` |
| `'\\n'` em mensagem WhatsApp | Newline literal no output | `'\\n\\n'` (template literal precisa) |
| Confiar em `node -c` apenas | Sintaxe passa, runtime quebra | Sempre curl + grep do servido |

---

## Output esperado

Ao final da execução desta skill, entregar:

```markdown
# Template Literal Audit — <FILE>

## Bugs encontrados
- Linha X: regex `/D/g` deveria ser `/\\D/g` (dentro do template iniciado em linha Y)
- Linha Z: `datetime("now")` deveria ser `datetime('now')`

## Fixes propostos
[diffs específicos]

## Smoke test pós-fix
[comandos curl/grep para validar]
```

---

## Heurística

> "Template literal multiline não é só string — é uma ZONA DE INTERPRETAÇÃO. Tudo que parece JavaScript ali dentro passa pela engine duas vezes: uma na compilação do template, outra no browser. Backslash e aspas duplas são as armadilhas mais comuns."
