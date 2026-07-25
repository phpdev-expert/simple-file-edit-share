"""Idempotently seed demo users (and a sample shared document) on startup."""
from sqlalchemy.orm import Session

from .core.security import hash_password
from .models import Document, Notification, Share, User

DEMO_PASSWORD = "password123"
DEMO_USERS = [
    {"email": "alice@demo.com", "name": "Alice"},
    {"email": "bob@demo.com", "name": "Bob"},
    {"email": "carol@demo.com", "name": "Carol"},
]


def seed(db: Session) -> None:
    created = {}
    for spec in DEMO_USERS:
        user = db.query(User).filter(User.email == spec["email"]).first()
        if user is None:
            user = User(
                email=spec["email"],
                name=spec["name"],
                password_hash=hash_password(DEMO_PASSWORD),
            )
            db.add(user)
            db.flush()
        created[spec["email"]] = user
    db.commit()

    # Give reviewers something to see: Alice owns a doc shared with Bob.
    alice, bob = created["alice@demo.com"], created["bob@demo.com"]
    if not db.query(Document).filter(Document.owner_id == alice.id).first():
        doc = Document(
            title="Welcome to Ajaia Docs",
            content=(
                "<h1>Welcome to Ajaia Docs</h1>"
                "<p>This is a <strong>collaborative</strong> document. "
                "Try <em>italic</em>, <u>underline</u>, and lists:</p>"
                "<ul><li>Create and edit documents</li>"
                "<li>Import a .txt or .md file</li>"
                "<li>Share with a teammate by email</li></ul>"
            ),
            owner_id=alice.id,
        )
        db.add(doc)
        db.flush()
        db.add(Share(document_id=doc.id, user_id=bob.id, role="editor"))
        db.add(
            Notification(
                user_id=bob.id,
                message=f'{alice.name} shared "{doc.title}" with you (edit access)',
                document_id=doc.id,
            )
        )
        db.commit()
