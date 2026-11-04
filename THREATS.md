# THREATS.md

Last updated: 4 Nov 2026

Format: threat, what I did, status (Closed / Partly / Accepted), test.

## 1. IDOR: changing the document ID in a URL
- Added: 2 Nov 2026. Updated: 4 Nov 2026
- Risk: owner2 opens /documents/1 which belongs to owner1.
- Done: every document route calls can() in permissions.py; the server decides.
- Status: Closed.
- Test: test_other_owner_cannot_download. I removed the can() check in download and 6 tests failed, so the tests guard it.

## 2. Existence leak via error codes
- Added: 2 Nov 2026
- Risk: 403 vs 404 shows which IDs exist.
- Done: no access, missing and deleted all return the same 404.
- Status: Closed.
- Test: test_deleted_document_is_gone_for_everyone, test_viewer_without_grant_cannot_download.

## 3. Role taken from the cookie
- Added: 2 Nov 2026
- Risk: user edits cookie to become admin.
- Done: session stores only user_id; role is re-read from the DB on every request. Cookie is signed.
- Status: Closed.

## 4. Access after revoke
- Added: 2 Nov 2026. Updated: 4 Nov 2026
- Risk: revoked user keeps reading.
- Done: no tokens or cached grants; can() checks revoked_at IS NULL in the DB on every request. Verified in the browser too.
- Status: Closed.
- Test: test_grant_then_revoke_is_immediate.

## 5. Audit log tampering
- Added: 2 Nov 2026. Updated: 4 Nov 2026
- Risk: someone edits or deletes audit rows.
- Done: SQLite triggers block UPDATE and DELETE; each row is hash-chained (time included) and /admin/audit/verify recomputes the chain.
- Status: Partly. Someone with the DB file can drop the triggers and delete the LAST rows; the chain cannot detect removed tail rows. Accepted for this scope.
- Test: test_audit_log_cannot_be_edited_or_deleted.

## 6. Refused attempts must be recorded
- Added: 4 Nov 2026
- Done: every denied download, grant, revoke, delete and admin access writes an audit row.
- Status: Closed.
- Test: test_refused_attempts_are_audited.

## 7. Brute-force login
- Added: 2 Nov 2026
- Done: 5 failures per username lock for 5 minutes; same error for wrong user or password.
- Status: Partly. Counter is in memory, resets on restart, per worker. Attacker can lock out a real user (accepted).

## 8. Default seed password in code
- Added: 2 Nov 2026
- Done: production uses SEED_PASSWORD from a Render environment variable.
- Status: Accepted for local dev. Demo passwords are in the README by requirement.

## 9. Admin reading documents
- Added: 2 Nov 2026
- Decision: admin manages and sees activity but has NO automatic read access.
- Status: Design choice.
- Test: test_admin_has_no_automatic_access.

## 10. Free-tier storage is not persistent
- Added: 2 Nov 2026
- Risk: Render restarts wipe the database and uploaded files.
- Done: seed users and documents are recreated at startup.
- Status: Accepted, stated in README.

## 11. Upload attacks
- Added: 2 Nov 2026
- Done: random stored name, extension allow-list, 10 MB limit, secure_filename, files stored outside static folder, served only through can().
- Status: Partly. Extension check only, no content scanning.
- Test: test_bad_file_type_rejected.

