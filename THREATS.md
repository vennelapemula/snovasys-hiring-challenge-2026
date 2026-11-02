# Threats
Last updated:2 Nov 2026

Format: threat, what I did, status (Closed / Partly / Accepted), test.

## 1. IDOR: changing the document ID in a URL
- Risk: owner2 opens /documents/5 which belongs to owner1.
- Done: every route calls can(user, doc_id, action) in permissions.py; the server decides, not the UI.
- Status: Closed once routes exist (can() written, routes pending).
- Test: owner2 requests owner1's document, expects 404.

## 2. Existence leak via error codes
- Risk: 403 vs 404 tells an attacker which IDs exist.
- Done: no access, missing and deleted all return the same 404.
- Status: Closed (design), to be tested.

## 3. Role taken from the cookie
- Risk: user edits cookie to become admin.
- Done: session stores only user_id; role is re-read from the DB on every request (auth.py load_user). Cookie is signed with SECRET_KEY.
- Status: Closed.

## 4. Access after revoke
- Risk: revoked user keeps reading.
- Done: no tokens or cached grants; can() checks grants.revoked_at IS NULL in the DB on every request.
- Status: Closed (design), to be tested.

## 5. Audit log tampering
- Risk: someone edits or deletes audit rows.
- Done: SQLite triggers block UPDATE and DELETE on audit_log; hash chain (prev_hash/hash) planned to detect any other change.
- Status: Partly. Anyone with direct DB file access could drop the triggers. Hash chain and verify endpoint pending.

## 6. Brute-force login
- Risk: guessing passwords.
- Done: 5 failed attempts per username locks for 5 minutes (429); same error for wrong user or wrong password; dummy hash so timing is similar.
- Status: Partly. Counter is in memory, resets on restart and is per gunicorn worker. Attacker can also lock out a real user (accepted).

## 7. Hardcoded default seed password
- Risk: LocalDemo-123 is visible in GitHub.
- Done: production uses SEED_PASSWORD from Render env var.
- Status: Accepted for local dev only. Demo passwords are in README by requirement.

## 8. Admin can read all documents
- Decision: admin manages users and sees activity but has NO automatic read access. can() gives admin nothing without a grant.
- Status: Design choice.

## 9. Free-tier storage is not persistent
- Risk: Render restarts delete trustvault.db and uploaded files; seed data is recreated at startup.
- Status: Accepted, stated honestly in README.

## 10. Upload attacks (pending routes)
- Planned: random stored_name, file type and size checks, filename sanitised, files outside web root, served only through can().
- Status: Not built yet.

## 11. Session cookie theft / CSRF
- Done: HttpOnly, SameSite=Lax, Secure on Render.
- Status: Partly. No CSRF tokens yet.