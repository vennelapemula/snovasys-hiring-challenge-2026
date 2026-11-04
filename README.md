# TrustVault

Secure document sharing where the server decides who can read a file, and every attempt (allowed or refused) is recorded in a tamper-evident audit log.

Live: https://trustvault-vennela.onrender.com
(Free instance: the first request can take about 50 seconds.)

## Demo accounts (live site)
| Role | Username | Password |
|---|---|---|
| Admin | admin1 | <READ@123> |
| Owner | owner1 | <READ@123> |
| Viewer | viewer1 | <READ@123> |

owner2 also exists so tests can prove one owner cannot read another owner's file.

## What each role can do
- **Admin**: sees activity (all, refused only, permission changes, flagged users) and verifies the audit chain. Has NO automatic access to document contents.
- **Owner**: uploads, shares (read or edit), revokes, deletes own documents.
- **Viewer**: reads only documents an owner has granted.

## Permission model
Per-document grants. One function, `can(user, doc_id, action)` in `permissions.py`, decides every document action.
- Owner: all actions on own document.
- Others: only with a live grant (`revoked_at IS NULL`). A read grant allows read; an edit grant allows read and edit.
- Delete and share: owner only.
- Missing, deleted and not-allowed all return the same 404, so existence does not leak.
- Revoking works on the next request, because the database is checked every time. No tokens or cached permissions.

## Audit trail
Every upload, download, delete, grant, revoke and refused attempt is appended to `audit_log`.
- SQLite triggers block UPDATE and DELETE.
- Each row stores a SHA-256 hash of the previous hash plus its own fields (including time). `GET /admin/audit/verify` recomputes the chain.

## Run locally
```
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY="any-long-random-string"
flask --app app run
```
Open http://127.0.0.1:5000. Local demo password: LocalDemo-123.

## Tests
```
python -m pytest -v
```


## Deploy (Render)
Build: `pip install -r requirements.txt`. Start: `gunicorn app:app`.
Environment variables: `SECRET_KEY` (long random), `SEED_PASSWORD` (demo password).

## Database
SQLite. `init_db()` in `db.py` creates users, documents, grants and audit_log at startup. Seed users and two sample documents are created when the database is empty.

## API (who may call it)
| Method and path | Who |
|---|---|
| POST /login | anyone |
| POST /logout, GET /me | logged in |
| POST /documents | owner, admin |
| GET /documents (?q, category, owner, since) | logged in; only own or granted documents |
| GET /documents/{id}/download | owner, or live read/edit grant |
| DELETE /documents/{id} | owner only |
| GET /documents/{id}/grants | owner only |
| POST /documents/{id}/grants | owner only |
| DELETE /documents/{id}/grants/{username} | owner only |
| GET /admin/audit, /admin/audit/verify, /admin/flagged | admin only |

## Honest limits
- Render free tier wipes the database and uploads on restart; seed data is recreated.
- No file editing, versions, external sharing links, retention rules or AI sharing suggestions.
- Audit chain cannot detect deleted tail rows if someone controls the database file.
- No CSRF tokens (SameSite=Lax only). Login lockout is in memory.
- Extension allow-list only, no content scanning.

See THREATS.md and PROMPTS.md.