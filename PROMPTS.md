PROMPTS log
## Entry 1: 2 Nov 2026
- **Asked:** SQLite schema for users, documents, grants, audit_log
- **Produced:** db.py with init_db and append-only triggers on audit_log
- **What was wrong:** I did not paste the code into db.py, so an empty file got pushed and app.py gave ImportError
- **What I did:** pasted the code, ran python app.py, trustvault.db was created. Fix commit: [61952fd](https://github.com/vennelapemula/snovasys-hiring-challenge-2026/commit/61952fd)

## Entry 2: 2 Nov 2026
- **Asked:** auth.py with login, logout, roles and seed users
- **Produced:** auth.py and app.py using a Flask blueprint
- **What was wrong:** The AI told me to test with `python app.py`, but app.py has no app.run(), so no server started and the login test failed with "Unable to connect"
- **What I did:** ran `flask --app app run` in one terminal and the login test in a second terminal. Commit: [6275b17](https://github.com/vennelapemula/snovasys-hiring-challenge-2026/commit/6275b17)

## Entry 3: 3 Nov 2026
- **Asked:** pytest tests proving one user cannot reach another user's documents
- **Produced:** tests/test_access.py (12 tests)
- **What was wrong:** Passing tests do not prove they test anything. I commented out the can() check in download and re-ran: 6 tests failed (other owner, viewer without grant, admin, revoke, deleted doc, audit of denied attempts), so the tests really guard the check.
- **What I did:** restored the check, 12 pass again. Commit: [1bb6679](https://github.com/vennelapemula/snovasys-hiring-challenge-2026/commit/1bb6679)

## Entry 4: 4 Nov 2026
- **Asked:** hash-chained audit log, admin view, seed documents and a web UI
- **Produced:** audit.py (time in hash, verify), admin.py, seed.py, static UI
- **What was wrong:** the AI changed the audit hash format but did not warn that my old local trustvault.db would break; /login returned 500 and the Access button showed "not allowed". It also showed an upload box to viewers who cannot upload.
- **What I did:** stopped the server, deleted the old trustvault.db, restarted clean; login and Access worked. Commit: [abc1234](https://github.com/vennelapemula/snovasys-hiring-challenge-2026/commit/abc1234)