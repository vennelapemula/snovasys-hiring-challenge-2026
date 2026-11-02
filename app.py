from flask import Flask
from db import init_db

app = Flask(__name__)
init_db()


@app.route("/")
def home():
    return "TrustVault is running"