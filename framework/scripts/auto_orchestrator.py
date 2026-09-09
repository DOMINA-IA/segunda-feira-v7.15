#!/usr/bin/env python3
"""
Auto Orchestrator — Briefing Matinal Proativo (Nível 1).

Roda toda manhã (cron 07:33 BRT). Faz:
1. Lê estado atual: WIP do CORTEX, decisões pendentes, sinais ativos.
2. Mapeia cada item para o agente mais apropriado (usa KEYWORD_TO_AGENT).
3. Invoca top 3 agentes via API local (/api/agents/{name}/ask).
4. Consolida resultados em ~/.cache/sf-morning-DATA.md.
5. Daily Briefing (.zshrc) lê esse arquivo e mostra resumo na próxima abertura de terminal.

Custo aproximado: 3 chamadas Claude Sonnet/dia (~R$0,15/dia).
"""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

import requests

# Importar agent_router pra reusar KEYWORD_TO_AGENT + detect
SF_DIR = Path.home() / "Desktop" / "segunda-feira-jarvis"
sys.path.insert(0, str(SF_DIR))

try:
    from agent_router import detect_agent_by_keywords
except ImportError as e:
    print(f"❌ Não consegui importar agent_router: {e}")
    sys.exit(1)

SEGUNDA_HOST = "http://localhost:8341"
HOME = Path.home()
CACHE_DIR = HOME / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
TODAY = datetime.now().strftime("%Y-%m-%d")
CACHE_FILE = CACHE_DIR / f"sf-morning-{TODAY}.md"
CACHE_LATEST = CACHE_DIR / "sf-morning-latest.md"


# ─── Coleta de contexto ──────────────────────────────────────────────────────

def _stringify_wip_item(x) -> str:
    """Extrai texto legível de um item de WIP (que pode ser dict, str, etc)."""
    if isinstance(x, str):
        return x[:120]
    if isinstance(x, dict):
        for key in ("description", "title", "text", "content", "summary"):
            v = x.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()[:120]
        return str(x)[:120]
    return str(x)[:120]


