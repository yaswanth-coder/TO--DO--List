
import os
import requests
from datetime import datetime
import requests

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

import db_config
from models import db, Task, seed_demo_tasks

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)   # auto-detects /static and /templates folders

app.config["SECRET_KEY"]                     = db_config.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"]        = db_config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = db_config.SQLALCHEMY_TRACK_MODIFICATIONS

CORS(app)
db.init_app(app)


# ── DB init ───────────────────────────────────────────────────────────────────
# with app.app_context():
#     db.create_all()
#     seed_demo_tasks()


# ── Pages ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ── GET /api/tasks ─────────────────────────────────────────────────────────
@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    f     = request.args.get("filter", "all").lower()
    query = Task.query.order_by(Task.created_at.desc())
    if f == "active":
        query = query.filter_by(done=False)
    elif f == "done":
        query = query.filter_by(done=True)
    return jsonify([t.to_dict() for t in query.all()]), 200


# ── POST /api/tasks ────────────────────────────────────────────────────────
@app.route("/api/tasks", methods=["POST"])
def create_task():
    data     = request.get_json(silent=True) or {}
    text     = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    priority = data.get("priority", "medium")
    if priority not in ("high", "medium", "low"):
        return jsonify({"error": "priority must be high, medium, or low"}), 400
    task = Task(text=text, priority=priority)
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


# ── PATCH /api/tasks/<id> ──────────────────────────────────────────────────
@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json(silent=True) or {}
    if "text" in data:
        text = data["text"].strip()
        if not text:
            return jsonify({"error": "text cannot be empty"}), 400
        task.text = text
    if "priority" in data:
        if data["priority"] not in ("high", "medium", "low"):
            return jsonify({"error": "invalid priority"}), 400
        task.priority = data["priority"]
    if "done" in data:
        task.done = bool(data["done"])
    task.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(task.to_dict()), 200


# ── DELETE /api/tasks/<id> ─────────────────────────────────────────────────
@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"deleted": task_id}), 200


# ── GET /api/stats ─────────────────────────────────────────────────────────
@app.route("/api/stats", methods=["GET"])
def get_stats():
    total = Task.query.count()
    done  = Task.query.filter_by(done=True).count()
    high  = Task.query.filter_by(priority="high", done=False).count()
    pct   = round((done / total) * 100) if total else 0
    return jsonify({"total": total, "done": done, "high": high, "completion": pct}), 200


# ── POST /api/ai  — 🔐 API key never leaves this file ─────────────────────
@app.route("/api/ai", methods=["POST"])
def ai_proxy():
    api_key = db_config.ANTHROPIC_API_KEY
    if not api_key or "your-real-key" in api_key:
        return jsonify({"error": "Add your ANTHROPIC_API_KEY in db_config.py"}), 500

    data    = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    # Pull live task context from MySQL — browser never sends the key
    rows = Task.query.order_by(Task.created_at.desc()).all()
    task_summary = (
        "\n".join(
            f"[{t.priority.upper()}][{'DONE' if t.done else 'PENDING'}] {t.text}"
            for t in rows
        ) or "No tasks yet."
    )

    system_prompt = (
        "You are an elite productivity AI coach inside FlowTask, a premium SaaS dashboard. "
        "Be warm, direct, and motivating. Never be generic.\n\n"
        f"User's current tasks:\n{task_summary}\n\n"
        "Rules: max 130 words, always actionable, end with one power tip."
    )

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            json={
                "model":      db_config.ANTHROPIC_MODEL,
                "max_tokens": 350,
                "system":     system_prompt,
                "messages":   [{"role": "user", "content": message}],
            },
            headers={
                "Content-Type":      "application/json",
                "x-api-key":         api_key,       # ← key stays on server
                "anthropic-version": "2023-06-01",
            },
            timeout=30,
        )
        if not resp.ok:
            err = resp.json()
            return jsonify({"error": err.get("error", {}).get("message", "Anthropic error")}), resp.status_code

        reply = resp.json()["content"][0]["text"]
        return jsonify({"reply": reply}), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out — try again"}), 504
    except Exception as exc:
        app.logger.error("[AI] %s", exc)
        return jsonify({"error": "Server error"}), 500


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    key_ok = bool(db_config.ANTHROPIC_API_KEY) and "your-real-key" not in db_config.ANTHROPIC_API_KEY
    print(f"\n✦ FlowTask  →  http://localhost:{port}")
    print(f"  DB   : {db_config.SQLALCHEMY_DATABASE_URI}")
    print(f"  Key  : {'✅ Set' if key_ok else '⚠️  Missing — edit db_config.py'}\n")
    app.run(host="0.0.0.0", port=port, debug=True)