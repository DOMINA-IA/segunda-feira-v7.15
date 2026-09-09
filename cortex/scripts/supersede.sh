#!/bin/bash
# =============================================================================
# CORTEX supersede.sh — Bi-Temporal Model (Absorção #2 inspirada em Zep)
#
# Marca nota antiga como SUPERSEDED por uma nova nota. Mantém histórico
# completo: a nota antiga não é deletada, apenas marcada com valid_until.
#
# Uso:
#   ~/cortex/scripts/supersede.sh --old OLD_ID --new NEW_ID [--reason "texto"]
#
# Efeitos:
#   1. Nota antiga: adiciona valid_until=$(now), status=superseded
#   2. Cria edge "supersedes" do new_id → old_id no grafo
#   3. Rebuild index
#
# Permite query histórica: "como estava em data X" via valid_from + valid_until.
# =============================================================================

set -euo pipefail

OLD_ID=""
NEW_ID=""
REASON="superseded by newer note"

while [[ $# -gt 0 ]]; do
  case $1 in
    --old) OLD_ID="$2"; shift 2;;
    --new) NEW_ID="$2"; shift 2;;
    --reason) REASON="$2"; shift 2;;
    *) echo "Argumento desconhecido: $1"; exit 1;;
  esac
done

if [[ -z "$OLD_ID" || -z "$NEW_ID" ]]; then
  echo "Uso: supersede.sh --old OLD_ID --new NEW_ID [--reason 'texto']"
  echo ""
  echo "Marca OLD_ID como superseded por NEW_ID. Adiciona valid_until na antiga"
  echo "e cria edge 'supersedes' no grafo CORTEX. Útil quando um fato muda no"
  echo "tempo (ex: benchmark CPL antigo vs novo)."
  exit 1
fi

VAULT_DIR="$HOME/cortex/vault"

# Localizar arquivos das notas (busca recursiva)
OLD_FILE=$(find "$VAULT_DIR" -name "${OLD_ID}.md" -type f 2>/dev/null | head -1)
NEW_FILE=$(find "$VAULT_DIR" -name "${NEW_ID}.md" -type f 2>/dev/null | head -1)

if [[ -z "$OLD_FILE" ]]; then
  echo "❌ Nota OLD não encontrada: ${OLD_ID}"
  echo "   Procurada em: $VAULT_DIR"
  exit 1
fi

if [[ -z "$NEW_FILE" ]]; then
  echo "❌ Nota NEW não encontrada: ${NEW_ID}"
  echo "   Procurada em: $VAULT_DIR"
  exit 1
fi

echo "▶ Old: $OLD_FILE"
echo "▶ New: $NEW_FILE"

# Atualizar frontmatter da nota antiga via Python (PyYAML para parser robusto)
python3 << PYTHON_EDIT
import yaml
import sys
from datetime import datetime, timezone
from pathlib import Path

old_path = Path("${OLD_FILE}")
content = old_path.read_text()

if not content.startswith("---"):
    print("⚠️  Nota antiga sem frontmatter YAML — pulando supersede de metadata")
    sys.exit(0)

parts = content.split("---", 2)
if len(parts) < 3:
    print("⚠️  Frontmatter mal formado")
    sys.exit(1)

try:
    fm = yaml.safe_load(parts[1]) or {}
except Exception as e:
    print(f"❌ Erro ao parsear YAML: {e}")
    sys.exit(1)

now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# Bi-temporal fields
fm["valid_until"] = now_iso
fm["status"] = "superseded"
fm["superseded_by"] = "${NEW_ID}"
fm["supersede_reason"] = """${REASON}"""

# Manter valid_from se já existe; senão usar created
if "valid_from" not in fm and "created" in fm:
    fm["valid_from"] = fm["created"]

new_yaml = yaml.dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=False)
new_content = f"---\n{new_yaml}---{parts[2]}"

old_path.write_text(new_content)
print(f"✅ Metadados bi-temporais atualizados em {old_path.name}")
print(f"   valid_until: {now_iso}")
print(f"   status: superseded")
print(f"   superseded_by: ${NEW_ID}")
PYTHON_EDIT

# Criar edge no grafo: NEW supersedes OLD
echo ""
echo "▶ Criando edge no grafo: ${NEW_ID} supersedes ${OLD_ID}"
python3 ~/cortex/scripts/cortex_engine.py link "${NEW_ID}" "${OLD_ID}" "supersedes"

# Rebuild index
echo ""
echo "▶ Reconstruindo índices..."
python3 ~/cortex/scripts/cortex_engine.py build-index 2>&1 | tail -5

echo ""
echo "✅ Supersede concluído:"
echo "   ${OLD_ID}  →  superseded by  →  ${NEW_ID}"
echo "   Razão: ${REASON}"
echo ""
echo "💡 Para consultar histórico: cortex_engine.py query --include-historical"
