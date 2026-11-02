import os
import time
from functools import wraps

from flask import Blueprint, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

bp = Blueprint("auth", __name__)

DUMMY_HASH = generate_password_hash("dummy-password")
FAILS = {}  # username -> [count, first_fail_time]
MAX_FAILS = 5
WINDOW = 300  # seconds


def seed_users():
    conn = get_db()
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        pw = os.environ.get("SEED_PASSWORD", "LocalDemo-123")
        for name, role in [("admin1", "admin"), ("owner1", "owner"),
                           ("owner2", "owner"), ("viewer1", "viewer")]:
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                (name, generate_password_hash(pw), role),
            )
        conn.commit()
    conn.close()


@bp.before_app_request
def load_user():
    # Role is read from the DB on every request, never from the cookie.
    g.user = None
    uid = session.get("user_id")
    if uid is not None:
        conn = get_db()
        g.user = conn.execute(
            "SELECT id, username, role FROM users WHERE id = ?", (uid,)
        ).fetchone()
        conn.close()


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if g.user is None:
            return jsonify(error="login required"), 401
        return f(*a, **kw)
    return wrapper


def role_required(*roles):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **kw):
            if g.user is None:
                return jsonify(error="login required"), 401
            if g.user["role"] not in roles:
                return jsonify(error="forbidden"), 403
            return f(*a, **kw)
        return wrapper
    return deco


def _locked(username):
    rec = FAILS.get(username)
    if not rec:
        return False
    if time.time() - rec[1] > WINDOW:
        FAILS.pop(username, None)
        return False
    return rec[0] >= MAX_FAILS


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", ""))[:64]
    password = str(data.get("password", ""))[:128]

    if _locked(username):
        return jsonify(error="too many attempts, try later"), 429

    conn = get_db()
    row = conn.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    ok = check_password_hash(row["password_hash"] if row else DUMMY_HASH, password)
    if not (row and ok):
        rec = FAILS.setdefault(username, [0, time.time()])
        rec[0] += 1
        return jsonify(error="invalid credentials"), 401

    FAILS.pop(username, None)
    session.clear()
    session["user_id"] = row["id"]
    return jsonify(message="logged in")


@bp.post("/logout")
@login_required
def logout():
    session.clear()
    return jsonify(message="logged out")


@bp.get("/me")
@login_required
def me():
    return jsonify(username=g.user["username"], role=g.user["role"])