def load_wip() -> list[str]:
    """WIP do CORTEX — itens em progresso."""
    candidates = [
        HOME / "cortex" / "wip" / "active.json",
        HOME / "cortex" / "wip" / "current.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                items = d if isinstance(d, list) else d.get("items", []) if isinstance(d, dict) else []
                cleaned = [_stringify_wip_item(x) for x in items]
                # Filtrar fragmentos com 'nn' (artefato de quebra de linha do CORTEX)
                cleaned = [c for c in cleaned if c and len(c) >= 10]
                return cleaned
            except Exception:
                continue
    return []


def load_decisions() -> list[dict]:
    p = HOME / "cortex" / "decisions" / "active.json"
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            return d.get("decisions", [])
        except Exception:
            return []
    return []


def load_signals() -> list[dict]:
    p = HOME / "broadcast" / "signals.json"
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(d, list):
                return [s for s in d if not s.get("consumed")]
        except Exception:
            return []
    return []


# ─── Identificação de agentes relevantes ─────────────────────────────────────

def pick_agents_for_context(wip: list, decisions: list, signals: list, top: int = 3) -> list[str]:
    """Identifica os agentes mais relevantes pro estado atual."""
    pieces = []
    pieces.extend(wip[:10])
    pieces.extend(d.get("description", "") for d in decisions)
    pieces.extend(s.get("action", s.get("type", "")) for s in signals)
    text = " ".join(p for p in pieces if p)

    if text.strip():
        suggestions = detect_agent_by_keywords(text, top_n=top * 2)
        chosen = [s["agent"] for s in suggestions if s["confidence"] >= 0.65][:top]
        if chosen:
            return chosen

    # Fallback: trio de generalistas + adversário
    return ["analyst", "advogado-do-diabo", "market-intel"]


def build_question(agent: str, wip: list, decisions: list) -> str:
    """Pergunta especializada por agente, contextualizada pelo WIP."""
    wip_brief = "; ".join(str(w)[:60] for w in wip[:3]) or "sem WIP carregado"

    library = {
        "tool-curator": (
            f"Olhando minhas pendências ({wip_brief}), em 3 frases: "
            "que ferramenta nova vale adotar nesta semana e qual estou subutilizando?"
        ),
        "market-intel": (
            "Em 3 frases curtas: qual a tendência mais relevante esta semana no nicho IA/mentoria Brasil "
            "e como isso afeta o posicionamento da DOMINA.IA?"
        ),
        "advogado-do-diabo": (
            f"Meu WIP atual inclui: {wip_brief}. "
            "Em 3 frases: aponte os 3 riscos invisíveis nessas pendências."
        ),
        "analyst": (
            f"Resumo executivo em 3 frases sobre meu estado atual: {wip_brief}. "
            "O que merece atenção primeiro?"
        ),
        "traffic": (
            "Olhando minhas campanhas ativas, em 3 frases: o que está performando, "
            "o que precisa pausar e qual o próximo movimento?"
        ),
        "creative-director": (
            "Em 3 frases: sugira 1 ângulo de criativo novo baseado em hooks já validados. "
            "Direto, sem teoria."
        ),
        "growth-hacker": (
            "Em 3 frases: qual mudança recente no algoritmo de Reels/IG eu deveria explorar esta semana?"
        ),
        "launch-strategist": (
            f"Estado: {wip_brief}. Em 3 frases: tenho lançamento/desafio pendente? "
            "Sugira 1 movimento pra essa semana."
        ),
        "fabio-soares": (
            f"Olhando meu estado ({wip_brief}), em 3 frases: aponte 1 fragilidade no método e 1 ação corretiva."
        ),
        "offer-engineer": (
            "Em 3 frases: olhando minha oferta atual da DOMINA.IA, "
            "qual elemento (preço, garantia, bônus, urgência) está mais fraco?"
        ),
        "cold-outreach": (
            "Em 3 frases: como otimizar meu próximo cold outreach B2B esta semana?"
        ),
        "challenge-funnel": (
            "Em 3 frases: avalie se minha próxima ação se encaixa no método 7.11.4 e o que ajustar."
        ),
        "video-producer": (
            "Em 3 frases: qual formato de vídeo curto eu deveria produzir esta semana pra DOMINA.IA?"
        ),
        "knowledge-builder": (
            "Em 3 frases: qual área do meu conhecimento está mais desorganizada e merece estruturação?"
        ),
    }
    return library.get(
        agent,
        f"Em 3 frases: olhando o contexto ({wip_brief}), o que você acha mais importante pra eu resolver hoje?",
    )


# ─── Invocação dos agentes ───────────────────────────────────────────────────

def ask_agent_local(agent_name: str, question: str) -> str:
    """Chama API local da Segunda-feira para invocar a persona."""
    try:
        r = requests.post(
            f"{SEGUNDA_HOST}/api/agents/{agent_name}/ask",
            json={"question": question, "max_tokens": 300},
            timeout=60,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("response", "(resposta vazia)").strip()
        return f"(HTTP {r.status_code}: {r.text[:100]})"
    except requests.exceptions.ConnectionError:
        return "(❌ Segunda-feira não está rodando — start-backend.sh)"
    except Exception as e:
        return f"(erro: {e})"


# ─── Decisões vencidas ───────────────────────────────────────────────────────

def overdue_decisions(decisions: list) -> list[dict]:
    today = date.today()
    out = []
    for d in decisions:
        try:
            verify = datetime.strptime(d.get("verify_at", ""), "%Y-%m-%d").date()
            if verify <= today and d.get("status") == "pending":
                out.append(d)
        except Exception:
            continue
    return out


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print(f"🌅 Auto Orchestrator — {datetime.now().strftime('%H:%M:%S')}")

    wip = load_wip()
    decisions = load_decisions()
    signals = load_signals()
    overdue = overdue_decisions(decisions)

    print(f"   WIP: {len(wip)} | Decisões pendentes: {len(decisions)} | Vencidas: {len(overdue)} | Sinais: {len(signals)}")

    agents = pick_agents_for_context(wip, decisions, signals)
    print(f"   Agentes escolhidos: {agents}")

    sections = []
    for agent in agents:
        question = build_question(agent, wip, decisions)
        print(f"   → consultando @{agent}...")
        response = ask_agent_local(agent, question)
        sections.append({"agent": agent, "question": question, "response": response})

    # Montar markdown final
    overdue_md = "\n".join(
        f"- **{d.get('description', '?')[:80]}** (decidida {d.get('made_at', '?')}, "
        f"verificar até {d.get('verify_at', '?')})"
        for d in overdue
    ) or "_(nenhuma decisão vencida)_"

    agents_md = "\n\n".join(
        f"### @{s['agent']}\n\n_{s['question']}_\n\n{s['response']}"
        for s in sections
    )

    body = f"""# 🌅 Briefing Matinal — {datetime.now().strftime('%d/%m/%Y às %H:%M')}

Gerado automaticamente pela Segunda-feira Auto Orchestrator (Nível 1).
Você não precisou pedir nada. 3 agentes consultaram seu contexto e te entregam o resumo abaixo.

---

## ⚠️ Decisões pra verificar hoje

{overdue_md}

---

## 🤖 O que os agentes te trouxeram

{agents_md}

---

_Próximo briefing: amanhã 07:33 BRT. Pra forçar agora: `~/scripts/auto-orchestrator.sh`_
_Pra desligar tudo: comente as linhas no crontab (`crontab -e`)._
"""

    CACHE_FILE.write_text(body, encoding="utf-8")
    if CACHE_LATEST.exists() or CACHE_LATEST.is_symlink():
        CACHE_LATEST.unlink()
    try:
        CACHE_LATEST.symlink_to(CACHE_FILE)
    except Exception:
        CACHE_LATEST.write_text(body, encoding="utf-8")

    print(f"\n✅ Briefing salvo: {CACHE_FILE}")
    print(f"   Latest symlink: {CACHE_LATEST}")
    print(f"\nPrévia (primeiras 25 linhas):")
    print("\n".join(body.splitlines()[:25]))

    # Notificação macOS — alerta visual de que o briefing está pronto
    import subprocess
    notify = HOME / "scripts" / "sf-notify.sh"
    if notify.exists():
        agents_str = ", ".join(f"@{s['agent']}" for s in sections)
        subtitle = f"{agents_str} consultaram seu contexto"
        msg = f"Briefing matinal pronto. {subtitle}. Abra o terminal."
        try:
            subprocess.run(
                [str(notify), "🌅 Briefing matinal pronto", msg, "info"],
                timeout=5, check=False,
            )
        except Exception as e:
            print(f"(notify falhou: {e})")


if __name__ == "__main__":
    main()
