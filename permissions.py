from db import get_db

LEVELS = {
    "read": {"read"},
    "edit": {"read", "edit"},
}
OWNER_ONLY = {"delete", "share"}
ALL_ACTIONS = {"read", "edit", "delete", "share"}


def can(user, doc_id, action):
    """The ONLY place that decides document access."""
    if user is None or action not in ALL_ACTIONS:
        return False

    conn = get_db()
    try:
        doc = conn.execute(
            "SELECT id, owner_id, deleted_at FROM documents WHERE id = ?",
            (doc_id,),
        ).fetchone()

        if doc is None or doc["deleted_at"] is not None:
            return False

        if doc["owner_id"] == user["id"]:
            return True

        if action in OWNER_ONLY:
            return False

        grant = conn.execute(
            "SELECT level FROM grants "
            "WHERE doc_id = ? AND user_id = ? AND revoked_at IS NULL "
            "ORDER BY id DESC LIMIT 1",
            (doc_id, user["id"]),
        ).fetchone()
        if grant is None:
            return False

        return action in LEVELS.get(grant["level"], set())
    finally:
        conn.close()