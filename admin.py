from flask import Blueprint, g, jsonify, request

import audit
from auth import login_required
from db import get_db

bp = Blueprint("admin", __name__)


def _admin_only():
    if g.user["role"] != "admin":
        audit.log(g.user["id"], "admin_area", None, "denied")
        return jsonify(error="forbidden"), 403
    return None


@bp.get("/admin/audit")
@login_required
def audit_list():
    blocked = _admin_only()
    if blocked:
        return blocked
    limit = min(request.args.get("limit", 100, type=int), 500)
    result = request.args.get("result", "")[:32]
    kind = request.args.get("kind", "")[:32]

    where, args = [], []
    if result:
        where.append("a.result = ?")
        args.append(result)
    if kind == "permissions":
        where.append("(a.action LIKE 'grant%' OR a.action LIKE 'revoke%')")
    sql = (
        "SELECT a.id, a.time, u.username AS user, a.action, a.doc_id, a.result "
        "FROM audit_log a LEFT JOIN users u ON u.id = a.user_id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY a.id DESC LIMIT ?"
    args.append(limit)

    conn = get_db()
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@bp.get("/admin/audit/verify")
@login_required
def audit_verify():
    blocked = _admin_only()
    if blocked:
        return blocked
    return jsonify(audit.verify())


@bp.get("/admin/flagged")
@login_required
def flagged():
    """Users with 3 or more refused attempts: worth a look."""
    blocked = _admin_only()
    if blocked:
        return blocked
    conn = get_db()
    rows = conn.execute(
        "SELECT u.username AS user, COUNT(*) AS refused FROM audit_log a "
        "JOIN users u ON u.id = a.user_id WHERE a.result != 'ok' "
        "GROUP BY u.username HAVING COUNT(*) >= 3 ORDER BY refused DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
from werkzeug.security import generate_password_hash


@bp.post("/admin/users")
@login_required
def create_user():
    blocked = _admin_only()
    if blocked:
        return blocked
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()[:64]
    password = str(data.get("password", ""))[:128]
    role = data.get("role")
    if not username or len(password) < 8 or role not in ("owner", "viewer", "admin"):
        return jsonify(error="username, password (8+ chars) and role required"), 400
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
            (username, generate_password_hash(password), role),
        )
        conn.commit()
    except Exception:
        conn.close()
        return jsonify(error="username already exists"), 409
    conn.close()
    audit.log(g.user["id"], f"create_user_{username}_{role}", None, "ok")
    return jsonify(message="user created"), 201