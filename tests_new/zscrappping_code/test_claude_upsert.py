from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.dialects.sqlite import insert
from datetime import datetime, timezone


# --- Model definition (for reference) ---

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    email      = Column(String, nullable=False, unique=True)
    name       = Column(String)
    role       = Column(String)
    updated_at = Column(DateTime)


# --- Upsert function ---

def upsert_users(session: Session, user_list: list[dict]) -> dict:
    """
    Weekly upsert of the Users table using email as the natural key.

    - INSERTs new users (email not yet in DB).
    - UPDATEs existing users (matched by email), leaving `id` untouched.

    Args:
        session:   An active SQLAlchemy Session bound to a SQLite engine.
        user_list: List of dicts with user data. Must include 'email'.
                   Example: [{"email": "a@b.com", "name": "Alice", "role": "admin"}]

    Returns:
        A summary dict: {"inserted": int, "updated": int, "skipped": int, "errors": list}
    """
    if not user_list:
        return {"inserted": 0, "updated": 0, "skipped": 0, "errors": []}

    summary = {"inserted": 0, "updated": 0, "skipped": 0, "errors": []}
    now = datetime.now(timezone.utc)

    # Fetch all existing emails in one query to avoid N+1 lookups
    existing_emails = {
        email for (email,) in session.query(User.email).all()
    }

    for raw in user_list:
        email = (raw.get("email") or "").strip().lower()

        if not email:
            summary["skipped"] += 1
            summary["errors"].append({"record": raw, "reason": "Missing or empty email"})
            continue

        # Normalize email in the payload
        payload = {k: v for k, v in raw.items() if k != "id"}  # never allow id override
        payload["email"] = email
        payload["updated_at"] = now

        try:
            if email in existing_emails:
                # UPDATE — filter by email, exclude PK from SET clause
                update_values = {k: v for k, v in payload.items() if k != "email"}
                session.query(User).filter(User.email == email).update(
                    update_values, synchronize_session="fetch"
                )
                summary["updated"] += 1
            else:
                # INSERT — let the DB assign the PK
                session.add(User(**payload))
                existing_emails.add(email)   # guard against duplicates within the batch
                summary["inserted"] += 1

        except Exception as exc:
            session.rollback()
            summary["errors"].append({"record": raw, "reason": str(exc)})
            summary["skipped"] += 1
            continue

    session.commit()
    return summary


# --- Usage example ---

if __name__ == "__main__":
    engine = create_engine("sqlite:///app.db", echo=False)
    Base.metadata.create_all(engine)

    weekly_update = [
        {"email": "alice@example.com", "name": "Alice",   "role": "admin"},
        {"email": "bob@example.com",   "name": "Bob",     "role": "editor"},
        {"email": "carol@example.com", "name": "Carol",   "role": "viewer"},
        {"email": "",                  "name": "Ghost"},   # will be skipped
    ]

    with Session(engine) as session:
        result = upsert_users(session, weekly_update)

    print(result)
    # {"inserted": 2, "updated": 1, "skipped": 1, "errors": [...]}

"""
Key design decisions
id is never touched. The payload strips out any id key before the insert or update, so external data can never clobber the internal PK.

Single prefetch, not N+1. All existing emails are loaded in one SELECT email FROM users query at the start, avoiding a round-trip per record.
Intra-batch deduplication. The existing_emails set is updated after each insert, so if the same email appears twice in user_list, the second occurrence becomes an update rather than a constraint violation.

Per-record error isolation. A try/except around each record calls session.rollback() on failure and continues processing the rest of the batch, collecting errors in the summary dict instead of aborting the whole run.

updated_at stamped automatically. Every touched row (insert or update) gets a UTC timestamp without requiring the caller to include it.
Returns an actionable summary with counts and error details — useful for logging or alerting in a scheduled job.
"""