import hashlib
from datetime import datetime, timezone

from db import get_db


def _hash(prev, t, user_id, action, doc_id, result):
    raw = f"{prev}|{t}|{user_id}|{action}|{doc_id}|{result}"
    return hashlib.sha256(raw.encode()).hexdigest()


def log(user_id, action, doc_id, result):
    """Append one audit row. Allowed AND refused attempts both go here."""
    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        last = conn.execute(
            "SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev = last["hash"] if last else "GENESIS"
        t = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        h = _hash(prev, t, user_id, action, doc_id, result)
        conn.execute(
            "INSERT INTO audit_log (time, user_id, action, doc_id, result, prev_hash, hash) "
            "VALUES (?,?,?,?,?,?,?)",
            (t, user_id, action, doc_id, result, prev, h),
        )
        conn.commit()
    finally:
        conn.close()


def verify():
    """Recompute the whole chain. Any edited row breaks it."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM audit_log ORDER BY id").fetchall()
    conn.close()
    prev = "GENESIS"
    for r in rows:
        want = _hash(prev, r["time"], r["user_id"], r["action"], r["doc_id"], r["result"])
        if r["prev_hash"] != prev or r["hash"] != want:
            return {"ok": False, "broken_at": r["id"], "rows": len(rows)}
        prev = r["hash"]
    return {"ok": True, "rows": len(rows)}