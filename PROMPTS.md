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