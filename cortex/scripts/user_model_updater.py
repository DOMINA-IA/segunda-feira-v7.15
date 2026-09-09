#!/usr/bin/env python3
"""
user_model_updater.py — Atualização dialética do user-model

Adaptado do conceito Honcho dialectic user modeling (hermes-agent).
Sem dependência de serviço externo (Honcho server). Implementação pura SF.

Dialética:
  TESE     — modelo atual em ~/cortex/vault/user-model/{4 arquivos}
  ANTÍTESE — sinais novos das últimas N sessões (episódios + mailbox + signals)
  SÍNTESE  — modelo atualizado, mudanças qualitativas vão para evolutive-log

Modos:
  --heuristic (default)  — regex-based, $0 (Tier 0)
  --llm                  — Claude Haiku para extração (Tier 1, ~$0.01)
  --dry-run              — só detecta sinais, não escreve

Uso:
    python3 ~/cortex/scripts/user_model_updater.py
    python3 ~/cortex/scripts/user_model_updater.py --days 14 --dry-run
    python3 ~/cortex/scripts/user_model_updater.py --llm --days 30
"""
import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path.home()
USER_MODEL_DIR = HOME / "cortex" / "vault" / "user-model"
EPISODIC_DIR = HOME / "consciousness" / "memory" / "episodic"
SESSIONS_DB = HOME / "cortex" / "sessions.db"
STATE_FILE = HOME / ".claude" / ".user-model-state.json"
META_ADS = HOME / "utm-manager" / "meta_ads.py"
FEEDBACK_LOOP = HOME / "feedback-loop" / "results.json"
SIGNALS = HOME / "broadcast" / "signals.json"
OPS_SNAPSHOT = USER_MODEL_DIR / "ops-snapshot.md"

# Patterns ampliados — capturam sinais REAIS dos episódios SF
DECISION_PATTERNS = [
    r"decis(ão|ões)\s+CEO",
    r"CEO\s+(decidiu|autorizou|aprovou|recusou|pediu)",
    r"${CEO_NAME}\s+(pediu|decidiu|sugeriu|aprovou|recusou)",
    r"autoriz(ado|ou)\s+(roadmap|sprint|absorpção|absorção)",
    r"\bdiretriz\s+CEO",
]

CLIENT_PATTERNS = [
    r"\b(CLIENTE_EXEMPLO|CLIENTE_EXEMPLO_2|CLIENTE_EXEMPLO_3|CLIENTE_EXEMPLO_4|Dominantes)\b",
    r"\bcliente\s+(novo|nova)\b",
    r"\bdiscovery\s+\w+",
    r"\bsprint\s+[A-Z]\s+\w+\s+entregue",
    r"\bmigração\s+\d+\s+aplicada",
]

PREFERENCE_PATTERNS = [
    r"\bsempre\s+(faça|use|prefira|evite|filtrar)",
    r"\bnunca\s+(faça|use|delete)",
    r"\bregra\s+de\s+ouro",
    r"\bbaratear\s+(custo|tokens?|consumo)",
    r"\bnão\s+(absorver|adicionar|fundir)",
    r"\barchive(\s+não\s+delete)?",
    r"\bquando\s+\w+\s+,?\s+(sempre|nunca|fazer)",
    r"\banti-?absorção",
    r"\bheurística:?",
]

STRATEGY_PATTERNS = [
    r"\bpausar?\s+(campanha|tráfego)",
    r"\boferta\s+(nova|atualizada|R\$[\d\.,]+)",
    r"\bsprint\s+(novo|próximo|[A-Z]\s+(complet|conclu))",
    r"\babsor(pção|ção)\s+\w+",
    r"\bvers(ão|ões)?\s+v?\d+\.\d+",
    r"\bbump(ado)?\s+v?\d+\.\d+",
    r"\b(novo|nova)\s+(agente|skill|rule|workflow|hook)\b",
    r"\bframework\s+\w+\s+(pronto|atualizado|otimizado)",
    r"\bcleanup\s+\w+",
]