## 12. Roles that must not act
- Added: 4 Nov 2026
- Done: viewers cannot upload (403); non-owners cannot share or delete; only admins reach /admin/*.
- Status: Closed.
- Test: test_viewer_cannot_upload, test_non_owner_cannot_grant_or_delete, test_admin_pages_are_admin_only.

## 13. XSS in the UI
- Added: 4 Nov 2026
- Done: UI writes with textContent only; CSP, nosniff, X-Frame-Options and no-store headers set.
- Status: Partly. No automated XSS test.

## 14. CSRF
- Added: 2 Nov 2026
- Done: SameSite=Lax, HttpOnly, Secure on Render.
- Status: Partly. No CSRF tokens.

## 15. Audit write race
- Added: 4 Nov 2026
- Done: BEGIN IMMEDIATE so only one audit writer at a time.
- Status: Partly. Not load-tested.

## 16. Not built
- Content replacement/versions, external sharing links, retention, AI sharing suggestions.# THREATS.md

Last updated: 4 Nov 2026

Format: threat, what I did, status (Closed / Partly / Accepted), test.

## 1. IDOR: changing the document ID in a URL
- Added: 2 Nov 2026. Updated: 4 Nov 2026
- Risk: owner2 opens /documents/1 which belongs to owner1.
- Done: every document route calls can() in permissions.py; the server decides.
- Status: Closed.
- Test: test_other_owner_cannot_download. I removed the can() check in download and 6 tests failed, so the tests guard it.

## 2. Existence leak via error codes
- Added: 2 Nov 2026
- Risk: 403 vs 404 shows which IDs exist.
- Done: no access, missing and deleted all return the same 404.
- Status: Closed.
- Test: test_deleted_document_is_gone_for_everyone, test_viewer_without_grant_cannot_download.

## 3. Role taken from the cookie
- Added: 2 Nov 2026
- Risk: user edits cookie to become admin.
- Done: session stores only user_id; role is re-read from the DB on every request. Cookie is signed.
- Status: Closed.

## 4. Access after revoke
- Added: 2 Nov 2026. Updated: 4 Nov 2026
- Risk: revoked user keeps reading.
- Done: no tokens or cached grants; can() checks revoked_at IS NULL in the DB on every request. Verified in the browser too.
- Status: Closed.
- Test: test_grant_then_revoke_is_immediate.

## 5. Audit log tampering
- Added: 2 Nov 2026. Updated: 4 Nov 2026
- Risk: someone edits or deletes audit rows.
- Done: SQLite triggers block UPDATE and DELETE; each row is hash-chained (time included) and /admin/audit/verify recomputes the chain.
- Status: Partly. Someone with the DB file can drop the triggers and delete the LAST rows; the chain cannot detect removed tail rows. Accepted for this scope.
- Test: test_audit_log_cannot_be_edited_or_deleted.

## 6. Refused attempts must be recorded
- Added: 4 Nov 2026
- Done: every denied download, grant, revoke, delete and admin access writes an audit row.
- Status: Closed.
- Test: test_refused_attempts_are_audited.

## 7. Brute-force login
- Added: 2 Nov 2026
- Done: 5 failures per username lock for 5 minutes; same error for wrong user or password.
- Status: Partly. Counter is in memory, resets on restart, per worker. Attacker can lock out a real user (accepted).

## 8. Default seed password in code
- Added: 2 Nov 2026
- Done: production uses SEED_PASSWORD from a Render environment variable.
- Status: Accepted for local dev. Demo passwords are in the README by requirement.

## 9. Admin reading documents
- Added: 2 Nov 2026
- Decision: admin manages and sees activity but has NO automatic read access.
- Status: Design choice.
- Test: test_admin_has_no_automatic_access.

## 10. Free-tier storage is not persistent
- Added: 2 Nov 2026
- Risk: Render restarts wipe the database and uploaded files.
- Done: seed users and documents are recreated at startup.
- Status: Accepted, stated in README.

## 11. Upload attacks
- Added: 2 Nov 2026
- Done: random stored name, extension allow-list, 10 MB limit, secure_filename, files stored outside static folder, served only through can().
- Status: Partly. Extension check only, no content scanning.
- Test: test_bad_file_type_rejected.

## 12. Roles that must not act
- Added: 4 Nov 2026
- Done: viewers cannot upload (403); non-owners cannot share or delete; only admins reach /admin/*.
- Status: Closed.
- Test: test_viewer_cannot_upload, test_non_owner_cannot_grant_or_delete, test_admin_pages_are_admin_only.

## 13. XSS in the UI
- Added: 4 Nov 2026
- Done: UI writes with textContent only; CSP, nosniff, X-Frame-Options and no-store headers set.
- Status: Partly. No automated XSS test.

## 14. CSRF
- Added: 2 Nov 2026
- Done: SameSite=Lax, HttpOnly, Secure on Render.
- Status: Partly. No CSRF tokens.

## 15. Audit write race
- Added: 4 Nov 2026
- Done: BEGIN IMMEDIATE so only one audit writer at a time.
- Status: Partly. Not load-tested.

## 16. Not built
- Content replacement/versions, external sharing links, retention, AI sharing suggestions.