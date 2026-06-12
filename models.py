# ── models.py ─────────────────────────────────────────────────────────────────
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Task(db.Model):
    __tablename__ = "tasks"

    id         = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    text       = db.Column(db.String(500), nullable=False)
    priority   = db.Column(db.String(10),  nullable=False, default="medium")  # high | medium | low
    done       = db.Column(db.Boolean,     nullable=False, default=False)
    created_at = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id":         self.id,
            "text":       self.text,
            "priority":   self.priority,
            "done":       self.done,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Task {self.id} [{self.priority}] {'✓' if self.done else '○'} {self.text[:30]!r}>"


def seed_demo_tasks():
    """Insert demo tasks only when the table is empty."""
    if Task.query.count() > 0:
        return
    demos = [
        Task(text="Review Q2 product roadmap",       priority="high",   done=False),
        Task(text="Send weekly team update",          priority="medium", done=True),
        Task(text="Update dashboard analytics",       priority="medium", done=False),
        Task(text="Schedule 1:1 with designer",       priority="low",    done=False),
        Task(text="Write blog post draft",            priority="low",    done=True),
        Task(text="Fix critical login bug",           priority="high",   done=False),
        Task(text="Prepare investor slide deck",      priority="high",   done=False),
    ]
    db.session.add_all(demos)
    db.session.commit()
    print("[DB] ✅ Demo tasks seeded.")