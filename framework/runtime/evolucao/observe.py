#!/usr/bin/env python3
"""observe.py — Junta a evidência da semana para o Ciclo de Evolução.

Saída: markdown com seções fixas (o diagnosticador lê isto, não o disco inteiro):
  1. Episódios com falha ou valência negativa (7d), por agente
  2. Heurísticas refutadas / aplicadas (7d)
  3. Alertas enviados (7d), por job
  4. Uso: episódios por agente, skills invocadas (se houver transcripts), delegações
  5. Correções do CEO (só no Mac: transcripts) — "não", "errado", "refaz", "de novo"
  6. Health check (--json) e bateria de roteamento
Uso: observe.py [--dias 7] [--saida arquivo.md]
"""
import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HOME = Path.home()


def ts_of(s):
    try:
        return time.mktime(time.strptime(str(s)[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
    except Exception:
        return 0


def episodios(cut):
    por_agente = defaultdict(lambda: {"total": 0, "falha": 0, "neg": 0, "exemplos": []})
    for f in (HOME / "consciousness/memory/episodic").glob("*.jsonl"):
        for line in f.read_text(errors="ignore").splitlines():
            try:
                d = json.loads(line)
            except Exception:
                continue
            if ts_of(d.get("timestamp")) < cut:
                continue
            a = d.get("agent", "?")
            e = por_agente[a]
            e["total"] += 1
            res = (d.get("outcome") or {}).get("result", "")
            val = float((d.get("valence") or {}).get("score", 0) or 0)
            if res in ("failure", "partial"):
                e["falha"] += 1
            if val < 0:
                e["neg"] += 1
            if (res in ("failure", "partial") or val < 0) and len(e["exemplos"]) < 3:
                les = d.get("lessons") or {}
                e["exemplos"].append(f"[{d.get('id')}] {str(d.get('summary',''))[:160]} | falhou: {str(les.get('what_failed',''))[:120]}")
    return por_agente


def heuristicas(cut):
    p = HOME / "consciousness/memory/procedural/heuristics.jsonl"
    ref, apl = [], []
    for line in p.read_text(errors="ignore").splitlines() if p.exists() else []:
        try:
            h = json.loads(line)
        except Exception:
            continue
        if (h.get("times_failed") or 0) > 0:
            ref.append(f"{h.get('agent')} · conf={h.get('confidence')} · falhas={h.get('times_failed')} · {str(h.get('heuristic',''))[:110]}")
        if ts_of(h.get("last_validated")) >= cut and (h.get("times_validated") or 0) > 1:
            apl.append(f"{h.get('agent')} · validada {h.get('times_validated')}x · {str(h.get('heuristic',''))[:110]}")
    return ref[:15], apl[:10]


def alertas(cut):
    c = Counter()
    for d in ("sent", "pending"):
        for f in (HOME / "autonomous/notifications" / d).glob("*.json"):
            try:
                if f.stat().st_mtime < cut:
                    continue
                j = json.loads(f.read_text(errors="ignore"))
                c[f"{j.get('severity')}: {str(j.get('title',''))[:70]}"] += 1
            except Exception:
                continue
    return c.most_common(15)


def correcoes(cut):
    """Só no Mac: mensagens do CEO que corrigem uma entrega."""
    proj = HOME / ".claude/projects"
    if not proj.exists():
        return [], 0
    pat = re.compile(r"(?i)^\s*(não|nao|errado|errou|refaz|de novo|não é isso|nao e isso|volta|desfaz|isso não|isso nao|está errado|ta errado)\b")
    achados, n_user = [], 0
    for f in proj.rglob("*.jsonl"):
        try:
            if f.stat().st_mtime < cut:
                continue
            for line in f.open(errors="ignore"):
                if '"type":"user"' not in line and '"type": "user"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if ts_of(d.get("timestamp")) < cut:
                    continue
                c = (d.get("message") or {}).get("content")
                txt = c if isinstance(c, str) else " ".join(x.get("text", "") for x in c if isinstance(x, dict)) if isinstance(c, list) else ""
                if not txt or txt.startswith("<"):
                    continue
                n_user += 1
                if pat.search(txt):
                    achados.append(txt.strip().replace("\n", " ")[:160])
        except OSError:
            continue
    return achados[:20], n_user


def uso(cut):
    skills, agentes = Counter(), Counter()
    proj = HOME / ".claude/projects"
    if proj.exists():
        for f in proj.rglob("*.jsonl"):
            try:
                if f.stat().st_mtime < cut:
                    continue
                for line in f.open(errors="ignore"):
                    if '"tool_use"' not in line:
                        continue
                    try:
                        d = json.loads(line)
                    except Exception:
                        continue
                    if ts_of(d.get("timestamp")) < cut:
                        continue
                    c = (d.get("message") or {}).get("content")
                    if not isinstance(c, list):
                        continue
                    for x in c:
                        if not isinstance(x, dict) or x.get("type") != "tool_use":
                            continue
                        if x.get("name") == "Skill":
                            skills[str((x.get("input") or {}).get("skill", "?")).split(":")[-1]] += 1
                        if x.get("name") in ("Agent", "Task"):
                            agentes[(x.get("input") or {}).get("subagent_type", "?")] += 1
            except OSError:
                continue
    return skills.most_common(10), agentes.most_common(10)


def health():
    try:
        r = subprocess.run(["python3", str(HOME / "framework/scripts/framework_health_check.py"), "--json"], capture_output=True, text=True, timeout=300)
        checks = json.loads(r.stdout or "[]")
        return [f"{c['level']} {c['check']}: {c['detail'][:120]}" for c in checks if c["level"] != "OK"]
    except Exception as e:
        return [f"health check falhou: {e}"]


def bateria():
    try:
        r = subprocess.run(["python3", str(HOME / "framework/tests/run-routing-battery.py")], capture_output=True, text=True, timeout=120)
        m = re.search(r"Score:\s*(\d+/\d+)", r.stdout)
        miss = re.findall(r'✗ pedido: "(.*?)"', r.stdout)
        return (m.group(1) if m else "?"), miss[:5]
    except Exception:
        return "?", []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=7)
    ap.add_argument("--saida")
    a = ap.parse_args()
    cut = time.time() - a.dias * 86400
    L = [f"# Observação da semana — {time.strftime('%Y-%m-%d')} (últimos {a.dias} dias, host {Path('/opt/segunda-feira').exists() and 'VPS' or 'Mac'})", ""]

    L.append("## 1. Episódios por agente (total · falha/parcial · valência negativa)")
    ep = episodios(cut)
    for ag, e in sorted(ep.items(), key=lambda x: (-x[1]["falha"] - x[1]["neg"], -x[1]["total"])):
        L.append(f"- {ag}: {e['total']} · falha {e['falha']} · neg {e['neg']}")
        for ex in e["exemplos"]:
            L.append(f"    - {ex}")
    if not ep:
        L.append("- (nenhum episódio na janela)")

    ref, apl = heuristicas(cut)
    L += ["", "## 2. Heurísticas refutadas (qualquer época) e validadas na janela"]
    L += [f"- REFUTADA: {r}" for r in ref] or ["- nenhuma refutada — o loop de contra-evidência não fechou nesta semana"]
    L += [f"- VALIDADA: {x}" for x in apl]

    L += ["", "## 3. Alertas enviados na janela"]
    al = alertas(cut)
    L += [f"- {n}× {t}" for t, n in al] or ["- nenhum"]

    sk, agd = uso(cut)
    L += ["", "## 4. Uso real (transcripts — só no Mac)"]
    L.append("- skills invocadas: " + (", ".join(f"{k}×{v}" for k, v in sk) or "nenhuma"))
    L.append("- delegações a agentes: " + (", ".join(f"{k}×{v}" for k, v in agd) or "nenhuma"))

    cor, n_user = correcoes(cut)
    L += ["", f"## 5. Correções do CEO ({len(cor)} em {n_user} mensagens)"]
    L += [f"- \"{c}\"" for c in cor] or ["- nenhuma detectada (ou sem transcripts neste host)"]

    L += ["", "## 6. Verificadores"]
    L += [f"- {h}" for h in health()] or ["- health check: tudo OK"]
    sc, miss = bateria()
    L.append(f"- bateria de roteamento: {sc}" + (f" · misses: {miss}" if miss else ""))

    out = "\n".join(L) + "\n"
    if a.saida:
        Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
        Path(a.saida).write_text(out)
        print(f"observação gravada em {a.saida} ({len(out)} chars)")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
