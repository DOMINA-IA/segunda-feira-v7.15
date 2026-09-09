#!/usr/bin/env python3
"""Hook PreToolUse: Valida acentuação em português antes de Write/Edit.
Bloqueia se detectar palavras sem acento em .html, .md, .txt, .mdx

Melhoria (Sprint 2 / Grupo A7 — 07-Jul-2026): ignora trechos técnicos antes
de checar acentuação — code-fences (```...```), URLs, paths de arquivo e
slugs (kebab/snake-case) — para evitar falso-positivo bloqueante confirmado
na auditoria (ex.: "nao" dentro de um bloco de código ou em "model-watchdog"
não é prosa em português)."""

import sys
import json
import re

# Trechos técnicos ignorados na checagem de acentuação (nesta ordem).
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_URL_RE = re.compile(r"https?://\S+")
_PATH_RE = re.compile(r"\S*/\S+")
_SLUG_RE = re.compile(r"\b[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)+\b")


def _strip_technical(content: str) -> str:
    """Remove code-fences, URLs, paths e slugs antes de checar acentuação."""
    text = _CODE_FENCE_RE.sub(" ", content)
    text = _URL_RE.sub(" ", text)
    text = _PATH_RE.sub(" ", text)
    text = _SLUG_RE.sub(" ", text)
    return text


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "")
file_path = data.get("tool_input", {}).get("file_path", "")

if tool == "Write":
    content = data.get("tool_input", {}).get("content", "")
elif tool == "Edit":
    content = data.get("tool_input", {}).get("new_string", "")
else:
    sys.exit(0)

if not content or not file_path:
    sys.exit(0)

ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
if ext not in ("html", "htm", "md", "txt", "mdx"):
    sys.exit(0)

CHECKS = [
    (r"\bnao\b", "não"),
    (r"\bvoce\b", "você"),
    (r"codigo", "código"),
    (r"producao", "produção"),
    (r"lancamento", "lançamento"),
    (r"\bpratica\b", "prática"),
    (r"numero", "número"),
    (r"servico", "serviço"),
    (r"automacao", "automação"),
    (r"inteligencia", "inteligência"),
    (r"\bnegocio", "negócio"),
    (r"operacoes", "operações"),
    (r"conteudo", "conteúdo"),
    (r"\bunico\b", "único"),
    (r"estrategico", "estratégico"),
    (r"estagiario", "estagiário"),
    (r"disponivel", "disponível"),
    (r"impossivel", "impossível"),
    (r"criterios", "critérios"),
    (r"cenarios", "cenários"),
    (r"validacao", "validação"),
    (r"simulacao", "simulação"),
    (r"orquestracao", "orquestração"),
    (r"decisoes", "decisões"),
    (r"\bgenerico", "genérico"),
    (r"\bpublico\b", "público"),
    (r"\bninguem\b", "ninguém"),
    (r"\btambem\b", "também"),
    (r"\balem\b", "além"),
    (r"\banalise\b", "análise"),
    (r"construcao", "construção"),
    (r"\bpagina\b", "página"),
    (r"informacao", "informação"),
    (r"\barea\b", "área"),
    (r"solucao", "solução"),
    (r"funcao\b", "função"),
    (r"educacao", "educação"),
    (r"\bsalario", "salário"),
    (r"\bpreco\b", "preço"),
]

errors = []
content_lower = _strip_technical(content).lower()
for pattern, correct in CHECKS:
    m = re.search(pattern, content_lower)
    if m:
        errors.append(f'  "{m.group()}" -> "{correct}"')

if errors:
    fname = file_path.split("/")[-1]
    lines = ["ACENTOS FALTANDO em " + fname + ":"] + errors[:10]
    if len(errors) > 10:
        lines.append(f"  ... e mais {len(errors) - 10} palavras")
    lines.append("Corrija os acentos/cedilhas antes de salvar.")
    result = {
        "decision": "block",
        "reason": "\n".join(lines),
    }
    print(json.dumps(result))

sys.exit(0)
