PROMPTS log
## Entry 1: 2 Nov 2026
- **Asked:** SQLite schema for users, documents, grants, audit_log
- **Produced:** db.py with init_db and append-only triggers on audit_log
- **What was wrong:** I did not paste the code into db.py, so an empty file got pushed and app.py gave ImportError
- **What I did:** pasted the code, ran python app.py, trustvault.db was created. Fix commit: [61952fd](https://github.com/vennelapemula/snovasys-hiring-challenge-2026/commit/61952fd)