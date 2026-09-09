#!/usr/bin/env python3
"""heuristic-loop-stop.py — Hook Stop que fecha o loop de heurísticas.

Problema medido (05-Set-2026): 0 de 80 episódios em 7 dias citavam o #handle de
uma heurística injetada, embora a rule operating-protocol exija. Rule não
fecha loop; código fecha. No fim da resposta, este hook:

  1. lê o transcript e coleta os #handles injetados na sessão;
  2. procura episódios gravados na janela desta sessão sem
     `heuristic_applied` / `heuristic_failed`;
  3. se houver handles E episódio sem citação, devolve `decision: block` UMA vez,
     com a lista, para o agente fechar (record-episode --heuristic-applied /
     --heuristic-failed, ou declarar "nenhuma se aplicou").

Nunca bloqueia duas vezes na mesma sessão (stop_hook_active + arquivo de estado).
Falha silenciosa: qualquer erro → exit 0 sem bloquear.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path.home()
EPIS = HOME / "consciousness" / "memory" / "episodic"
STATE = HOME / ".claude" / ".heuristic-loop-state"
JANELA = 6 * 3600  # episódios gravados nas últimas 6h contam como "desta sessão"


def episodios_pendentes(agora):
    pendentes = []
    if not EPIS.exists():
        return pendentes
    for f in EPIS.glob("*.jsonl"):
        if agora - f.stat().st_mtime > JANELA:
            continue
        for line in f.read_text(errors="ignore").splitlines()[-20:]:
            try:
                d = json.loads(line)
            except Exception:
                continue
            ts = d.get("timestamp", "")
            try:
                t = time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
            except Exception:
                continue
            if agora - t > JANELA:
                continue
            les = d.get("lessons", {}) or {}
            if not (les.get("heuristic_applied") or les.get("heuristic_failed") or d.get("loop_closed")):
                pendentes.append(d.get("id", "?"))
    return pendentes


def main():
    if os.environ.get("SF_AUTOMATED"):
        return 0  # chamada automatizada (claude -p do Ciclo de Evolução etc.): sem loop humano
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    if payload.get("stop_hook_active"):
        return 0  # já estamos continuando por causa de um hook: nunca encadear
    sid = payload.get("session_id", "")
    tp = payload.get("transcript_path", "")
    if not sid or not tp or not Path(tp).exists():
        return 0
    STATE.mkdir(exist_ok=True)
    marker = STATE / sid
    if marker.exists():
        return 0  # 1 bloqueio por sessão
    txt = Path(tp).read_text(errors="ignore")
    handles = sorted(set(re.findall(r"·\s*#([0-9a-f]{8})\b", txt)))
    if not handles:
        return 0
    agora = time.time()
    pendentes = episodios_pendentes(agora)
    if not pendentes:
        return 0
    marker.write_text(time.strftime("%Y-%m-%dT%H:%M:%S"))
    reason = (
        "[heuristic-loop] Episódio(s) desta sessão sem fechamento de loop: "
        + ", ".join(pendentes[:3])
        + f". Heurísticas injetadas na sessão: {' '.join('#' + h for h in handles[:8])}. "
        "Antes de encerrar: se alguma guiou a tarefa, rode "
        "`~/consciousness/scripts/record-episode.sh ... --heuristic-applied '#handle'` "
        "(ou `--heuristic-failed`); se nenhuma se aplicou, diga 'nenhuma heurística se aplicou' "
        "em uma linha e encerre."
    )
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
