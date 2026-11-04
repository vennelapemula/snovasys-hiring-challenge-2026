import os

from flask import Flask, request

import admin
import auth
import documents
import seed
from db import init_db

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
)
app.register_blueprint(auth.bp)
app.register_blueprint(documents.bp)
app.register_blueprint(admin.bp)

init_db()
auth.seed_users()
seed.seed_documents()


@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'"
    )
    if not request.path.startswith("/static"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/")
def home():
    return app.send_static_file("index.html")