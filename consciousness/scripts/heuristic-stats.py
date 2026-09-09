#!/usr/bin/env python3
"""heuristic-stats — Estatísticas do pool de heurísticas para o @heuristic-curator.

Criado 16-Jul-2026: o agente heuristic-curator invocava este script
(`heuristic-stats.py --dormant-since 30`) mas ele não existia — a curadoria
não tinha como listar heurísticas dormentes.

Complementa heuristic_validator.py (que recalibra confidence por evidência):
este aqui apenas RELATA, não altera nada.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

HEUR = Path.home() / "consciousness" / "memory" / "procedural" / "heuristics.jsonl"


def load():
    return [json.loads(l) for l in HEUR.read_text().splitlines() if l.strip()]


def days_since(ts):
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except (ValueError, AttributeError):
        return None


def main():
    p = argparse.ArgumentParser(description="Estatísticas do pool de heurísticas")
    p.add_argument("--dormant-since", type=int, metavar="DAYS",
                   help="lista heurísticas sem validação há mais de DAYS dias")
    p.add_argument("--summary", action="store_true", help="sumário do pool")
    args = p.parse_args()

    hs = load()

    if args.dormant_since:
        cut = args.dormant_since
        dormant = []
        for h in hs:
            d = days_since(h.get("last_validated") or h.get("created"))
            if d is not None and d >= cut:
                dormant.append((d, h))
        dormant.sort(key=lambda x: x[0], reverse=True)  # só por dias; dicts não são comparáveis
        print(f"Heurísticas dormentes há >= {cut} dias: {len(dormant)}\n")
        for d, h in dormant:
            conf = h.get("confidence", "?")
            method = h.get("validation_method", "?")
            print(f"  {d:>4}d  conf={conf}  [{method}]  {h.get('agent','')}: {(h.get('heuristic','') or '')[:64]}")
        return

    # Default: sumário
    total = len(hs)
    by_method = {}
    for h in hs:
        m = h.get("validation_method", "unvalidated")
        by_method[m] = by_method.get(m, 0) + 1
    # "confidence < 0.5" NÃO é refutação — é decaimento por tempo. Chamar isso de
    # refutada levou a leitura errada da saúde do pool em 04-Set-2026: 242 apareciam
    # como refutadas sem que UMA sequer tivesse falhado. Refutação real é times_failed.
    corroborated = len([h for h in hs if h.get("confidence", 0) > 0.5])
    decaidas = len([h for h in hs if h.get("confidence", 1) < 0.5])
    refuted = len([h for h in hs if (h.get("times_failed") or 0) > 0])
    validadas = len([h for h in hs if (h.get("times_validated") or 0) > 1])
    nunca_disp = len([h for h in hs if not (h.get("triggered_count") or 0)])

    print(f"Pool de heurísticas: {total}")
    print(f"  corroboradas (conf >0.5):     {corroborated}")
    print(f"  decaídas por tempo (conf<0.5): {decaidas}")
    print(f"  REFUTADAS (times_failed>0):    {refuted}"
          + ("   ← zero indica que o loop de contra-evidência não fecha" if refuted == 0 else ""))
    print(f"  validadas (times_validated>1): {validadas}"
          + ("   ← só o heuristic_validator escreve este campo" if validadas <= 5 else ""))
    print(f"  nunca recuperadas em runtime:  {nunca_disp}")
    print(f"  por método de validação:")
    for m, n in sorted(by_method.items(), key=lambda x: -x[1]):
        print(f"    {m:16s} {n}")


if __name__ == "__main__":
    main()
