#!/usr/bin/env python3
"""
THALAMUS — Router Inteligente (Hook Unificado)

Substitui os 3 hooks separados por 1 router que decide
o que injetar baseado em:
  - Relevância (o prompt menciona algo no CORTEX?)
  - Urgência (existem alertas críticos?)
  - Frescor (dados estão atualizados?)
  - Budget (max ~1500 tokens de injeção por mensagem)

Também funciona como hook Stop para session save.

Modo: UserPromptSubmit ou Stop (detectado pelo argumento)
"""

import sys
import os
import json
import re
import yaml
from pathlib import Path

BRAIN_HOME = Path.home() / "brain"
CORTEX_HOME = Path.home() / "cortex"
CORTEX_SCRIPTS = CORTEX_HOME / "scripts"
BROADCAST_HOME = Path.home() / "broadcast"

sys.path.insert(0, str(CORTEX_SCRIPTS))

# Token budget — max chars a injetar (1 token ~= 4 chars)
MAX_INJECT_CHARS = 9000  # ~2250 tokens (subiu de 6000 em 2026-07-07 junto com o corte por-rule 1500→3000; o budget global continua truncando com marcador)

# ─── Importações seguras ────────────────────────────────────

def safe_import(func_name, module_name):
    try:
        mod = __import__(module_name)
        return getattr(mod, func_name)
    except (ImportError, AttributeError):
        return None

load_session_context = safe_import("load_session_context", "session_tracker")
load_wip_context = safe_import("load_wip_context", "session_tracker")
save_session = safe_import("save_session", "session_tracker")
format_pulse = safe_import("format_pulse_for_injection", "pulse_check")
run_alerts = safe_import("run_decision_engine", "decision_engine")
format_alerts = safe_import("format_alerts_for_injection", "decision_engine")
format_predictions = safe_import("format_predictions_for_injection", "predictor")
format_heuristics = safe_import("format_heuristics_for_agent", "heuristics_inject")
format_heuristics_rel = safe_import("format_heuristics_by_relevance", "heuristics_inject")


# ─── MODO: UserPromptSubmit ─────────────────────────────────

