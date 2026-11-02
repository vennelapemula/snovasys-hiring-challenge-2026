import os
import uuid

from flask import Blueprint, g, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

import audit
from auth import login_required
from db import get_db
from permissions import can

bp = Blueprint("documents", __name__)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED = {"pdf", "txt", "png", "jpg", "jpeg", "docx", "xlsx"}


def _not_found():
    # same answer for "missing", "deleted" and "not yours"
    return jsonify(error="not found"), 404


@bp.post("/documents")
@login_required
def upload():
    if g.user["role"] not in ("owner", "admin"):
        audit.log(g.user["id"], "upload", None, "denied")
        return jsonify(error="forbidden"), 403

    f = request.files.get("file")
    if f is None or not f.filename:
        return jsonify(error="file required"), 400

    clean = secure_filename(f.filename)
    ext = clean.rsplit(".", 1)[-1].lower() if "." in clean else ""
    if ext not in ALLOWED:
        audit.log(g.user["id"], "upload", None, "rejected_type")
        return jsonify(error="file type not allowed"), 400

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored = uuid.uuid4().hex + "." + ext
    f.save(os.path.join(UPLOAD_DIR, stored))

    category = str(request.form.get("category", ""))[:64]
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO documents (owner_id, name, category, stored_name) VALUES (?,?,?,?)",
        (g.user["id"], clean, category, stored),
    )
    doc_id = cur.lastrowid
    conn.commit()
    conn.close()
    audit.log(g.user["id"], "upload", doc_id, "ok")
    return jsonify(id=doc_id, name=clean), 201


@bp.get("/documents")
@login_required
def list_documents():
    # permission filter is inside the query: you only see what you own or hold a live grant for
    q = request.args.get("q", "")[:64]
    category = request.args.get("category", "")[:64]
    owner = request.args.get("owner", "")[:64]
    since = request.args.get("since", "")[:32]

    sql = (
        "SELECT d.id, d.name, d.category, d.created_at, u.username AS owner "
        "FROM documents d JOIN users u ON u.id = d.owner_id "
        "WHERE d.deleted_at IS NULL AND (d.owner_id = ? OR EXISTS ("
        "  SELECT 1 FROM grants g WHERE g.doc_id = d.id AND g.user_id = ? "
        "  AND g.revoked_at IS NULL)) "
    )
    args = [g.user["id"], g.user["id"]]
    if q:
        sql += "AND d.name LIKE ? "
        args.append("%" + q + "%")
    if category:
        sql += "AND d.category = ? "
        args.append(category)
    if owner:
        sql += "AND u.username = ? "
        args.append(owner)
    if since:
        sql += "AND d.created_at >= ? "
        args.append(since)
    sql += "ORDER BY d.id DESC LIMIT 100"

    conn = get_db()
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@bp.get("/documents/<int:doc_id>/download")
@login_required
def download(doc_id):
    # THE authorization decision for downloads. Remove this check and everything leaks.
    if not can(g.user, doc_id, "read"):
        audit.log(g.user["id"], "download", doc_id, "denied")
        return _not_found()

    conn = get_db()
    doc = conn.execute(
        "SELECT name, stored_name FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()
    conn.close()
    audit.log(g.user["id"], "download", doc_id, "ok")
    return send_from_directory(
        UPLOAD_DIR, doc["stored_name"], as_attachment=True, download_name=doc["name"]
    )


@bp.post("/documents/<int:doc_id>/grants")
@login_required
def grant(doc_id):
    if not can(g.user, doc_id, "share"):
        audit.log(g.user["id"], "grant", doc_id, "denied")
        return _not_found()

    data = request.get_json(silent=True) or {}
    username = str(data.get("username", ""))[:64]
    level = data.get("level")
    if level not in ("read", "edit"):
        return jsonify(error="level must be read or edit"), 400

    conn = get_db()
    target = conn.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if target is None:
        conn.close()
        return jsonify(error="user not found"), 404
    if target["id"] == g.user["id"]:
        conn.close()
        return jsonify(error="you already own this document"), 400

    # one live grant per person: close the old one first
    conn.execute(
        "UPDATE grants SET revoked_at = CURRENT_TIMESTAMP "
        "WHERE doc_id = ? AND user_id = ? AND revoked_at IS NULL",
        (doc_id, target["id"]),
    )
    conn.execute(
        "INSERT INTO grants (doc_id, user_id, level) VALUES (?,?,?)",
        (doc_id, target["id"], level),
    )
    conn.commit()
    conn.close()
    audit.log(g.user["id"], f"grant_{level}_to_{username}", doc_id, "ok")
    return jsonify(message="granted"), 201


@bp.delete("/documents/<int:doc_id>/grants/<username>")
@login_required
def revoke(doc_id, username):
    if not can(g.user, doc_id, "share"):
        audit.log(g.user["id"], "revoke", doc_id, "denied")
        return _not_found()

    conn = get_db()
    target = conn.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if target is not None:
        conn.execute(
            "UPDATE grants SET revoked_at = CURRENT_TIMESTAMP "
            "WHERE doc_id = ? AND user_id = ? AND revoked_at IS NULL",
            (doc_id, target["id"]),
        )
        conn.commit()
    conn.close()
    audit.log(g.user["id"], f"revoke_{username}", doc_id, "ok")
    return jsonify(message="revoked")


@bp.delete("/documents/<int:doc_id>")
@login_required
def delete(doc_id):
    if not can(g.user, doc_id, "delete"):
        audit.log(g.user["id"], "delete", doc_id, "denied")
        return _not_found()

    conn = get_db()
    conn.execute(
        "UPDATE documents SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?", (doc_id,)
    )
    conn.commit()
    conn.close()
    audit.log(g.user["id"], "delete", doc_id, "ok")
    return jsonify(message="deleted")