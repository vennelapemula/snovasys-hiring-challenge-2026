import io
import os
import tempfile

import pytest

os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["SEED_PASSWORD"] = "TestPass-123"

import db

# use a throwaway database for tests, never the real one
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
db.DB_PATH = _tmp.name

import app as app_module  # noqa: E402

PW = "TestPass-123"


@pytest.fixture()
def clients():
    app = app_module.app
    app.config["TESTING"] = True
    out = {}
    for name in ("owner1", "owner2", "viewer1", "admin1"):
        c = app.test_client()
        r = c.post("/login", json={"username": name, "password": PW})
        assert r.status_code == 200
        out[name] = c
    return out


def upload(client, name="secret.txt", data=b"top secret"):
    r = client.post(
        "/documents",
        data={"file": (io.BytesIO(data), name), "category": "salary"},
        content_type="multipart/form-data",
    )
    assert r.status_code == 201
    return r.get_json()["id"]


def audit_results(doc_id):
    conn = db.get_db()
    rows = conn.execute(
        "SELECT action, result FROM audit_log WHERE doc_id = ?", (doc_id,)
    ).fetchall()
    conn.close()
    return [(r["action"], r["result"]) for r in rows]


def test_other_owner_cannot_download(clients):
    doc = upload(clients["owner1"])
    assert clients["owner1"].get(f"/documents/{doc}/download").status_code == 200
    assert clients["owner2"].get(f"/documents/{doc}/download").status_code == 404


def test_viewer_without_grant_cannot_download(clients):
    doc = upload(clients["owner1"])
    assert clients["viewer1"].get(f"/documents/{doc}/download").status_code == 404


def test_admin_has_no_automatic_access(clients):
    doc = upload(clients["owner1"])
    assert clients["admin1"].get(f"/documents/{doc}/download").status_code == 404


def test_not_logged_in_is_rejected():
    c = app_module.app.test_client()
    assert c.get("/documents/1/download").status_code == 401
    assert c.get("/documents").status_code == 401


def test_listing_hides_other_users_documents(clients):
    doc = upload(clients["owner1"], name="only-owner1.txt")
    ids = [d["id"] for d in clients["owner2"].get("/documents").get_json()]
    assert doc not in ids
    ids = [d["id"] for d in clients["owner1"].get("/documents").get_json()]
    assert doc in ids


def test_grant_then_revoke_is_immediate(clients):
    doc = upload(clients["owner1"])
    r = clients["owner1"].post(
        f"/documents/{doc}/grants", json={"username": "viewer1", "level": "read"}
    )
    assert r.status_code == 201
    assert clients["viewer1"].get(f"/documents/{doc}/download").status_code == 200

    r = clients["owner1"].delete(f"/documents/{doc}/grants/viewer1")
    assert r.status_code == 200
    # same session, no re-login: access must already be gone
    assert clients["viewer1"].get(f"/documents/{doc}/download").status_code == 404


def test_non_owner_cannot_grant_or_delete(clients):
    doc = upload(clients["owner1"])
    r = clients["owner2"].post(
        f"/documents/{doc}/grants", json={"username": "owner2", "level": "edit"}
    )
    assert r.status_code == 404
    assert clients["owner2"].delete(f"/documents/{doc}").status_code == 404
    # a read grant does not allow delete or re-sharing either
    clients["owner1"].post(
        f"/documents/{doc}/grants", json={"username": "viewer1", "level": "edit"}
    )
    assert clients["viewer1"].delete(f"/documents/{doc}").status_code == 404
    assert clients["viewer1"].post(
        f"/documents/{doc}/grants", json={"username": "viewer1", "level": "edit"}
    ).status_code == 404


def test_viewer_cannot_upload(clients):
    r = clients["viewer1"].post(
        "/documents",
        data={"file": (io.BytesIO(b"x"), "a.txt")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 403


def test_bad_file_type_rejected(clients):
    r = clients["owner1"].post(
        "/documents",
        data={"file": (io.BytesIO(b"MZ"), "virus.exe")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 400


def test_deleted_document_is_gone_for_everyone(clients):
    doc = upload(clients["owner1"])
    assert clients["owner1"].delete(f"/documents/{doc}").status_code == 200
    assert clients["owner1"].get(f"/documents/{doc}/download").status_code == 404


def test_refused_attempts_are_audited(clients):
    doc = upload(clients["owner1"])
    clients["owner2"].get(f"/documents/{doc}/download")
    assert ("download", "denied") in audit_results(doc)
    clients["owner1"].get(f"/documents/{doc}/download")
    assert ("download", "ok") in audit_results(doc)


def test_audit_log_cannot_be_edited_or_deleted():
    conn = db.get_db()
    with pytest.raises(Exception):
        conn.execute("UPDATE audit_log SET result = 'x'")
    with pytest.raises(Exception):
        conn.execute("DELETE FROM audit_log")
    conn.close()