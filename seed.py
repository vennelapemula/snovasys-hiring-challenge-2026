import os
import uuid

import audit
from db import get_db
from documents import UPLOAD_DIR

SAMPLES = [
    ("owner1", "salary-letter.txt", "salary", "Demo salary letter (fake data)."),
    ("owner2", "contract-acme.txt", "contract", "Demo contract with ACME (fake data)."),
]


def seed_documents():
    events = []
    conn = get_db()
    try:
        if conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] > 0:
            return
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        docs = {}
        for owner, name, cat, text in SAMPLES:
            u = conn.execute("SELECT id FROM users WHERE username = ?", (owner,)).fetchone()
            if u is None:
                continue
            stored = uuid.uuid4().hex + ".txt"
            with open(os.path.join(UPLOAD_DIR, stored), "w") as f:
                f.write(text)
            cur = conn.execute(
                "INSERT INTO documents (owner_id, name, category, stored_name) VALUES (?,?,?,?)",
                (u["id"], name, cat, stored),
            )
            docs[owner] = (u["id"], cur.lastrowid)
            events.append((u["id"], "upload", cur.lastrowid, "ok"))

        viewer = conn.execute("SELECT id FROM users WHERE username = 'viewer1'").fetchone()
        if viewer and "owner1" in docs:
            owner_id, doc_id = docs["owner1"]
            conn.execute(
                "INSERT INTO grants (doc_id, user_id, level) VALUES (?,?, 'read')",
                (doc_id, viewer["id"]),
            )
            events.append((owner_id, "grant_read_to_viewer1", doc_id, "ok"))
        conn.commit()
    finally:
        conn.close()
    for e in events:
        audit.log(*e)