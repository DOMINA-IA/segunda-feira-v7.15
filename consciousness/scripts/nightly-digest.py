#!/usr/bin/env python3
"""Nightly Digest — Analisa o pipeline da noite e envia relatório via Telegram.

Responde:
- O que foi assimilado (episódios, heurísticas, fatos)
- O que foi distribuído (briefings, links, sinais)
- O que o CEO não vê (anomalias, agentes silenciosos, frustrações)
- Sugestões (novos agentes, ajustes, projetos estagnados)
"""
import json, os, re, sys, subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict

HOME = Path.home()
TG_ENV = HOME / ".claude/channels/telegram/.env"
TG_ACCESS = HOME / ".claude/channels/telegram/access.json"
EP_DIR = HOME / "consciousness/memory/episodic"
HEUR_FILE = HOME / "consciousness/memory/procedural/heuristics.jsonl"
CONS_DIR = HOME / "consciousness/memory/consolidation"
VAULT = HOME / "cortex/vault"
BRIEF = HOME / "cortex/briefings"
SIGNALS = HOME / "broadcast/signals.json"
FEEDBACK = HOME / "feedback-loop/results.json"

def tg_creds():
    token = None
    if TG_ENV.exists():
        for line in TG_ENV.read_text().splitlines():
            if line.startswith(("TELEGRAM_BOT_TOKEN=", "BOT_TOKEN=")):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    chat_id = None
    if TG_ACCESS.exists():
        try:
            d = json.loads(TG_ACCESS.read_text())
            allowed = d.get("allowFrom", [])
            if allowed:
                chat_id = allowed[0]
        except Exception:
            pass
    return token, chat_id

def send_telegram(text: str, parse_mode: str = "HTML") -> bool:
    token, chat_id = tg_creds()
    if not token or not chat_id:
        print("ERRO: credenciais Telegram ausentes", file=sys.stderr)
        return False
    # Telegram max 4096 chars — quebrar se maior
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)] or [text]
    ok = True
    for chunk in chunks:
        try:
            r = subprocess.run(
                [
                    "curl", "-sS", "--max-time", "15",
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    "--data-urlencode", f"chat_id={chat_id}",
                    "--data-urlencode", f"text={chunk}",
                    "--data-urlencode", f"parse_mode={parse_mode}",
                    "--data-urlencode", "disable_web_page_preview=true",
                ],
                capture_output=True, text=True, timeout=20,
            )
            try:
                resp = json.loads(r.stdout)
            except Exception:
                resp = {"ok": False, "raw": r.stdout, "err": r.stderr}
            if not resp.get("ok"):
                print(f"Telegram erro: {resp}", file=sys.stderr)
                ok = False
        except Exception as e:
            print(f"Telegram falhou: {e}", file=sys.stderr)
            ok = False
    return ok

