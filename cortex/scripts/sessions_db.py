#!/usr/bin/env python3
"""
sessions_db.py — SQLite FTS5 session search

Indexa em ~/cortex/sessions.db:
- Episódios de ~/consciousness/memory/episodic/*.jsonl
- Mailbox messages de ~/broadcast/mailbox/*.json
- Signals de ~/broadcast/signals.json (histórico)
- Transcripts opcionais de ~/.claude/projects/*/sessions/ (se houver)

3 modos de busca (adaptado de hermes-agent/tools/session_search_tool.py):
- DISCOVERY: query → top N hits com snippet + contexto
- SCROLL: id específico → janela de mensagens próximas
- BROWSE: sem args → recentes cronológicas

Uso:
    python3 ~/cortex/scripts/sessions_db.py rebuild           # reconstroi DB
    python3 ~/cortex/scripts/sessions_db.py search "termo"    # discovery
    python3 ~/cortex/scripts/sessions_db.py browse            # recentes
    python3 ~/cortex/scripts/sessions_db.py stats             # estatísticas

Origem: hermes-agent FTS5 pattern adaptado para SF (sem dependência de hermes_state).
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
DB_PATH = HOME / "cortex" / "sessions.db"
EPISODIC_DIR = HOME / "consciousness" / "memory" / "episodic"
MAILBOX_DIR = HOME / "broadcast" / "mailbox"
SIGNALS_PATH = HOME / "broadcast" / "signals.json"
SESSIONS_DIR = HOME / ".claude" / "projects"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    source_type TEXT NOT NULL,     -- episodic | mailbox | signal | transcript
    source_id TEXT,                -- agent name, mailbox owner, signal id
    timestamp TEXT,
    agent TEXT,
    role TEXT,
    content TEXT,
    metadata TEXT                  -- JSON blob com extras
);

CREATE VIRTUAL TABLE IF NOT EXISTS sources_fts USING fts5(
    content,
    agent,
    source_type,
    content='sources',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS sources_ai AFTER INSERT ON sources BEGIN
    INSERT INTO sources_fts(rowid, content, agent, source_type)
    VALUES (new.id, new.content, new.agent, new.source_type);
END;

CREATE TRIGGER IF NOT EXISTS sources_ad AFTER DELETE ON sources BEGIN
    INSERT INTO sources_fts(sources_fts, rowid, content, agent, source_type)
    VALUES('delete', old.id, old.content, old.agent, old.source_type);
END;

CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_agent ON sources(agent);
CREATE INDEX IF NOT EXISTS idx_sources_ts ON sources(timestamp);
"""


