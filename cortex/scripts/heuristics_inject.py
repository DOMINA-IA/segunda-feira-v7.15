#!/usr/bin/env python3
"""
heuristics_inject — Recuperação de heurísticas em runtime (fecha o loop write→read).

Problema que resolve: o Consciousness Engine ESCREVE centenas de heurísticas validadas
mas o thalamus/router.py só injetava as 3 do topo por solidez — sempre as MESMAS 3,
sempre para o mesmo agente. ~390 heurísticas sólidas (confidence alta, times_validated
alto) ficavam presas fora do top-3 eterno e nunca circulavam (Sprint 3, 2026-07-08).

Este módulo é importado pelo router via safe_import. Quando um @agent é detectado,
injeta heurísticas daquele agente: os GUARANTEED_TOP mais sólidos SEMPRE entram
(exploração garantida do topo) e as vagas restantes são sorteadas — ponderadas por
confidence × log(1+times_validated) × recência, sem reposição, determinístico por
prompt (mesmo prompt → mesmo sorteio; prompts diferentes → conjuntos diferentes) —
entre os próximos candidatos por solidez. Isso faz circular também heurísticas que
nunca chegavam ao topo. Incrementa triggered_count das injetadas, que passa a medir
USO REAL, não validação batch.

Best-effort: qualquer falha retorna "" e nunca quebra o hook.
"""

import hashlib
import json
import math
import os
import random
import re
from datetime import datetime, timezone
from pathlib import Path

HEUR_PATH = Path.home() / "consciousness" / "memory" / "procedural" / "heuristics.jsonl"

# Sprint 3 Grupo F — log de heurísticas injetadas (fecha o elo "medir" do ciclo:
# cruzado depois com trajectory.jsonl por ~/framework/scripts/heuristic-efficacy.py).
INJECTED_LOG = Path.home() / "cortex" / "heuristics-injected.jsonl"

# Piso de credibilidade: exclui heurísticas REFUTADAS, não as não-corroboradas.
#
# Até 15-Jul-2026 este piso era 0.7 numa escala em que 89,5% do pool marcava >=0.9,
# porque a "validação" era coocorrência de palavras (ver heuristic_validator.py).
# Filtrar >=0.7 parecia seletivo e não filtrava nada — a seleção real sempre foi
# relevância + TOP_N. Com a confidence recalibrada por evidência independente, a
# escala mudou: 0.5 = registrada e não corroborada, >0.5 = corroborada, <0.5 = tem
# contra-evidência. Manter 0.7 aqui zeraria a injeção.
#
# O piso agora significa "não foi refutada". Uma heurística verdadeira mas rara
# ("quando deploy Hostinger falhar com nologin, usar sftp") tem evidência fraca e
# relevância altíssima — confidence epistêmica nunca foi o critério certo de
# injeção, e fingir que era foi o que forçou a inflação.
MIN_CONFIDENCE = 0.4
TOP_N = 6              # heurísticas injetadas quando há @agent explícito no prompt
TOP_N_RELEVANCE = 4    # heurísticas injetadas por relevância de conteúdo (sem @agent)
GUARANTEED_TOP = 3     # entram sempre pelo score primário — exploração garantida do topo
SAMPLE_POOL = 15       # candidatos pós-topo de onde as vagas restantes são sorteadas
MAX_TEXT = 180  # corta heurística verbosa


