#!/usr/bin/env python3
"""
preflight-stop.py — Hook Stop para pre-check de pendências antes de fechar sessão.

Detecta padrões que viram "EROS verde mas trabalho pendente":
  1. Edits em arquivos gerados por scripts (~/patterns/*-inema.md sem *-EXTRA / *-delta-)
  2. Alerts em mailboxes criados sem evidência de cortex_engine.py query precedente
  3. Sinais críticos no broadcast sem ação registrada

Output:
  - Stderr: checklist visível na sessão atual
  - Persistido: ~/.claude/.last-preflight.json (consumido pelo cortex-auto.py
    no próximo UserPromptSubmit para reinjetar contexto se houver pendência)

NÃO bloqueia Stop. Hook que falha não quebra Claude Code (exit 0 sempre).

Origem: heurística @sf-master 10-Mai-2026 — "EROS verde ≠ tudo executado".
"""

import json
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
PATTERNS_DIR = HOME / "patterns"
MAILBOX_DIR = HOME / "broadcast" / "mailbox"
SIGNALS_FILE = HOME / "broadcast" / "signals.json"
PREFLIGHT_OUTPUT = HOME / ".claude" / ".last-preflight.json"

SESSION_MINUTES = 90  # janela do que conta como "nesta sessão"
MAX_FINDINGS = 8


def recently_modified(path: Path, minutes: int = SESSION_MINUTES) -> bool:
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return mtime > datetime.now() - timedelta(minutes=minutes)


def find_recent_files(directory: Path, pattern: str = "*", minutes: int = SESSION_MINUTES) -> list:
    if not directory.exists():
        return []
    cutoff = datetime.now() - timedelta(minutes=minutes)
    return [
        p for p in directory.glob(pattern)
        if p.is_file() and datetime.fromtimestamp(p.stat().st_mtime) > cutoff
    ]


def check_generated_file_edits() -> list:
    """Edits em ~/patterns/*-inema.md (regenerados por synthesize_agents.py)."""
    findings = []
    for f in find_recent_files(PATTERNS_DIR, "*-inema.md"):
        if "-EXTRA" in f.name or "-delta-" in f.name or "-extra" in f.name:
            continue
        findings.append({
            "type": "generated_file_edit",
            "severity": "warning",
            "file": str(f),
            "message": (
                f"Edit recente em {f.name} pode ser sobrescrito por "
                f"synthesize_agents.py. Considere mover customizações para "
                f"{f.stem.replace('-inema', '-inema-EXTRA')}.md."
            ),
        })
    return findings[:MAX_FINDINGS]


def check_alerts_without_cortex_evidence() -> list:
    """Alerts criados em mailboxes recentes sem evidência de query CORTEX."""
    findings = []
    cutoff = datetime.now() - timedelta(minutes=SESSION_MINUTES)
    for mb_file in find_recent_files(MAILBOX_DIR, "*.json"):
        try:
            data = json.loads(mb_file.read_text())
            inbox = data.get("inbox") if isinstance(data, dict) else data
            if not isinstance(inbox, list):
                continue
            for msg in inbox:
                if not isinstance(msg, dict):
                    continue
                if msg.get("type") != "alert":
                    continue
                ts = msg.get("timestamp", "")
                try:
                    msg_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    msg_time = msg_time.replace(tzinfo=None)
                except Exception:
                    continue
                if msg_time < cutoff:
                    continue
                findings.append({
                    "type": "alert_without_cortex_check",
                    "severity": "info",
                    "mailbox": mb_file.stem,
                    "subject": msg.get("subject", "")[:80],
                    "message": (
                        f"Alert recente em @{mb_file.stem}: '{msg.get('subject', '')[:60]}'. "
                        f"Considere `cortex_engine.py query` sobre o tópico — "
                        f"pode já estar resolvido em sessão anterior."
                    ),
                })
                if len(findings) >= MAX_FINDINGS:
                    return findings
        except Exception:
            continue
    return findings


def check_unrouted_signals() -> list:
    """Sinais com risk:high não roteados nas últimas N min."""
    findings = []
    if not SIGNALS_FILE.exists():
        return findings
    try:
        signals = json.loads(SIGNALS_FILE.read_text())
        if not isinstance(signals, list):
            return findings
        cutoff = datetime.now() - timedelta(minutes=SESSION_MINUTES)
        for sig in signals:
            if not isinstance(sig, dict):
                continue
            if sig.get("routed") or sig.get("expired"):
                continue
            if (sig.get("risk") or "").lower() != "high":
                continue
            ts = sig.get("created_at") or sig.get("timestamp", "")
            try:
                sig_time = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                if sig_time < cutoff:
                    continue
            except Exception:
                continue
            findings.append({
                "type": "unrouted_high_risk_signal",
                "severity": "warning",
                "signal_id": sig.get("id", ""),
                "signal_type": sig.get("type", ""),
                "message": (
                    f"Sinal {sig.get('type', '?')} com risk:high não roteado. "
                    f"Considere rodar signal-router.py manualmente ou aguardar próximo cron."
                ),
            })
            if len(findings) >= 3:
                break
    except Exception:
        pass
    return findings


