#!/usr/bin/env python3
"""sf-merge-jsonl — união de dois JSONL/JSON-array por `id`, ordem por timestamp.

Usado pelo sf-sync.sh para arquivos que têm DOIS escritores legítimos
(episódios gravados por sessões no Mac e por crons na VPS; sinais e mailbox
emitidos dos dois lados). Regra: união por id; em conflito de conteúdo para o
mesmo id, vence o registro mais recente por `timestamp`/`ts`/`updated_at`.

Uso:
  sf-merge-jsonl.py jsonl  <local> <remoto> <saída>
  sf-merge-jsonl.py signals <local> <remoto> <saída>      # lista JSON com ids
  sf-merge-jsonl.py mailbox <local> <remoto> <saída>      # {"agent","inbox":[...]}
Exit 0 sempre que conseguiu escrever a saída; 2 em erro de parse.
"""
import json
import sys
from pathlib import Path


def _ts(r):
    for k in ("timestamp", "ts", "updated_at", "created", "created_at"):
        v = r.get(k)
        if v:
            return str(v)
    return ""


INVALID = 0


def _load_lines(p):
    global INVALID
    out = []
    if not Path(p).exists():
        return out
    for line in Path(p).read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            INVALID += 1
            sys.stderr.write(f"[merge] linha inválida ignorada em {p}\n")
    return out


def _load_json(p, default):
    try:
        return json.loads(Path(p).read_text(errors="ignore")) if Path(p).exists() else default
    except json.JSONDecodeError:
        return default


def _rank(r):
    """Ordem de vitória em conflito: (1) timestamp/updated_at mais novo, (2) já processado
    vence raw (auditoria Codex 07-Set: empate devolvia o raw do Mac por cima do processed)."""
    return (_ts(r), max(str(r.get("updated_at", "")), str(r.get("processed_at", ""))),
            1 if r.get("consolidation_status") == "processed" else 0)


def _merge_lists(dst, src):
    for k, v in src.items():
        if isinstance(v, list) and isinstance(dst.get(k), list):
            seen = set(json.dumps(x, sort_keys=True) for x in dst[k])
            dst[k] = dst[k] + [x for x in v if json.dumps(x, sort_keys=True) not in seen]
    return dst


def merge_records(a, b):
    by = {}
    order = []
    for r in a + b:
        if not isinstance(r, dict):
            continue
        k = r.get("id") or json.dumps(r, sort_keys=True)[:200]
        if k in by:
            win, lose = (r, by[k]) if _rank(r) > _rank(by[k]) else (by[k], r)
            by[k] = _merge_lists(dict(win), lose)   # listas (consumed_by, participants…) = união
        else:
            by[k] = r
            order.append(k)
    recs = [by[k] for k in order]
    recs.sort(key=_ts)
    return recs


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    kind, local, remoto, saida = sys.argv[1:]
    if kind == "jsonl":
        recs = merge_records(_load_lines(local), _load_lines(remoto))
        # separators compactos: consolidate.sh procura a substring '"consolidation_status":"raw"'
        # (07-Set: 43 episódios raw, 0 reconhecidos porque o merger gravava com espaço)
        Path(saida).write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in recs))
    elif kind == "signals":
        la, lb = _load_json(local, []), _load_json(remoto, [])
        la = la.get("signals", []) if isinstance(la, dict) else la
        lb = lb.get("signals", []) if isinstance(lb, dict) else lb
        Path(saida).write_text(json.dumps(merge_records(la, lb), ensure_ascii=False, indent=1))
    elif kind == "mailbox":
        da, db = _load_json(local, {}), _load_json(remoto, {})
        inbox = merge_records(da.get("inbox", []) or [], db.get("inbox", []) or [])
        out = dict(db) if db else dict(da)
        out.update({"agent": da.get("agent") or db.get("agent"), "inbox": inbox})
        lc = max(str(da.get("last_checked", "")), str(db.get("last_checked", "")))
        if lc:
            out["last_checked"] = lc
        Path(saida).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print("tipo desconhecido:", kind)
        return 2
    return 3 if INVALID else 0   # 3 = saída escrita, mas houve linha inválida (não silencia)


if __name__ == "__main__":
    sys.exit(main())