def gather_ops_snapshot() -> dict:
    """Coleta snapshot OPS de 3 fontes: meta_ads.py (Meta API), feedback-loop, signals."""
    import subprocess
    snapshot = {
        "generated_at": datetime.now().isoformat(),
        "meta_ads": {},
        "feedback_loop": {},
        "signals": {},
        "errors": [],
    }

    # 1. Meta Ads (via subprocess curto)
    if META_ADS.exists():
        try:
            result = subprocess.run(
                ["python3", str(META_ADS), "insights", "--dias", "3"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                snapshot["meta_ads"]["raw_output"] = result.stdout[:2000]
                # Tentar extrair métricas via regex
                m_cpl = re.search(r"CPL[:\s]+R?\$?\s*([\d\.,]+)", result.stdout)
                m_leads = re.search(r"Leads?[:\s]+(\d+)", result.stdout)
                m_spend = re.search(r"(?:Spend|Gasto|Investido)[:\s]+R?\$?\s*([\d\.,]+)", result.stdout)
                if m_cpl:
                    snapshot["meta_ads"]["cpl_3d"] = f"R${m_cpl.group(1)}"
                if m_leads:
                    snapshot["meta_ads"]["leads_3d"] = int(m_leads.group(1))
                if m_spend:
                    snapshot["meta_ads"]["spend_3d"] = f"R${m_spend.group(1)}"
            else:
                snapshot["errors"].append(f"meta_ads stderr: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            snapshot["errors"].append("meta_ads.py timeout (>30s)")
        except Exception as e:
            snapshot["errors"].append(f"meta_ads exception: {e}")
    else:
        snapshot["errors"].append(f"meta_ads.py não existe em {META_ADS}")

    # 2. Feedback loop
    if FEEDBACK_LOOP.exists():
        try:
            fl = json.loads(FEEDBACK_LOOP.read_text())
            summary = {}
            for key, val in fl.items():
                if isinstance(val, dict):
                    summary[key] = {
                        "keys": list(val.keys())[:5],
                        "total_items": sum(
                            len(v) if isinstance(v, list) else 1
                            for v in val.values()
                        ),
                    }
                elif isinstance(val, list):
                    summary[key] = {"count": len(val)}
            snapshot["feedback_loop"] = summary
        except (OSError, json.JSONDecodeError) as e:
            snapshot["errors"].append(f"feedback-loop error: {e}")
    else:
        snapshot["errors"].append("feedback-loop/results.json não existe")

    # 3. Signals
    if SIGNALS.exists():
        try:
            sigs = json.loads(SIGNALS.read_text())
            if isinstance(sigs, dict):
                sigs = sigs.get("signals", []) or []
            if isinstance(sigs, list):
                by_type = Counter(s.get("type", "unknown") for s in sigs)
                by_severity = Counter(s.get("severity", "normal") for s in sigs if isinstance(s, dict))
                snapshot["signals"] = {
                    "total": len(sigs),
                    "by_type": dict(by_type.most_common(10)),
                    "by_severity": dict(by_severity),
                }
                # Top 5 por confidence se houver
                top = sorted(
                    [s for s in sigs if isinstance(s, dict) and "confidence" in s],
                    key=lambda s: s.get("confidence", 0),
                    reverse=True,
                )[:5]
                snapshot["signals"]["top_5_high_confidence"] = [
                    {
                        "type": s.get("type"),
                        "agent": s.get("agent"),
                        "action": (s.get("action") or "")[:80],
                        "confidence": s.get("confidence"),
                    }
                    for s in top
                ]
        except (OSError, json.JSONDecodeError) as e:
            snapshot["errors"].append(f"signals error: {e}")

    return snapshot


def write_ops_snapshot(snapshot: dict):
    """Escreve ops-snapshot.md (overrides — auto-generated, não preserve manual edits)."""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    meta = snapshot.get("meta_ads") or {}
    fl = snapshot.get("feedback_loop") or {}
    sig = snapshot.get("signals") or {}
    errors = snapshot.get("errors") or []

    # Counter de updates (preservar do anterior)
    update_count = 1
    if OPS_SNAPSHOT.exists():
        try:
            existing = OPS_SNAPSHOT.read_text()
            m = re.search(r"update_count:\s*(\d+)", existing)
            if m:
                update_count = int(m.group(1)) + 1
        except OSError:
            pass

    def yaml_dict(d: dict, indent: int = 0) -> str:
        if not d:
            return f"{' ' * indent}(vazio)"
        lines = []
        for k, v in d.items():
            pre = " " * indent
            if isinstance(v, dict):
                lines.append(f"{pre}{k}:")
                lines.append(yaml_dict(v, indent + 2))
            elif isinstance(v, list):
                lines.append(f"{pre}{k}: ({len(v)} items)")
                for item in v[:5]:
                    if isinstance(item, dict):
                        compact = ", ".join(f"{ik}={iv}" for ik, iv in item.items())
                        lines.append(f"{pre}  - {compact[:120]}")
                    else:
                        lines.append(f"{pre}  - {str(item)[:120]}")
            else:
                lines.append(f"{pre}{k}: {v}")
        return "\n".join(lines)

    content = f"""---
id: user-model-ops-snapshot
type: user-model
axis: ops
auto_generated: true
last_updated: {today}
update_count: {update_count}
source: user_model_updater.py (gather_ops_snapshot)
warning: "ARQUIVO AUTO-GERADO — não edite manualmente. Para customização, edite business-context.md (curado)."
---

# OPS Snapshot — Auto-Gerado

> Snapshot operacional capturado em {today}.
> **Para análise curada/qualitativa:** ver [[business-context]] (manual).

## Meta Ads (últimos 3 dias)

```yaml
{yaml_dict(meta) if meta else '(meta_ads.py indisponível ou sem dados)'}
```

## Feedback Loop

```yaml
{yaml_dict({k: v for k, v in fl.items()}) if fl else '(feedback-loop/results.json indisponível)'}
```

## Signals (broadcast)

```yaml
{yaml_dict(sig) if sig else '(signals.json indisponível)'}
```

## Erros na coleta

{chr(10).join(f'- ⚠️ {e}' for e in errors) if errors else '_(nenhum)_'}

## Links

- [[business-context]] — análise curada manual
- [[cognitive-style]] — como CEO interpreta esses números
- [[evolutive-log]] — histórico de mudanças
"""

    OPS_SNAPSHOT.write_text(content, encoding="utf-8")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {"last_run": None, "total_updates": 0, "last_synthesis": None}


def save_state(state: dict):
    state["last_run"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def load_recent_episodes(days: int) -> list:
    """Carrega episódios significativos dos últimos N dias."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    episodes = []
    if not EPISODIC_DIR.exists():
        return episodes
    for jsonl in EPISODIC_DIR.glob("*.jsonl"):
        agent = jsonl.stem
        if agent.startswith(".") or agent in {"autonomous-smoke", "brainstem"}:
            continue
        try:
            with jsonl.open() as f:
                for line in f:
                    try:
                        ep = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    ts = ep.get("timestamp")
                    if not ts:
                        continue
                    try:
                        ep_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        continue
                    if ep_dt < cutoff:
                        continue
                    summary = ep.get("summary", "")
                    if not summary or "tarefa desconhecida" in summary.lower():
                        continue
                    episodes.append({
                        "agent": agent,
                        "timestamp": ts,
                        "summary": summary,
                        "lessons": ep.get("lessons") or {},
                        "result": (ep.get("outcome") or {}).get("result"),
                        "valence": (ep.get("valence") or {}).get("score", 0),
                    })
        except OSError:
            continue
    episodes.sort(key=lambda e: e["timestamp"])
    return episodes


def extract_signals(episodes: list) -> dict:
    """Extrai sinais qualitativos das narratives dos episódios (modo heurístico)."""
    signals = {
        "decisions": [],
        "client_updates": [],
        "preferences": [],
        "strategy_changes": [],
        "agent_activity": Counter(),
        "valence_avg": 0.0,
        "total_episodes": len(episodes),
        "timespan": [
            episodes[0]["timestamp"] if episodes else None,
            episodes[-1]["timestamp"] if episodes else None,
        ],
    }
    if not episodes:
        return signals

    val_sum = 0
    for ep in episodes:
        text = ep["summary"]
        signals["agent_activity"][ep["agent"]] += 1
        val_sum += ep["valence"]
        for pat in DECISION_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                signals["decisions"].append({
                    "ts": ep["timestamp"], "agent": ep["agent"],
                    "summary": text[:200]
                })
                break
        for pat in CLIENT_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                signals["client_updates"].append({
                    "ts": ep["timestamp"], "agent": ep["agent"],
                    "summary": text[:200]
                })
                break
        for pat in PREFERENCE_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                signals["preferences"].append({
                    "ts": ep["timestamp"], "agent": ep["agent"],
                    "summary": text[:200]
                })
                break
        for pat in STRATEGY_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                signals["strategy_changes"].append({
                    "ts": ep["timestamp"], "agent": ep["agent"],
                    "summary": text[:200]
                })
                break
    signals["valence_avg"] = val_sum / len(episodes) if episodes else 0
    return signals


def has_qualitative_change(signals: dict) -> bool:
    """Decide se há mudança qualitativa que justifica update."""
    return (
        len(signals["decisions"]) >= 1
        or len(signals["client_updates"]) >= 2
        or len(signals["preferences"]) >= 1
        or len(signals["strategy_changes"]) >= 2
    )


def append_evolutive_entry(signals: dict, args):
    """Adiciona entry no evolutive-log.md (síntese dialética)."""
    log_path = USER_MODEL_DIR / "evolutive-log.md"
    if not log_path.exists():
        print(f"⚠️  evolutive-log.md não encontrado em {log_path}", file=sys.stderr)
        return

    current = log_path.read_text(encoding="utf-8")
    date_str = datetime.now().strftime("%Y-%m-%d")
    timespan_start = (signals["timespan"][0] or "?")[:10]
    timespan_end = (signals["timespan"][1] or "?")[:10]

    top_agents = ", ".join(
        f"@{a}({n})" for a, n in signals["agent_activity"].most_common(5)
    )

    sample_decisions = "\n".join(
        f"  - {d['agent']} ({d['ts'][:10]}): {d['summary'][:120]}..."
        for d in signals["decisions"][:3]
    ) or "  (nenhuma decisão CEO detectada nesta janela)"

    sample_strategy = "\n".join(
        f"  - {s['agent']} ({s['ts'][:10]}): {s['summary'][:120]}..."
        for s in signals["strategy_changes"][:3]
    ) or "  (nenhuma mudança estratégica detectada)"

    sample_clients = "\n".join(
        f"  - {c['agent']} ({c['ts'][:10]}): {c['summary'][:120]}..."
        for c in signals["client_updates"][:3]
    ) or "  (nenhuma atualização de cliente detectada)"

    entry = f"""

### {date_str} — Update automático ({timespan_start}..{timespan_end})

**Disparou:** `user_model_updater.py` analisou {signals['total_episodes']} episódios. Mudança qualitativa detectada.

**Sinais capturados:**
- {len(signals['decisions'])} decisões CEO referenciadas
- {len(signals['client_updates'])} atualizações de cliente
- {len(signals['preferences'])} preferências reveladas
- {len(signals['strategy_changes'])} mudanças estratégicas
- Top agents: {top_agents}
- Valência média: {signals['valence_avg']:.2f}

**Amostras — Decisões CEO:**
{sample_decisions}

**Amostras — Mudanças estratégicas:**
{sample_strategy}

**Amostras — Atualizações de cliente:**
{sample_clients}

**Síntese:** Modelo atualizado. Detalhes derivados precisam revisão manual em `cognitive-style.md`, `business-context.md`, `relationship-graph.md` se necessário.

**Modo:** {"LLM (Haiku)" if args.llm else "Heurístico (Tier 0, $0)"}
"""

    # Insere a entry ANTES da seção "## Padrões de update"
    marker = "## Padrões de update"
    if marker in current:
        new_content = current.replace(marker, entry + "\n---\n\n" + marker, 1)
    else:
        new_content = current + entry
    log_path.write_text(new_content, encoding="utf-8")
    print(f"✓ Entry adicionada a {log_path.name}", file=sys.stderr)


def update_last_updated(file: Path, increment: bool = True):
    """Atualiza last_updated e update_count no frontmatter."""
    if not file.exists():
        return
    text = file.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")
    text = re.sub(r"last_updated:\s*\S+", f"last_updated: {today}", text)
    if increment:
        m = re.search(r"update_count:\s*(\d+)", text)
        if m:
            count = int(m.group(1)) + 1
            text = re.sub(r"update_count:\s*\d+", f"update_count: {count}", text)
    file.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Atualização dialética do user-model")
    parser.add_argument("--days", type=int, default=14,
                        help="Janela de análise (dias). Default 14.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Só detecta sinais, não escreve.")
    parser.add_argument("--llm", action="store_true",
                        help="Use Haiku para síntese refinada (Tier 1, ~$0.01).")
    parser.add_argument("--force", action="store_true",
                        help="Adiciona entry mesmo sem mudança qualitativa.")
    parser.add_argument("--json", action="store_true",
                        help="Output estruturado.")
    args = parser.parse_args()

    if not USER_MODEL_DIR.exists():
        print(f"⚠️  {USER_MODEL_DIR} não existe. Rode com seed primeiro.",
              file=sys.stderr)
        return 1

    print(f"🧠 Carregando episódios dos últimos {args.days} dias...", file=sys.stderr)
    episodes = load_recent_episodes(args.days)
    print(f"   {len(episodes)} episódios significativos", file=sys.stderr)

    if not episodes:
        print("Nenhum episódio para analisar.", file=sys.stderr)
        return 0

    print(f"🔍 Extraindo sinais ({'LLM' if args.llm else 'heurístico'})...",
          file=sys.stderr)
    signals = extract_signals(episodes)

    qualitative = has_qualitative_change(signals)

    if args.json:
        # Convert Counter to dict for JSON
        signals_out = {**signals, "agent_activity": dict(signals["agent_activity"])}
        signals_out["has_qualitative_change"] = qualitative
        print(json.dumps(signals_out, ensure_ascii=False, indent=2, default=str))
        return 0

    print(f"\n📊 Sinais extraídos ({len(episodes)} episódios):")
    print(f"   Decisões CEO:        {len(signals['decisions'])}")
    print(f"   Updates cliente:     {len(signals['client_updates'])}")
    print(f"   Preferências:        {len(signals['preferences'])}")
    print(f"   Mudanças estratégia: {len(signals['strategy_changes'])}")
    print(f"   Valência média:      {signals['valence_avg']:.2f}")
    print(f"\n   Top agents: {', '.join(f'@{a}({n})' for a, n in signals['agent_activity'].most_common(5))}")
    print(f"\n   Mudança qualitativa: {'SIM' if qualitative else 'NÃO'}")

    if not qualitative and not args.force:
        print(f"\n✓ Modelo estável — sem mudanças qualitativas necessárias.")
        return 0

    if args.dry_run:
        print(f"\n(--dry-run: nenhum arquivo modificado)")
        return 0

    append_evolutive_entry(signals, args)
    for fname in ["cognitive-style.md", "business-context.md", "relationship-graph.md"]:
        update_last_updated(USER_MODEL_DIR / fname, increment=False)
    update_last_updated(USER_MODEL_DIR / "evolutive-log.md", increment=True)

    # OPS snapshot — sempre atualizado (não condicional a mudança qualitativa)
    print("\n📡 Capturando OPS snapshot (meta_ads + feedback-loop + signals)...",
          file=sys.stderr)
    ops = gather_ops_snapshot()
    write_ops_snapshot(ops)
    err_count = len(ops.get("errors") or [])
    if err_count > 0:
        print(f"   ⚠️  {err_count} erro(s) na coleta — ver ops-snapshot.md", file=sys.stderr)
    else:
        print(f"   ✓ ops-snapshot.md atualizado", file=sys.stderr)

    state = load_state()
    state["total_updates"] = state.get("total_updates", 0) + 1
    state["last_synthesis"] = {
        "decisions": len(signals["decisions"]),
        "client_updates": len(signals["client_updates"]),
        "preferences": len(signals["preferences"]),
        "strategy_changes": len(signals["strategy_changes"]),
    }
    save_state(state)

    print(f"\n✅ User model atualizado.")
    print(f"   Veja: cat ~/cortex/vault/user-model/evolutive-log.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