def check_blocked_by_human_without_audit() -> list:
    """Detecta 'depende de você/CEO/UI' SOMENTE em seções Status/Pendências.

    Heurística meta da sessão 10-Mai: 5 falsos-positivos de 'precisa humano'
    porque não auditei capacidades disponíveis. Refinamento (mesma sessão):
    olhar SÓ headings explícitos de status — texto de heurística sobre o
    padrão NÃO conta como ocorrência ativa.
    """
    findings = []
    cortex_projects = Path.home() / "cortex" / "vault" / "projects"
    if not cortex_projects.exists():
        return findings
    cutoff = datetime.now() - timedelta(minutes=SESSION_MINUTES)
    # Padrões de heading que indicam seção operacional de pendência
    status_headings = re.compile(
        r"^#{1,4}\s+(status|pendências?|pendente|aguardando|bloqueio|depende|"
        r"a fazer|próximos passos|to-?do|aberto)",
        re.IGNORECASE | re.MULTILINE,
    )
    # Padrões dentro da seção que indicam dependência humana ATIVA
    active_markers = re.compile(
        r"(precisa do ceo|aguarda ceo|ceo precisa|ready_for_human|"
        r"via ui|manual via ui|bloqueio:.{0,40}humano)",
        re.IGNORECASE,
    )
    for f in cortex_projects.glob("*.md"):
        if not f.is_file():
            continue
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        # Quebra em seções por heading
        sections = re.split(r"^(#{1,4}\s+.+)$", content, flags=re.MULTILINE)
        # sections alterna: [pre-heading, heading1, conteudo1, heading2, conteudo2, ...]
        for i in range(1, len(sections) - 1, 2):
            heading = sections[i]
            body = sections[i + 1] if i + 1 < len(sections) else ""
            if not status_headings.match(heading):
                continue
            if active_markers.search(body):
                findings.append({
                    "type": "blocked_by_human_unaudited",
                    "severity": "warning",
                    "file": str(f),
                    "section": heading.strip()[:60],
                    "message": (
                        f"'{f.name}' marca dependência humana em '{heading.strip()[:40]}' — "
                        f"audite skill/tool/list disponível antes de declarar bloqueado."
                    ),
                })
                if len(findings) >= 3:
                    return findings
                break  # 1 hit por arquivo basta
    return findings


def check_create_without_list() -> list:
    """Detecta 'create' de recurso sem 'list' precedente (CORTEX, GitHub, Routines).

    Heurística meta: ao criar routine/repo/skill, sempre listar existentes
    antes — evita duplicação como aconteceu com Daily Health Check
    sobreposta a proactive-monitor existente.
    """
    # Hook não tem acesso a histórico tool-calls; sinaliza preventivamente
    # quando detecta arquivos novos com timestamp muito próximo.
    findings = []
    cortex_dirs = [
        Path.home() / "cortex" / "vault" / "playbooks",
        Path.home() / "cortex" / "vault" / "projects",
    ]
    cutoff = datetime.now() - timedelta(minutes=SESSION_MINUTES)
    for d in cortex_dirs:
        if not d.exists():
            continue
        new_files = [
            p for p in d.glob("*.md")
            if datetime.fromtimestamp(p.stat().st_ctime) > cutoff
            and datetime.fromtimestamp(p.stat().st_ctime) ==
                datetime.fromtimestamp(p.stat().st_mtime)  # criado, não editado
        ]
        if len(new_files) >= 2:
            findings.append({
                "type": "multiple_creates_without_audit",
                "severity": "info",
                "count": len(new_files),
                "directory": str(d),
                "message": (
                    f"{len(new_files)} arquivos criados em {d.name} "
                    f"nesta sessão — audite se há overlap com existentes "
                    f"(rodar audit_ids ou cortex_engine query antes)."
                ),
            })
            break
    return findings


def main():
    findings = []
    try:
        findings.extend(check_generated_file_edits())
        findings.extend(check_alerts_without_cortex_evidence())
        findings.extend(check_unrouted_signals())
        findings.extend(check_blocked_by_human_without_audit())
        findings.extend(check_create_without_list())
    except Exception:
        # Hook nunca quebra
        return 0

    if not findings:
        # Limpa preflight anterior se existia
        if PREFLIGHT_OUTPUT.exists():
            try:
                PREFLIGHT_OUTPUT.unlink()
            except Exception:
                pass
        return 0

    # Persiste para próxima sessão
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "findings_count": len(findings),
        "findings": findings,
    }
    try:
        PREFLIGHT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        PREFLIGHT_OUTPUT.write_text(
            json.dumps(output_data, indent=2, ensure_ascii=False)
        )
    except Exception:
        pass

    # Stderr para visibilidade na sessão atual
    print("\n[Pre-Flight] Pendências detectadas:", file=sys.stderr)
    for f in findings:
        sev = f.get("severity", "info").upper()
        print(f"  [{sev}] {f.get('message', '')}", file=sys.stderr)
    print(
        f"\n[Pre-Flight] {len(findings)} item(s) salvos em "
        f"{PREFLIGHT_OUTPUT.name} para próxima sessão.\n",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # Falha silenciosa — hook nunca quebra Claude Code
        print(f"preflight-stop.py non-fatal error: {e}", file=sys.stderr)
        sys.exit(0)