def get_db():
    """Conecta + cria schema se necessário."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def rebuild_db():
    """Limpa e reindexa de todas as fontes."""
    print("🔄 Rebuilding sessions.db...", file=sys.stderr)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = get_db()
    cur = conn.cursor()

    total = 0

    # 1. Episodic memories
    if EPISODIC_DIR.exists():
        for jsonl in EPISODIC_DIR.glob("*.jsonl"):
            agent = jsonl.stem
            with jsonl.open() as f:
                for line in f:
                    try:
                        ep = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    summary = ep.get("summary", "")
                    lessons = ep.get("lessons") or {}
                    heuristic = lessons.get("heuristic") or ""
                    worked = lessons.get("what_worked") or ""
                    failed = lessons.get("what_failed") or ""
                    content = " ".join(filter(None, [summary, heuristic, worked, failed]))
                    if not content:
                        continue
                    cur.execute(
                        "INSERT INTO sources(source_type, source_id, timestamp, agent, role, content, metadata) "
                        "VALUES('episodic', ?, ?, ?, 'agent', ?, ?)",
                        (
                            ep.get("id"),
                            ep.get("timestamp"),
                            agent,
                            content,
                            json.dumps({"type": ep.get("type"), "result": ep.get("outcome", {}).get("result")}),
                        ),
                    )
                    total += 1

    # 2. Mailbox
    if MAILBOX_DIR.exists():
        for mb in MAILBOX_DIR.glob("*.json"):
            agent = mb.stem
            try:
                data = json.loads(mb.read_text())
                if isinstance(data, dict):
                    data = [data]
            except (json.JSONDecodeError, OSError):
                continue
            for msg in data if isinstance(data, list) else []:
                content_parts = [
                    msg.get("subject", ""),
                    msg.get("body", "")
                ]
                content = " — ".join(filter(None, content_parts))
                if not content:
                    continue
                cur.execute(
                    "INSERT INTO sources(source_type, source_id, timestamp, agent, role, content, metadata) "
                    "VALUES('mailbox', ?, ?, ?, ?, ?, ?)",
                    (
                        msg.get("id"),
                        msg.get("timestamp"),
                        agent,
                        msg.get("from", ""),
                        content,
                        json.dumps({"type": msg.get("type"), "priority": msg.get("priority")}),
                    ),
                )
                total += 1

    # 3. Signals
    if SIGNALS_PATH.exists():
        try:
            signals = json.loads(SIGNALS_PATH.read_text())
            if isinstance(signals, dict):
                signals = signals.get("signals", []) or list(signals.values())
        except (json.JSONDecodeError, OSError):
            signals = []
        for sig in signals if isinstance(signals, list) else []:
            content = " — ".join(filter(None, [
                sig.get("type", ""),
                sig.get("message", ""),
                str(sig.get("payload", "")),
            ]))
            if not content:
                continue
            cur.execute(
                "INSERT INTO sources(source_type, source_id, timestamp, agent, role, content, metadata) "
                "VALUES('signal', ?, ?, ?, 'system', ?, ?)",
                (
                    sig.get("id"),
                    sig.get("timestamp") or sig.get("created_at"),
                    sig.get("from") or sig.get("source", ""),
                    content,
                    json.dumps({"severity": sig.get("severity"), "scope": sig.get("scope")}),
                ),
            )
            total += 1

    conn.commit()
    conn.close()
    print(f"✅ Indexed {total} entries to {DB_PATH}", file=sys.stderr)
    return total


def search(query: str, limit: int = 10, source_type: str = None,
           agent: str = None) -> list:
    """DISCOVERY mode — FTS5 search."""
    conn = get_db()
    cur = conn.cursor()
    where_extra = []
    params = [query]
    if source_type:
        where_extra.append("s.source_type = ?")
        params.append(source_type)
    if agent:
        where_extra.append("s.agent = ?")
        params.append(agent)
    extra_sql = ""
    if where_extra:
        extra_sql = " AND " + " AND ".join(where_extra)
    params.append(limit)

    sql = f"""
        SELECT s.id, s.source_type, s.source_id, s.timestamp, s.agent, s.role,
               snippet(sources_fts, 0, '<mark>', '</mark>', '…', 32) AS snippet,
               s.content, s.metadata
        FROM sources_fts
        JOIN sources s ON s.id = sources_fts.rowid
        WHERE sources_fts MATCH ?{extra_sql}
        ORDER BY rank
        LIMIT ?
    """
    try:
        rows = cur.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        print(f"⚠️  FTS5 query error: {e}", file=sys.stderr)
        rows = []
    conn.close()
    return [dict(r) for r in rows]


def browse(limit: int = 10) -> list:
    """BROWSE mode — recentes cronológicos."""
    conn = get_db()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, source_type, source_id, timestamp, agent, role, "
        "substr(content, 1, 200) || '...' AS preview, metadata "
        "FROM sources ORDER BY timestamp DESC NULLS LAST, id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def context(source_id: int, window: int = 3) -> dict:
    """SCROLL mode — janela de entries em torno de source_id."""
    conn = get_db()
    cur = conn.cursor()
    pivot = cur.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    if not pivot:
        conn.close()
        return {"error": f"id {source_id} not found"}
    around = cur.execute(
        "SELECT id, source_type, agent, timestamp, substr(content, 1, 300) AS preview "
        "FROM sources WHERE id BETWEEN ? AND ? ORDER BY id",
        (source_id - window, source_id + window),
    ).fetchall()
    conn.close()
    return {
        "pivot": dict(pivot),
        "window": [dict(r) for r in around],
        "before": sum(1 for r in around if r["id"] < source_id),
        "after": sum(1 for r in around if r["id"] > source_id),
    }


def stats() -> dict:
    """Estatísticas do DB."""
    conn = get_db()
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    by_type = cur.execute("SELECT source_type, COUNT(*) FROM sources GROUP BY source_type").fetchall()
    by_agent = cur.execute(
        "SELECT agent, COUNT(*) FROM sources WHERE agent IS NOT NULL GROUP BY agent ORDER BY 2 DESC LIMIT 15"
    ).fetchall()
    db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    conn.close()
    return {
        "total_entries": total,
        "by_type": {t: c for t, c in by_type},
        "top_agents": {a: c for a, c in by_agent},
        "db_size_bytes": db_size,
        "db_size_human": f"{db_size / 1024:.1f}KB" if db_size < 1024*1024 else f"{db_size / (1024*1024):.1f}MB",
    }


def cmd_search(args):
    results = search(args.query, limit=args.limit,
                     source_type=args.type, agent=args.agent)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    print(f"\n🔍 Found {len(results)} matches for '{args.query}':\n")
    for r in results:
        ts = r["timestamp"] or "?"
        agent = r["agent"] or "system"
        print(f"  [{r['source_type']:9s}] @{agent} — {ts}")
        print(f"    {r['snippet']}")
        print(f"    (id={r['id']}, source_id={r['source_id']})")
        print()


def cmd_browse(args):
    results = browse(limit=args.limit)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    print(f"\n📚 Recent {len(results)} entries:\n")
    for r in results:
        ts = r["timestamp"] or "?"
        agent = r["agent"] or "system"
        print(f"  [{r['source_type']:9s}] @{agent} — {ts}")
        print(f"    {r['preview']}")
        print()


def cmd_context(args):
    result = context(args.id, window=args.window)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if "error" in result:
        print(result["error"])
        return
    pivot = result["pivot"]
    print(f"\n🎯 Context window around id={args.id} (±{args.window}):\n")
    for r in result["window"]:
        marker = "→" if r["id"] == args.id else " "
        print(f"  {marker} [{r['id']:5d}] {r['source_type']:9s} @{r['agent']} — {r['timestamp']}")
        print(f"      {r['preview']}")
        print()


def cmd_stats(args):
    s = stats()
    if args.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return
    print("\n📊 Sessions DB Stats:")
    print(f"  Total entries: {s['total_entries']}")
    print(f"  DB size:       {s['db_size_human']}")
    print(f"\n  By source type:")
    for t, c in s["by_type"].items():
        print(f"    {t:12s} {c}")
    print(f"\n  Top agents (by entries):")
    for a, c in s["top_agents"].items():
        print(f"    @{a:25s} {c}")


def main():
    parser = argparse.ArgumentParser(description="FTS5 session search para SF")
    sub = parser.add_subparsers(dest="cmd")

    p_rebuild = sub.add_parser("rebuild", help="Reconstroi o DB a partir das fontes")

    p_search = sub.add_parser("search", help="Busca FTS5 (DISCOVERY mode)")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.add_argument("--type", help="Filtrar por source_type")
    p_search.add_argument("--agent", help="Filtrar por agente")
    p_search.add_argument("--json", action="store_true")

    p_browse = sub.add_parser("browse", help="Recentes (BROWSE mode)")
    p_browse.add_argument("--limit", type=int, default=10)
    p_browse.add_argument("--json", action="store_true")

    p_ctx = sub.add_parser("context", help="Janela em torno de id (SCROLL mode)")
    p_ctx.add_argument("id", type=int)
    p_ctx.add_argument("--window", type=int, default=3)
    p_ctx.add_argument("--json", action="store_true")

    p_stats = sub.add_parser("stats", help="Estatísticas do DB")
    p_stats.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.cmd is None:
        parser.print_help()
        return 1

    if args.cmd == "rebuild":
        rebuild_db()
    elif args.cmd == "search":
        cmd_search(args)
    elif args.cmd == "browse":
        cmd_browse(args)
    elif args.cmd == "context":
        cmd_context(args)
    elif args.cmd == "stats":
        cmd_stats(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
