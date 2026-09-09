#!/usr/bin/env python3
"""
CORTEX Auto-Ingest Hook — Detecta aprendizado e sugere ingest.

Roda no evento `Stop` (após assistente terminar de responder).
Analisa o transcript da conversa recente e detecta:
1. Infra alterada (porta, IP, config, deploy)
2. Bug resolvido com workaround
3. Projeto novo ou status alterado
4. Padrão novo descoberto

NÃO ingere automaticamente — imprime sugestão que o assistente pode executar.
Isso é mais seguro que auto-ingest cego.
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime

CORTEX_HOME = Path.home() / "cortex"
INDEX_DIR = CORTEX_HOME / "index"
SCRIPTS_DIR = CORTEX_HOME / "scripts"

# Importar session tracker
sys.path.insert(0, str(SCRIPTS_DIR))
try:
    from session_tracker import save_session
    SESSION_AVAILABLE = True
except ImportError:
    SESSION_AVAILABLE = False

# Ler transcript do stdin
try:
    transcript = sys.stdin.read().strip()
except:
    transcript = ""

if not transcript or len(transcript) < 100:
    sys.exit(0)

transcript_lower = transcript.lower()
suggestions = []

# ─── Detectores de Aprendizado ──────────────────────────────────

# 1. Alteração de infra (porta, IP, config)
infra_patterns = [
    (r'porta\s+(\d{2,5})', "porta alterada"),
    (r'mudou?\s+(?:a\s+)?porta', "porta alterada"),
    (r'ip\s+(?:novo|alterado|mudou)', "IP alterado"),
    (r'pm2\s+(?:restart|start|stop|delete)', "PM2 service changed"),
    (r'nginx\s+(?:reload|restart|config)', "nginx config changed"),
    (r'deploy\s+(?:completo|sucesso|feito|ok)', "deploy realizado"),
    (r'ssh\s+.*?(?:configurado|alterado)', "SSH config changed"),
]

for pattern, label in infra_patterns:
    if re.search(pattern, transcript_lower):
        suggestions.append({
            "type": "infra",
            "reason": label,
            "action": f"Verificar e atualizar notas de infra no CORTEX: `python3 ~/cortex/scripts/cortex_engine.py query \"infra porta\"`"
        })
        break  # 1 sugestão de infra é suficiente

# 2. Bug resolvido / workaround encontrado
bug_patterns = [
    (r'(?:bug|erro|error|fix|corrigido|resolvido|workaround|solução)', "bug/workaround"),
    (r'(?:o problema era|a causa era|descobri que|o erro estava)', "root cause found"),
]

bug_matches = sum(1 for p, _ in bug_patterns if re.search(p, transcript_lower))
if bug_matches >= 2:  # Precisa de 2+ indicadores para evitar falso positivo
    suggestions.append({
        "type": "feedback",
        "reason": "bug resolvido ou workaround encontrado",
        "action": "Considere criar nota feedback: `~/cortex/scripts/ingest.sh --title \"Fix: [descrição]\" --type feedback --tags bug fix`"
    })

# 3. Campanha criada/pausada/alterada
campaign_patterns = [
    (r'campanha\s+(?:criada|pausada|ativada|duplicada|lançada)', "campanha alterada"),
    (r'(?:cpl|roas|ctr)\s*[:=]\s*[\d.,]+', "métricas de campanha"),
    (r'meta\s+ads?\s+(?:criou|pausou|ativou)', "ação Meta Ads"),
]

for pattern, label in campaign_patterns:
    if re.search(pattern, transcript_lower):
        suggestions.append({
            "type": "project",
            "reason": label,
            "action": "Atualizar nota do projeto no CORTEX e registrar resultado no feedback loop"
        })
        break

# 4. Novo projeto ou configuração significativa
project_patterns = [
    (r'projeto\s+(?:novo|criado|iniciado)', "novo projeto"),
    (r'(?:iniciei|começamos|criamos)\s+(?:o|um|novo)', "novo trabalho"),
    (r'(?:domínio|subdomínio)\s+(?:configurado|apontado|criado)', "domínio configurado"),
]

for pattern, label in project_patterns:
    if re.search(pattern, transcript_lower):
        suggestions.append({
            "type": "project",
            "reason": label,
            "action": "Criar nota de projeto: `~/cortex/scripts/ingest.sh --title \"[Nome]\" --type project`"
        })
        break

# 5. Padrão aprendido (heurística)
pattern_indicators = [
    (r'(?:aprendi que|descobri que|lição|takeaway|importante lembrar)', "aprendizado explícito"),
    (r'(?:sempre|nunca)\s+(?:fazer|usar|verificar|checar)', "heurística detectada"),
    (r'(?:da próxima vez|no futuro|para lembrar)', "nota para futuro"),
]

for pattern, label in pattern_indicators:
    if re.search(pattern, transcript_lower):
        suggestions.append({
            "type": "pattern",
            "reason": label,
            "action": "Criar nota de padrão: `~/cortex/scripts/ingest.sh --title \"Pattern: [descrição]\" --type pattern`"
        })
        break

# ─── Output ──────────────────────────────────────────────────────

# ─── 6. Salvar sessão automaticamente ────────────────────────────

if SESSION_AVAILABLE and len(transcript) > 300:
    try:
        save_session(transcript)
    except Exception:
        pass

# ─── Output ──────────────────────────────────────────────────────

if suggestions:
    # Deduplicate by type
    seen_types = set()
    unique = []
    for s in suggestions:
        if s["type"] not in seen_types:
            seen_types.add(s["type"])
            unique.append(s)

    lines = ["[CORTEX Auto-Ingest — aprendizado detectado na conversa]"]
    for s in unique[:3]:  # Max 3 sugestões
        lines.append(f"  ⚡ {s['reason']} ({s['type']})")
        lines.append(f"     → {s['action']}")
    lines.append("Avalie se vale atualizar o CORTEX com esses aprendizados.")
    print("\n".join(lines))
