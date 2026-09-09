#!/usr/bin/env python3
"""
Activation Sprint Reminder — envia email REAL via SMTP Gmail.
Substitui Cloud Routine draft-only (que criava rascunho invisível na inbox).

Cron sugerido: 15 12 * * 1,3,5  (SEG/QUA/SEX 12:15 UTC = 09:15 BRT)
Env: ~/_secrets/sprint-reminder.env (chmod 600)
  GMAIL_USER=voce@example.com
  GMAIL_APP_PASSWORD=<16-char app password de https://myaccount.google.com/apppasswords>

Para concluir sprint: editar este arquivo (DELIVERED += 1, remover linha de PENDING) ou
remover linha do cron. Se DEADLINE passou, script sai sem enviar.
"""

from __future__ import annotations

import smtplib
import ssl
import sys
from datetime import date
from email.message import EmailMessage
from pathlib import Path

ENV_FILE = Path.home() / "_secrets" / "sprint-reminder.env"
LOG_TAG = "[sprint-reminder]"

DEADLINE = date(2026, 5, 26)
TO = "voce@example.com"
TOTAL_AGENTS = 9

PENDING = [
    ("@rag-architect",      "fórmula canônica freshness CORTEX"),
    ("@knowledge-builder",  "documentar fórmulas atuais CORTEX"),
    ("@offer-engineer",     "audit oferta evento 7 cidades (Hormozi $100M)"),
    ("@challenge-funnel",   "audit 12 pilares pré-campanha"),
    ("@growth-hacker",      "reverse engineer top 10 Reels"),
    ("@cold-outreach",      "playbook outreach freelancer IA"),
    ("@contract-analyst",   "audit contrato CLIENTE_EXEMPLO + template DOMINA"),
]


def load_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        sys.stderr.write(
            f"{LOG_TAG} env ausente: {ENV_FILE}. Crie com GMAIL_USER e GMAIL_APP_PASSWORD (chmod 600).\n"
        )
        sys.exit(2)
    creds: dict[str, str] = {}
    for raw in ENV_FILE.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        creds[k.strip()] = v.strip().strip('"').strip("'")
    for required in ("GMAIL_USER", "GMAIL_APP_PASSWORD"):
        if not creds.get(required):
            sys.stderr.write(f"{LOG_TAG} env incompleto: faltou {required}\n")
            sys.exit(2)
    return creds


def build_message(creds: dict[str, str]) -> tuple[EmailMessage, str]:
    today = date.today()
    days_left = (DEADLINE - today).days
    delivered = TOTAL_AGENTS - len(PENDING)
    subject = f"[Activation Sprint D-{days_left}] Invoque @workflow-orchestrator localmente"

    lines = [
        f"Sprint Activation — D-{days_left} até {DEADLINE.isoformat()}. "
        f"Status: {delivered}/{TOTAL_AGENTS} entregue.",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"AGENTES PENDENTES ({len(PENDING)}/{TOTAL_AGENTS})",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]
    for agent, mission in PENDING:
        lines.append(f"• {agent:<22} → {mission}")
    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "AÇÃO AGORA — cole na sessão Claude local:",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "@workflow-orchestrator *task activation-sprint-pull. "
        "Leia ~/cortex/vault/projects/agent-activation-sprint-2026-05.md seção Reboot 19-Mai "
        "e ~/broadcast/mailbox/workflow-orchestrator.json msg_20260519_reboot. "
        "Invoque cada agente pendente via Agent tool. Colete entregáveis. "
        "Gere ~/cortex/reports/activation-sprint-progress-{data}.md",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "Responda SKIP se hoje não dá. DONE se sprint concluído (eu desabilito o cron).",
    ]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = creds["GMAIL_USER"]
    msg["To"] = TO
    msg.set_content("\n".join(lines))
    return msg, subject


def send(msg: EmailMessage, creds: dict[str, str]) -> None:
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as smtp:
        smtp.login(creds["GMAIL_USER"], creds["GMAIL_APP_PASSWORD"])
        smtp.send_message(msg)


def main() -> None:
    today = date.today()
    days_left = (DEADLINE - today).days
    if days_left < 0:
        print(f"{LOG_TAG} sprint passou de {DEADLINE} — nada a enviar.")
        return
    if not PENDING:
        print(f"{LOG_TAG} 0 pendências — sprint concluído. Edite/remova cron.")
        return
    creds = load_env()
    msg, subject = build_message(creds)
    send(msg, creds)
    print(f"{LOG_TAG} {today.isoformat()} ENVIADO: {subject}")


if __name__ == "__main__":
    main()
