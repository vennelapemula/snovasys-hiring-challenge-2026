import os

from flask import Flask

import auth
import documents
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

init_db()
auth.seed_users()


@app.route("/")
def home():
    return "TrustVault is running"