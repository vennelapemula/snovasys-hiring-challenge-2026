import hashlib

from db import get_db


def log(user_id, action, doc_id, result):
    """Append one audit row. Every allowed AND refused attempt goes here."""
    conn = get_db()
    try:
        last = conn.execute(
            "SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        prev = last["hash"] if last else "GENESIS"
        raw = f"{prev}|{user_id}|{action}|{doc_id}|{result}"
        h = hashlib.sha256(raw.encode()).hexdigest()
        conn.execute(
            "INSERT INTO audit_log (user_id, action, doc_id, result, prev_hash, hash) "
            "VALUES (?,?,?,?,?,?)",
            (user_id, action, doc_id, result, prev, h),
        )
        conn.commit()
    finally:
        conn.close()