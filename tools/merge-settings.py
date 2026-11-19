#!/usr/bin/env python3
"""
merge-settings.py — mescla o settings.template.json no ~/.claude/settings.json.

Uso: python3 tools/merge-settings.py <settings.json> <settings.template.json> <pasta-backup>

Rotina única, chamada pelo install.sh e pelo upgrade.sh. Até 19-Nov-2026 só o upgrade.sh
mesclava: o install.sh, ao encontrar um settings.json (todo mundo que já usou o Claude
Code tem um), salvava o template ao lado e pedia mescla manual. A instalação "passava"
com zero hooks registrados.

Regras: bloco `hooks` do template substitui inteiro; permissões são união; `model`,
`language`, `effortLevel` e `alwaysThinkingEnabled` só entram se ausentes; o resto do
arquivo do usuário (plugins, env, MCPs) fica como está.
"""
import json, sys, os, shutil

atual_p, novo_p, backup = sys.argv[1], sys.argv[2], sys.argv[3]

try:
    novo = json.load(open(novo_p, encoding="utf-8"))
except Exception as e:
    print(f"  ! nao consegui ler o template ({e})"); sys.exit(0)

if not os.path.exists(atual_p):
    shutil.copy(novo_p, atual_p)
    print("  ✓ settings.json criado a partir do template")
    sys.exit(0)

try:
    atual = json.load(open(atual_p, encoding="utf-8"))
except Exception:
    shutil.copy(atual_p, os.path.join(backup, "settings.json.ilegivel"))
    shutil.copy(novo_p, atual_p)
    print("  ! settings.json anterior estava ilegivel — substituido (copia no backup)")
    sys.exit(0)

mudou = []

# hooks: o bloco da v7.15 substitui inteiro. Mesclar item a item produz
# duplicata (o mesmo hook registrado 2x) e deixa hook morto de versao antiga.
if atual.get("hooks") != novo.get("hooks"):
    atual["hooks"] = novo["hooks"]
    mudou.append("hooks (router, gates, coach) registrados")

# model: sem isto, herda-se o modelo mais caro por padrao
if not atual.get("model"):
    atual["model"] = novo.get("model", "sonnet")
    mudou.append(f'model = "{atual["model"]}"')

# permissoes: uniao — o que voce liberou continua liberado
pa = atual.setdefault("permissions", {})
pn = novo.get("permissions", {})
for chave in ("allow", "deny", "ask"):
    if chave in pn:
        antes = list(pa.get(chave, []))
        pa[chave] = list(dict.fromkeys(antes + pn[chave]))
        if len(pa[chave]) != len(antes):
            mudou.append(f"permissions.{chave}: +{len(pa[chave]) - len(antes)}")

for chave in ("language", "effortLevel", "alwaysThinkingEnabled"):
    if chave in novo and chave not in atual:
        atual[chave] = novo[chave]
        mudou.append(chave)

json.dump(atual, open(atual_p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
if mudou:
    for m in mudou:
        print(f"  ✓ {m}")
else:
    print("  ✓ settings.json ja estava atualizado")