def load_jsonl(path: Path):
    out = []
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def yesterday_str():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def parse_ts(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

def safe_float(v, default=0.0):
    if isinstance(v, dict):
        v = v.get("score", default)
    try:
        return float(v)
    except Exception:
        return default

def analyze_episodes():
    """Retorna estatísticas dos episódios das últimas 24h."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    stats = {
        "total": 0, "by_agent": Counter(), "by_type": Counter(),
        "by_result": Counter(), "valence_by_agent": defaultdict(list),
        "samples_positive": [], "samples_negative": [],
        "silent_agents": [],
    }
    all_agents = []
    if EP_DIR.exists():
        for f in EP_DIR.glob("*.jsonl"):
            agent = f.stem
            all_agents.append(agent)
            eps = load_jsonl(f)
            recent = []
            for e in eps:
                ts = parse_ts(e.get("timestamp", ""))
                if ts and ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts and ts >= cutoff:
                    recent.append(e)
            if not recent:
                # silencioso se teve atividade antes mas não nas últimas 24h
                if eps:
                    stats["silent_agents"].append((agent, len(eps)))
                continue
            stats["total"] += len(recent)
            stats["by_agent"][agent] = len(recent)
            for e in recent:
                stats["by_type"][e.get("type", "?")] += 1
                stats["by_result"][e.get("result", "?")] += 1
                v = safe_float(e.get("valence"))
                stats["valence_by_agent"][agent].append(v)
                summary = (e.get("summary") or "")[:110]
                if v >= 0.7:
                    stats["samples_positive"].append((agent, v, summary))
                elif v <= -0.5:
                    stats["samples_negative"].append((agent, v, summary))
    return stats, all_agents

def analyze_heuristics():
    heur = load_jsonl(HEUR_FILE)
    today = today_str()
    new_today = [h for h in heur if today in (h.get("created_at", "") + h.get("timestamp", ""))]
    by_agent = Counter(h.get("agent", "?") for h in heur)
    low_conf = [h for h in heur if safe_float(h.get("confidence"), 1.0) < 0.5]
    return {
        "total": len(heur),
        "new_today": len(new_today),
        "new_samples": new_today[:5],
        "by_agent": by_agent,
        "low_confidence": low_conf[:3],
    }

def analyze_consolidation():
    today_log = CONS_DIR / f"consolidation-{today_str()}.log"
    if not today_log.exists():
        return {"found": False}
    text = today_log.read_text()
    # pegar último bloco (produção)
    blocks = re.split(r"=== CONSOLIDAÇÃO INICIADA ===", text)
    last = blocks[-1] if blocks else text
    def ext(pat):
        m = re.search(pat, last)
        return m.group(1) if m else None
    return {
        "found": True,
        "mode": ext(r"Modo: (\w+)"),
        "episodes": ext(r"Episódios analisados: (\d+)"),
        "patterns": ext(r"Padrões extraídos: (\d+)"),
        "facts": ext(r"Fatos consolidados: (\d+)"),
        "exported": ext(r"Fatos exportados para CORTEX vault: (\d+)"),
        "validated": ext(r"Heurísticas validadas/ajustadas: (\d+)"),
        "deprecated": ext(r"Heurísticas depreciadas.*: (\d+)"),
    }

def analyze_cortex():
    notes = list(VAULT.rglob("*.md")) if VAULT.exists() else []
    briefs = list(BRIEF.glob("*.md")) if BRIEF.exists() else []
    today = datetime.now().date()
    new_today = [n for n in notes if datetime.fromtimestamp(n.stat().st_mtime).date() == today]
    briefs_today = [b for b in briefs if datetime.fromtimestamp(b.stat().st_mtime).date() == today]
    return {
        "notes_total": len(notes),
        "notes_new_today": len(new_today),
        "notes_samples": [n.name for n in new_today[:5]],
        "briefings_refreshed": len(briefs_today),
    }

def analyze_signals():
    if not SIGNALS.exists():
        return []
    try:
        d = json.loads(SIGNALS.read_text())
        signals = d.get("signals", [])
        active = [s for s in signals if not s.get("consumed")]
        return active[:5]
    except Exception:
        return []

def derive_insights(ep_stats, heur_data, cortex_data, all_agents):
    """Análises que o CEO não vê facilmente."""
    insights = []
    # 1. Agente dominante
    if ep_stats["total"] > 10:
        top_agent, top_count = ep_stats["by_agent"].most_common(1)[0]
        share = top_count / ep_stats["total"]
        if share > 0.5:
            insights.append(
                f"⚠️ <b>@{top_agent}</b> concentrou {share*100:.0f}% dos episódios ({top_count}/{ep_stats['total']}). "
                f"Se for voz, ok. Se for operacional, considere dividir carga."
            )
    # 2. Agentes silenciosos com histórico
    silent_heavy = [(a, n) for a, n in ep_stats["silent_agents"] if n >= 5]
    if silent_heavy:
        insights.append(
            f"💤 <b>{len(silent_heavy)} agentes inativos há 24h+</b> com histórico: "
            + ", ".join(f"@{a}" for a, _ in silent_heavy[:5])
            + ". Reavaliar se ainda são necessários ou se devem ser reativados."
        )
    # 3. Valência negativa persistente
    frustrated = []
    for agent, vals in ep_stats["valence_by_agent"].items():
        if len(vals) >= 3:
            avg = sum(vals) / len(vals)
            if avg < -0.3:
                frustrated.append((agent, avg, len(vals)))
    for agent, avg, n in frustrated:
        insights.append(
            f"🔴 <b>@{agent}</b> com valência média {avg:+.2f} em {n} tarefas. "
            f"Sinal de frustração sistêmica — investigar obstáculos."
        )
    # 4. Result field drift (schema)
    unknown_ratio = ep_stats["by_result"].get("?", 0) / max(ep_stats["total"], 1)
    if unknown_ratio > 0.3:
        insights.append(
            f"🐛 <b>Schema drift</b>: {unknown_ratio*100:.0f}% dos episódios sem campo <code>result</code>. "
            f"record-episode.sh pode estar sem flag --result no invocador."
        )
    # 5. Heurísticas com baixa confiança persistente
    if heur_data["low_confidence"]:
        insights.append(
            f"📉 <b>{len(heur_data['low_confidence'])} heurísticas com confiança &lt; 0.5</b> — "
            f"revisar ou depreciar para não poluir decisão futura."
        )
    # 6. CORTEX estagnado
    if cortex_data["notes_new_today"] == 0 and ep_stats["total"] >= 10:
        insights.append(
            "📚 <b>Nenhuma nota CORTEX nova hoje</b> apesar de atividade significativa. "
            "Conhecimento produzido não está sendo capturado — episódios não estão virando notas."
        )
    return insights

def derive_suggestions(ep_stats, signals, cortex_data):
    """Sugestões acionáveis de agentes/projetos."""
    suggestions = []
    # Tipos de episódio que dominam sem agente dedicado
    top_types = ep_stats["by_type"].most_common(3)
    if ep_stats["by_type"].get("pattern_detected", 0) >= 10:
        suggestions.append(
            "🤖 <b>Novo agente sugerido: @pattern-watcher</b> — "
            "10+ pattern_detected em 24h indica trabalho de observação que poderia ser dedicado."
        )
    # Sinais sem responsável
    if signals:
        unhandled = [s for s in signals if not s.get("assigned_to")]
        if unhandled:
            suggestions.append(
                f"📡 <b>{len(unhandled)} sinais ativos sem responsável</b>: "
                + ", ".join(s.get("type", "?") for s in unhandled[:3])
                + ". Atribuir a um agente específico."
            )
    # sf-voice alto → pode indicar oportunidade de UI
    voice_eps = ep_stats["by_agent"].get("sf-voice", 0)
    if voice_eps >= 20:
        suggestions.append(
            f"🎙 <b>@sf-voice registrou {voice_eps} interações</b> em 24h. "
            "Considere transformar top 5 comandos em atalhos de 1 clique para reduzir fricção."
        )
    # Sempre tem algo
    if not suggestions:
        suggestions.append("✅ Sem sugestões críticas hoje — sistema operando dentro do esperado.")
    return suggestions

def build_digest():
    ep_stats, all_agents = analyze_episodes()
    heur_data = analyze_heuristics()
    cons = analyze_consolidation()
    cortex_data = analyze_cortex()
    signals = analyze_signals()
    insights = derive_insights(ep_stats, heur_data, cortex_data, all_agents)
    suggestions = derive_suggestions(ep_stats, signals, cortex_data)

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    lines = []
    lines.append(f"🧠 <b>SEGUNDA-FEIRA — Digest Noturno</b>")
    lines.append(f"<i>{now}</i>")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("<b>📥 ASSIMILADO</b>")
    if cons["found"]:
        lines.append(f"• Modo: {cons['mode'] or '?'}")
        lines.append(f"• Episódios analisados: <b>{cons['episodes'] or 0}</b>")
        lines.append(f"• Padrões extraídos: <b>{cons['patterns'] or 0}</b>")
        lines.append(f"• Fatos consolidados: <b>{cons['facts'] or 0}</b>")
        lines.append(f"• Exportados p/ CORTEX: <b>{cons['exported'] or 0}</b>")
    else:
        lines.append("⚠️ Log de consolidação do dia não encontrado.")
    lines.append(f"• Heurísticas novas: <b>{heur_data['new_today']}</b> (total {heur_data['total']})")
    lines.append(f"• Atividade 24h: <b>{ep_stats['total']}</b> episódios em {len(ep_stats['by_agent'])} agentes")
    lines.append("")
    lines.append("<b>📤 DISTRIBUÍDO</b>")
    lines.append(f"• Briefings regenerados: <b>{cortex_data['briefings_refreshed']}</b>")
    lines.append(f"• Notas CORTEX novas: <b>{cortex_data['notes_new_today']}</b> (total {cortex_data['notes_total']})")
    if cortex_data["notes_samples"]:
        for n in cortex_data["notes_samples"][:3]:
            lines.append(f"  └ {n}")
    if signals:
        lines.append(f"• Sinais ativos no broadcast: <b>{len(signals)}</b>")
    lines.append("")
    lines.append("<b>🏆 TOP AGENTES (24h)</b>")
    for agent, count in ep_stats["by_agent"].most_common(5):
        vals = ep_stats["valence_by_agent"].get(agent, [])
        avg = sum(vals) / len(vals) if vals else 0
        emoji = "🟢" if avg > 0.3 else "🟡" if avg >= -0.1 else "🔴"
        lines.append(f"{emoji} @{agent}: {count} ({avg:+.2f})")
    if ep_stats["samples_positive"]:
        lines.append("")
        lines.append("<b>✨ DESTAQUES POSITIVOS</b>")
        for agent, v, s in ep_stats["samples_positive"][:3]:
            s_esc = s.replace("<", "&lt;").replace(">", "&gt;")
            lines.append(f"• @{agent} [{v:+.1f}]: {s_esc}")
    if ep_stats["samples_negative"]:
        lines.append("")
        lines.append("<b>⚠️ PONTOS DE ATENÇÃO</b>")
        for agent, v, s in ep_stats["samples_negative"][:3]:
            s_esc = s.replace("<", "&lt;").replace(">", "&gt;")
            lines.append(f"• @{agent} [{v:+.1f}]: {s_esc}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("<b>🔍 O QUE VOCÊ NÃO VÊ</b>")
    if insights:
        for i in insights[:6]:
            lines.append(f"• {i}")
    else:
        lines.append("• Nenhuma anomalia detectada — sistema saudável.")
    lines.append("")
    lines.append("<b>💡 SUGESTÕES</b>")
    for s in suggestions[:5]:
        lines.append(f"• {s}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("<i>Próxima assimilação: amanhã 20:30 BRT</i>")
    lines.append("<i>Healthcheck: 08:00 BRT — se falhou, roda automático</i>")
    return "\n".join(lines)

def main():
    dry = "--dry-run" in sys.argv
    digest = build_digest()
    if dry:
        print(digest)
        return 0
    ok = send_telegram(digest)
    # log
    log_path = HOME / "logs/nightly-digest.log"
    log_path.parent.mkdir(exist_ok=True)
    with log_path.open("a") as f:
        f.write(f"[{datetime.now().isoformat()}] Digest enviado: {'OK' if ok else 'FALHOU'}\n")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