def handle_submit(prompt):
    """Processa prompt do usuário e injeta contexto relevante."""
    if not prompt:
        return

    prompt_lower = prompt.lower()
    parts = []  # (prioridade, conteúdo)
    total_chars = 0

    # Skip para mensagens simples
    skip = re.match(r'^(sim|não|ok|beleza|pode|valeu|obrigado|s|n|SIM|NÃO)\s*[.!?]*$', prompt.strip())
    if skip:
        return

    # ── P0: ALERTAS CRÍTICOS (sempre, se existem) ──────────
    if run_alerts and format_alerts:
        try:
            alerts = run_alerts()
            high = [a for a in alerts if a.get("priority") == "high"]
            if high:
                ctx = format_alerts(high)
                if ctx:
                    parts.append((0, ctx))
        except Exception:
            pass

    # ── P1: SESSION + WIP (continuidade) ───────────────────
    if load_session_context:
        try:
            ctx = load_session_context()
            if ctx:
                parts.append((1, ctx))
        except Exception:
            pass

    if load_wip_context:
        try:
            ctx = load_wip_context()
            if ctx:
                parts.append((1, ctx))
        except Exception:
            pass

    # ── P2: @AGENT BRIEFING ────────────────────────────────
    agent_match = re.findall(r'@([\w-]+)', prompt_lower)
    if agent_match:
        briefings_dir = CORTEX_HOME / "briefings"
        for agent in agent_match[:1]:  # Max 1 briefing
            # Briefings foram reorganizados em meta/ e ops/ (axis-separation) —
            # tentar flat (legado), depois os dois eixos (fix 2026-07-09, Sprint 3)
            bf = None
            for cand in (briefings_dir / f"{agent}.md",
                         briefings_dir / "ops" / f"{agent}.md",
                         briefings_dir / "meta" / f"{agent}.md"):
                if cand.exists():
                    bf = cand
                    break
            if bf:
                content = bf.read_text(encoding="utf-8")[:2000]
                parts.append((2, f"[CORTEX Briefing @{agent}]\n{content}"))
            # Heurísticas validadas do agente (fecha loop write→read; ver heuristics_inject.py).
            # Passa o prompt como seed do sorteio ponderado — prompts diferentes do
            # mesmo agente circulam heurísticas diferentes; o mesmo prompt é estável.
            if format_heuristics:
                try:
                    h = format_heuristics(agent, prompt_lower)
                    if h:
                        parts.append((2, h))
                except Exception:
                    pass

            # Mailbox não-lida do agente (fecha o loop de comunicação inter-agente;
            # ver agent-communication.md — agente deve ler mailbox ao ser ativado).
            # Parse 100% defensivo: arquivo ausente/corrompido = silêncio, nunca
            # quebra o hook. NÃO marca como lida — quem decide é o próprio agente.
            try:
                mb_path = BROADCAST_HOME / "mailbox" / f"{agent}.json"
                if mb_path.exists():
                    mb = json.loads(mb_path.read_text(encoding="utf-8"))
                    inbox = mb.get("inbox", []) if isinstance(mb, dict) else []
                    unread = [m for m in inbox if isinstance(m, dict) and m.get("read") is False]
                    if unread:
                        unread.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
                        lines = [f"[Mailbox @{agent} — {len(unread)} não lidas]"]
                        for m in unread[:3]:
                            frm = m.get("from", "?")
                            subj = m.get("subject", "(sem assunto)")
                            lines.append(f"  • de {frm}: {subj}")
                        parts.append((2, "\n".join(lines)))
            except Exception:
                pass

    # ── P3: KNOWLEDGE (BM25 + rules on-demand) ────────────
    should_search = len(prompt) > 15 and len(prompt.split()) > 2 and not agent_match

    if should_search:
        # Heurísticas por relevância de conteúdo (modo conversacional, sem @agent).
        # Fecha o loop write→read: a maioria dos prompts não cita @agent, então
        # antes as 447 heurísticas de alta confiança nunca eram recuperadas (F6/W1).
        if format_heuristics_rel:
            try:
                hr = format_heuristics_rel(prompt_lower)
                if hr:
                    parts.append((2, hr))
            except Exception:
                pass

        # BM25 search
        search_index_path = CORTEX_HOME / "index" / "search-index.json"
        if search_index_path.exists():
            try:
                import math
                search_index = json.loads(search_index_path.read_text(encoding="utf-8"))
                stopwords = {
                    "como", "para", "você", "voce", "pode", "quero", "preciso",
                    "fazer", "criar", "qual", "quais", "onde", "está", "esta",
                    "esse", "essa", "isso", "algo", "sobre", "nosso", "nossa",
                    "todos", "todo", "toda", "mais", "menos", "muito", "muita",
                    "agora", "depois", "antes", "ainda", "também", "vamos",
                    "deixa", "manda", "roda", "execute", "mostra",
                    "implementar", "configure", "atualizar", "verificar",
                }
                words = [w for w in re.findall(r'\w+', prompt_lower) if len(w) > 3 and w not in stopwords]

                if words:
                    N = len(search_index)
                    results = []
                    for nid, entry in search_index.items():
                        score = 0
                        kw = entry.get("keywords", [])
                        title = entry.get("title", "").lower()
                        tags = [str(t).lower() for t in entry.get("tags", [])]
                        for term in words[:5]:
                            if term in title: score += 5
                            if term in tags: score += 3
                            score += sum(1 for k in kw if term in k)
                        if score > 3:
                            f = entry.get("freshness", 0.5)
                            results.append((nid, entry.get("title", nid), entry.get("type", ""), round(score * (0.5 + 0.5 * f), 1), str(entry.get("path", "")).replace("/opt/segunda-feira", str(Path.home()))))  # índice pode vir da VPS

                    results.sort(key=lambda x: x[3], reverse=True)
                    if results[:3]:
                        lines = ["[CORTEX Context]"]
                        for r in results[:3]:
                            lines.append(f"  - {r[1]} ({r[2]}) [score:{r[3]}] → {r[4]}")
                        parts.append((3, "\n".join(lines)))
            except Exception:
                pass

        # Rules on-demand — injeta as 3 MAIS RELEVANTES (não as 3 primeiras do disco).
        # Score = nº de triggers que batem no prompt → seleção determinística por
        # relevância em vez da ordem não-determinística do glob() do filesystem.
        rules_dir = CORTEX_HOME / "vault" / "rules"
        if rules_dir.exists():
            try:
                candidates = []
                for rf in rules_dir.glob("*.md"):
                    content = rf.read_text(encoding="utf-8")
                    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                    if not fm_match:
                        continue
                    fm = yaml.safe_load(fm_match.group(1)) or {}
                    triggers = fm.get("triggers", [])
                    score = sum(1 for t in triggers if str(t).lower() in prompt_lower)
                    if score > 0:
                        body_full = content[fm_match.end():].strip()
                        body = body_full[:3000]
                        if len(body_full) > 3000:
                            # Truncamento explícito com ponteiro — antes cortava em 1500
                            # sem marcador e 23/24 rules perdiam conteúdo silenciosamente
                            body += f"\n... [truncado — rule completa em: {rf}]"
                        candidates.append((score, rf.stem,
                                           f"[CORTEX Rule: {fm.get('title', rf.stem)}]\n{body}"))
                candidates.sort(key=lambda x: (-x[0], x[1]))  # mais triggers primeiro; nome desempata (estável)
                for _, _, block in candidates[:3]:
                    parts.append((3, block))
            except Exception:
                pass

    # ── P4: PULSE (estado do negócio) ──────────────────────
    if format_pulse:
        try:
            ctx = format_pulse()
            if ctx:
                parts.append((4, ctx))
        except Exception:
            pass

    # ── P5: PREDICTIONS ────────────────────────────────────
    if format_predictions:
        try:
            ctx = format_predictions()
            if ctx:
                parts.append((5, ctx))
        except Exception:
            pass

    # ── Montar output com budget ───────────────────────────
    parts.sort(key=lambda x: x[0])  # Menor prioridade = mais importante

    output = []
    total = 0
    for priority, content in parts:
        if total + len(content) > MAX_INJECT_CHARS:
            # Truncar se necessário (P0-P1 nunca truncam)
            if priority <= 1:
                output.append(content)
                total += len(content)
            else:
                remaining = MAX_INJECT_CHARS - total
                if remaining > 200:
                    output.append(content[:remaining] + "\n... [truncado por budget de tokens]")
                break
        else:
            output.append(content)
            total += len(content)

    if output:
        print("\n---\n".join(output))


