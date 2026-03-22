import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
import sqlite3, uuid, json
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DB = "db.sqlite3"

# ===== DB =====
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT,
        type TEXT,
        content TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ===== REGISTER =====
@app.route("/register", methods=["POST"])
def register():
    return {"client_id": str(uuid.uuid4())}

# ===== LOG =====
@app.route("/log", methods=["POST"])
def log():
    cid = request.headers.get("X-API-KEY")
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "INSERT INTO logs (client_id, type, content, timestamp) VALUES (?, ?, ?, ?)",
        (cid, data.get("type"), json.dumps(data), data.get("timestamp"))
    )

    conn.commit()
    conn.close()

    socketio.emit("new_log", {
        "client_id": cid,
        "data": data
    })

    return {"ok": True}

# ===== HISTORY =====
@app.route("/logs/<cid>")
def logs(cid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        SELECT type, content, timestamp
        FROM logs
        WHERE client_id=?
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = c.fetchall()
    conn.close()

    return jsonify([
        {
            "type": r[0],
            "content": json.loads(r[1]),
            "timestamp": r[2]
        }
        for r in rows
    ])

# ===== WEB =====
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)