def _load():
    recs = []
    with open(HEUR_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return recs


def _score(h):
    # Solidez = confiança × evidência independente.
    # Desde 15-Jul-2026 times_validated conta episódios DISTINTOS do que criou a
    # heurística e que a confirmaram; antes contava passagens da consolidação
    # noturna, que validava por coocorrência de palavras — daí valores como 86
    # em heurísticas com zero confirmação real.
    return h.get("confidence", 0) * (1 + h.get("times_validated", 0))


def _evidence_tag(h):
    """Rótulo honesto da procedência. "validada Nx" era literalmente falso para
    95% do pool: N contava passagens do contador de palavras, não confirmações."""
    method = h.get("validation_method")
    tv = h.get("times_validated", 0) or 0
    if method == "declared":
        return f"confirmada {tv}x pelo agente"
    if method == "inferred" and tv:
        return f"corroborada {tv}x"
    return "registrada, não corroborada"


def _norm_agent(agent):
    a = agent.lower().lstrip("@")
    return a


def _stable_seed(text):
    """Hash estável entre processos. hash() nativo do Python é salgado por processo
    (PYTHONHASHSEED) — cada `python3 router.py` daria um sorteio diferente para o
    MESMO prompt. md5 garante o mesmo sorteio sempre que o texto for o mesmo."""
    digest = hashlib.md5((text or "").encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _parse_dt(ts):
    """Parse defensivo de timestamp ISO. O pipeline noturno às vezes grava
    '+00:00Z' (offset e Z juntos, malformado) — normaliza antes do fromisoformat.
    Retorna None em qualquer formato inesperado (nunca levanta exceção)."""
    if not ts or not isinstance(ts, str):
        return None
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1]
        if not re.search(r"[+-]\d{2}:\d{2}$", s):
            s += "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _recency_decay(h):
    """1.0 se validada há <30 dias, 0.7 se <90 dias, 0.4 acima — ou se a data
    faltar/vier corrompida (campo pode faltar; nunca derruba o sorteio)."""
    dt = _parse_dt(h.get("last_validated"))
    if dt is None:
        return 0.4
    days = (datetime.now(timezone.utc) - dt).days
    if days < 30:
        return 1.0
    if days < 90:
        return 0.7
    return 0.4


def _weight(h):
    """Peso do sorteio ponderado: confiança × log(1+validações) × recência.
    Confidence<=0 zera o peso (cai no fallback uniforme do sorteio)."""
    conf = h.get("confidence", 0) or 0
    if conf <= 0:
        return 0.0
    tv = h.get("times_validated", 0) or 0
    return conf * math.log(1 + tv) * _recency_decay(h)


def _weighted_sample(rng, items, weights, k):
    """Amostragem ponderada SEM reposição, sem numpy (Efraimidis-Spirakis seria
    mais elegante, mas para k<=6 e pool<=15 a remoção iterativa é simples e clara).
    Pesos todos <=0 → sorteio uniforme do que resta (nunca trava vazio)."""
    items = list(items)
    weights = list(weights)
    picked = []
    for _ in range(min(k, len(items))):
        total = sum(weights)
        if total <= 0:
            idx = rng.randrange(len(items))
        else:
            r = rng.uniform(0, total)
            acc = 0.0
            idx = len(items) - 1
            for i, w in enumerate(weights):
                acc += w
                if r <= acc:
                    idx = i
                    break
        picked.append(items.pop(idx))
        weights.pop(idx)
    return picked


def _select_weighted(matched_sorted, n, seed_text):
    """Seleciona até n heurísticas de uma lista já ordenada por score desc:
    os GUARANTEED_TOP primeiros entram sempre (exploração garantida do topo) e as
    vagas restantes são sorteadas (ponderado, sem reposição, determinístico por
    seed_text) entre os próximos SAMPLE_POOL candidatos — assim heurísticas fora
    do topo eterno também circulam."""
    guaranteed_n = min(GUARANTEED_TOP, n, len(matched_sorted))
    selected = list(matched_sorted[:guaranteed_n])

    remaining_slots = n - guaranteed_n
    pool = matched_sorted[guaranteed_n:guaranteed_n + SAMPLE_POOL]
    if remaining_slots > 0 and pool:
        rng = random.Random(_stable_seed(seed_text))
        weights = [_weight(h) for h in pool]
        selected.extend(_weighted_sample(rng, pool, weights, remaining_slots))
    return selected


def _heur_id(h):
    """ID de log para a heurística: usa o id se existir, senão hash curto do texto."""
    hid = h.get("id")
    if hid:
        return hid
    text = (h.get("heuristic") or "").strip()
    return "sha1:" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def _log_injection(kind, target, ids):
    """Registra uma injeção de heurísticas em INJECTED_LOG (append-only).

    Best-effort e fail-open: qualquer falha é ignorada — nunca deve quebrar
    a injeção nem adicionar latência perceptível ao hook.
    """
    try:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
            "kind": kind,  # "agent" ou "relevance"
            "agent_ou_relevance": target,
            "ids": ids,
        }
        with open(INJECTED_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _handle(h):
    """Sufixo curto do id, para o agente citar em --heuristic-applied/--heuristic-failed.

    Sem isto o agente só via o TEXTO da heurística e tinha que passar um fragmento,
    que colide com frequência ("quando" bate em centenas). ~10 chars de contexto por
    heurística compram um match exato no feedback.
    """
    hid = h.get("id") or ""
    return hid[-8:] if len(hid) > 8 else hid


def format_heuristics_for_agent(agent, seed_text=None):
    """Retorna bloco de injeção com heurísticas do agente, ou "" se nenhuma.

    GUARANTEED_TOP heurísticas por solidez sempre entram; as demais (até TOP_N)
    são sorteadas ponderadas entre os próximos candidatos — ver _select_weighted.
    seed_text determina o sorteio (passe o prompt completo para variar entre
    prompts do mesmo agente; sem seed_text, usa o próprio nome do agente).

    Efeito colateral best-effort: incrementa triggered_count das injetadas
    (reescrita atômica do JSONL). Falha de escrita não impede a injeção.
    """
    try:
        target = _norm_agent(agent)
        recs = _load()
    except Exception:
        return ""

    matched = [
        h for h in recs
        if _norm_agent(h.get("agent", "")) == target
        and h.get("confidence", 0) >= MIN_CONFIDENCE
    ]
    if not matched:
        return ""

    matched.sort(key=_score, reverse=True)
    top = _select_weighted(matched, TOP_N, seed_text or agent)

    lines = [f"[Heurísticas @{target} — aplique se relevante]"]
    top_ids = set()
    for h in top:
        txt = (h.get("heuristic") or "").strip()
        if len(txt) > MAX_TEXT:
            txt = txt[:MAX_TEXT].rstrip() + "…"
        tv = h.get("times_validated", 0)
        lines.append(f"  • {txt} [{_evidence_tag(h)} · #{_handle(h)}]")
        top_ids.add(h.get("id"))

    # Fecha o loop de medição: marca uso real. Best-effort, atômico.
    try:
        changed = False
        for h in recs:
            if h.get("id") in top_ids:
                h["triggered_count"] = h.get("triggered_count", 0) + 1
                changed = True
        if changed:
            tmp = HEUR_PATH.with_suffix(".jsonl.tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                for h in recs:
                    fh.write(json.dumps(h, ensure_ascii=False) + "\n")
            tmp.replace(HEUR_PATH)
    except Exception:
        pass

    _log_injection("agent", target, [_heur_id(h) for h in top])

    return "\n".join(lines)


_STOPWORDS = {
    "como", "para", "você", "voce", "pode", "quero", "preciso", "fazer", "criar",
    "qual", "quais", "onde", "está", "esta", "esse", "essa", "isso", "algo", "sobre",
    "nosso", "nossa", "todos", "todo", "toda", "mais", "menos", "muito", "muita",
    "agora", "depois", "antes", "ainda", "também", "vamos", "deixa", "manda", "roda",
    "execute", "mostra", "quando", "porque", "sendo", "temos", "tenho", "seria",
}


def format_heuristics_by_relevance(prompt_lower):
    """Retorna heurísticas relevantes ao CONTEÚDO do prompt (não exige @agent).

    Recupera por relevância semântica: keywords do prompt cruzadas com a solidez
    da heurística. Fecha o loop write→read no modo conversacional — a maioria das
    mensagens não cita @agent, então antes as heurísticas nunca eram injetadas.
    GUARANTEED_TOP por relevância sempre entram; as demais (até TOP_N_RELEVANCE)
    são sorteadas ponderadas — ver _select_weighted. Sorteio determinístico pelo
    próprio prompt (mesmo prompt → mesmo conjunto; prompts diferentes variam).
    Efeito colateral best-effort: incrementa triggered_count + grava last_triggered.
    """
    try:
        words = {w for w in re.findall(r"\w+", prompt_lower or "")
                 if len(w) > 3 and w not in _STOPWORDS}
        if not words:
            return ""
        recs = _load()
    except Exception:
        return ""

    scored = []
    for h in recs:
        if (h.get("confidence", 0) or 0) < MIN_CONFIDENCE:
            continue
        text = (h.get("heuristic") or "").lower()
        matches = sum(1 for w in words if w in text)
        if matches == 0:
            continue
        solidez = h.get("confidence", 0) * (1 + h.get("times_validated", 0))
        scored.append((matches * solidez, h))

    if not scored:
        return ""
    scored.sort(key=lambda x: x[0], reverse=True)
    candidates = [h for _, h in scored]
    top = _select_weighted(candidates, TOP_N_RELEVANCE, prompt_lower)

    lines = ["[Heurísticas relevantes ao contexto — aplique se fizer sentido]"]
    top_ids = set()
    for h in top:
        txt = (h.get("heuristic") or "").strip()
        if len(txt) > MAX_TEXT:
            txt = txt[:MAX_TEXT].rstrip() + "…"
        lines.append(f"  • {txt} [{h.get('agent', '')}, {_evidence_tag(h)} · #{_handle(h)}]")
        top_ids.add(h.get("id"))

    # Fecha o loop de medição: uso real + timestamp (corrige o last_triggered nulo)
    try:
        now = datetime.now(timezone.utc).isoformat()
        changed = False
        for h in recs:
            if h.get("id") in top_ids:
                h["triggered_count"] = (h.get("triggered_count", 0) or 0) + 1
                h["last_triggered"] = now
                changed = True
        if changed:
            tmp = HEUR_PATH.with_suffix(".jsonl.tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                for h in recs:
                    fh.write(json.dumps(h, ensure_ascii=False) + "\n")
            tmp.replace(HEUR_PATH)
    except Exception:
        pass

    _log_injection("relevance", (prompt_lower or "")[:100], [_heur_id(h) for h in top])

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    arg = sys.argv[1] if len(sys.argv) > 1 else "@dev"
    if arg.startswith("@"):
        out = format_heuristics_for_agent(arg)
    else:
        out = format_heuristics_by_relevance(arg.lower())
    print(out or "(nenhuma heurística relevante)")