# ─── MODO: Stop ─────────────────────────────────────────────

def handle_stop(transcript):
    """Processa fim de conversa — salva sessão + detecta aprendizado."""
    if not transcript or len(transcript) < 300:
        return

    # Salvar sessão
    if save_session:
        try:
            save_session(transcript)
        except Exception:
            pass

    # Detectar aprendizado (simplificado)
    t = transcript.lower()
    suggestions = []

    if re.search(r'(?:porta|ip|config)\s+(?:mudou|alterou|novo)', t):
        suggestions.append("Infra alterada — verificar notas CORTEX")
    if sum(1 for p in [r'bug|erro|fix|corrigido|workaround', r'problema era|causa era|descobri que'] if re.search(p, t)) >= 2:
        suggestions.append("Bug/workaround — considerar nota feedback")
    if re.search(r'campanha\s+(?:criada|pausada|ativada|duplicada)', t):
        suggestions.append("Campanha alterada — atualizar projeto")

    if suggestions:
        lines = ["[CORTEX — aprendizado detectado]"]
        for s in suggestions[:3]:
            lines.append(f"  → {s}")
        print("\n".join(lines))


# ─── Entry Point ────────────────────────────────────────────

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "submit"
    raw = sys.stdin.read().strip()

    # Hooks do Claude Code entregam um envelope JSON no stdin — extrair o campo
    # certo em vez de tratar o envelope inteiro como texto (fix 2026-07-07, Sprint 1;
    # espelha o parsing do telegram-guard.py). Antes deste fix, o JSON inteiro era
    # usado como "prompt": o fast-path de skip nunca disparava e a busca CORTEX
    # rodava com lixo em 100% dos prompts.
    data = raw
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            if mode == "stop":
                # O Stop hook envia transcript_path, não o texto do transcript
                tp = payload.get("transcript_path", "")
                if tp and Path(tp).exists():
                    data = Path(tp).read_text(encoding="utf-8", errors="ignore")[-20000:]
                else:
                    data = ""
            else:
                data = payload.get("prompt", "")
    except (json.JSONDecodeError, ValueError):
        pass  # stdin não-JSON (ex.: teste manual via echo) — usa o texto cru

    if mode == "stop":
        handle_stop(data)
    else:
        handle_submit(data)
