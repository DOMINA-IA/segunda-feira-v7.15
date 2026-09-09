#!/usr/bin/env node
// agent-booster.mjs — Refactors mecânicos $0 (Tier 0 WASM-style, mas implementação simples regex)
// Origem: ruflo Agent Booster (3-Tier Routing). Esta é uma versão simplificada por regex
// até trocarmos por tree-sitter real. Mesmo assim: $0, latência <1ms, zero LLM.
//
// Uso:
//   node agent-booster.mjs --intent var-to-const --file src/foo.ts
//   node agent-booster.mjs --intent remove-console --file src/foo.js
//   node agent-booster.mjs --intent async-await --file src/api.ts
//
// Intents suportados:
//   var-to-const     — `var` → `const` (heurístico: se nunca reassinado)
//   let-to-const     — `let` → `const` (mesmo critério)
//   remove-console   — remove console.log/debugger lines
//   async-await      — .then() chain → await (estrutural simples)

import fs from "node:fs";

const argv = process.argv.slice(2);
const args = {};
for (let i = 0; i < argv.length; i++) {
  if (argv[i].startsWith("--")) {
    const key = argv[i].slice(2);
    args[key] = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[i + 1] : true;
    if (args[key] !== true) i++;
  }
}

if (!args.intent || !args.file) {
  console.error("Uso: agent-booster.mjs --intent <intent> --file <path> [--dry-run]");
  console.error("Intents: var-to-const, let-to-const, remove-console, async-await");
  process.exit(1);
}

const filePath = args.file;
if (!fs.existsSync(filePath)) {
  console.error(`Arquivo não existe: ${filePath}`);
  process.exit(1);
}

const original = fs.readFileSync(filePath, "utf8");
let modified = original;
let changes = 0;

function isReassigned(text, name) {
  // Heurística simples: se aparece `name =` (sem outro var/let/const antes), foi reassigned
  const reassignRegex = new RegExp(`(^|[^.\\w])${name}\\s*=(?!=)`, "g");
  let matches = 0;
  let m;
  while ((m = reassignRegex.exec(text)) !== null) matches++;
  return matches > 1; // declaração inclui 1 match
}

switch (args.intent) {
  case "var-to-const":
  case "let-to-const": {
    const keyword = args.intent === "var-to-const" ? "var" : "let";
    const regex = new RegExp(`\\b${keyword}\\s+([a-zA-Z_$][\\w$]*)\\s*=`, "g");
    modified = modified.replace(regex, (match, name) => {
      if (isReassigned(original, name)) {
        return match; // mantém
      }
      changes++;
      return `const ${name} =`;
    });
    break;
  }
  case "remove-console": {
    const lines = modified.split("\n");
    const filtered = lines.filter((line) => {
      const trimmed = line.trim();
      if (/^(console\.(log|info|debug|warn|error)|debugger);?$/.test(trimmed)) {
        changes++;
        return false;
      }
      return true;
    });
    modified = filtered.join("\n");
    break;
  }
  case "async-await": {
    // Detecta .then(arrow) simples e converte para await (best-effort)
    const regex = /(\w+(?:\([^)]*\))?)\.then\(\s*\(?(\w+)\)?\s*=>\s*\{?\s*([^}]+?)\s*\}?\s*\)/g;
    modified = modified.replace(regex, (match, expr, param, body) => {
      changes++;
      const cleanBody = body.replace(/return\s+/, "").trim();
      return `const ${param} = await ${expr};\n${cleanBody.replace(new RegExp("\\b" + param + "\\b", "g"), param)}`;
    });
    break;
  }
  default:
    console.error(`Intent desconhecido: ${args.intent}`);
    process.exit(1);
}

if (changes === 0) {
  console.log(`Nenhuma mudança aplicável (${args.intent} em ${filePath})`);
  process.exit(0);
}

if (args["dry-run"]) {
  console.log(`[DRY-RUN] ${changes} mudança(s) detectada(s) em ${filePath}`);
  console.log("Diff:");
  const origLines = original.split("\n");
  const modLines = modified.split("\n");
  for (let i = 0; i < Math.max(origLines.length, modLines.length); i++) {
    if (origLines[i] !== modLines[i]) {
      if (origLines[i] !== undefined) console.log(`  -${i + 1}: ${origLines[i]}`);
      if (modLines[i] !== undefined) console.log(`  +${i + 1}: ${modLines[i]}`);
    }
  }
} else {
  // Backup
  const backupPath = `${filePath}.bak-${Date.now()}`;
  fs.writeFileSync(backupPath, original);
  fs.writeFileSync(filePath, modified);
  console.log(`✓ ${changes} mudança(s) em ${filePath}`);
  console.log(`  Backup: ${backupPath}`);
}
