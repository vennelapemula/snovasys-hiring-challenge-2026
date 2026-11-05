# TrustVault: write-up

## What I built
A document-sharing platform in Flask and SQLite, deployed on Render. Three roles (admin, owner, viewer). Owners upload documents and grant read or edit access to named people, and take it back. Every decision is made on the server by one function, can(), in permissions.py. Every upload, download, delete, grant, revoke and refused attempt goes into a hash-chained audit log. Admin can view activity, refused attempts, permission changes, flagged users, and verify the chain. There is a simple web UI, search by name, owner, category and date, upload validation, and 15 automated tests.

## Permission model (in my own words)
Each document has an owner. Anyone else needs a live grant: a row in the grants table with revoked_at empty. A read grant allows reading; an edit grant allows read and edit. Only the owner can share, revoke or delete. Admin manages and watches, but has no automatic access to file contents. I chose per-document grants (no folders or groups) because they are easy to reason about and test.
Missing, deleted and not-allowed documents all return the same 404, so an attacker cannot learn which IDs exist.
Revoking is immediate because nothing is cached: the database is checked on every request, and the role is read from the database, not the cookie.

## How the audit trail is protected
SQLite triggers block UPDATE and DELETE on audit_log. Each row also stores a SHA-256 hash of the previous hash plus its own fields (including time), and /admin/audit/verify recomputes the chain, so an edited row is detected.

## Tests
15 tests prove that one user cannot reach another's documents, that revoking works at once, that refused attempts are logged, that viewers cannot upload, and that the audit chain detects tampering. To check the tests are real, I removed the can() check from download and 6 tests failed.

## How I used AI, and where it was wrong
I used AI to draft code and then read, ran and tested it. Examples are in PROMPTS.md:
- The first audit hash left out the time, so changing a timestamp would not break the chain. I found it while reading and fixed it.
- The AI changed the audit hash format without warning that my old local database would break, which caused a 500 on login until I deleted it.
- The AI described an edit right but built no edit route, so I listed it as not built.
- The first UI showed an upload box to viewers.

## What I deliberately did not build
Folders and groups, external sharing links, versions and file replacement, retention rules, AI sharing suggestions, CSRF tokens, content scanning of uploads.

## Unfinished and known weaknesses
- Render free tier wipes the database and uploads on restart; seed data is recreated.
- The audit chain cannot detect removed last rows if someone controls the database file.
- Login lockout is in memory and resets on restart.
- "Edit" is a grant level but there is no edit route yet.
- No automated XSS or CSRF test.