import json
import os
import random
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer

DB_FILE = "/data/quotes.db"
SEED_FILE = "/app/quotes.json"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn 

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            char TEXT NOT NULL
        )
    """)
    conn.commit()

    # Seed from quotes.json only if the table is empty
    count = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    if count == 0 and os.path.exists(SEED_FILE):
        with open(SEED_FILE,"r", encoding="utf-8") as f:
            seed = json.load(f)
        conn.executemany(
            "INSERT INTO quotes (text, char) VALUES (?, ?)",
            [(q["text"], q["char"]) for q in seed]
        )
        conn.commit()
        print(f"Seeded {len(seed)} quotes from quotes.json")
    conn.close()

def fetch_all():
    conn = get_db()
    rows = conn.execute("SELECT text, char FROM quotes").fetchall()
    conn.close()
    return [dict(r) for r in rows]

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())
    def do_GET(self):
        try:
            if self.path == "/quote":
                quotes = fetch_all()
                self._send_json(200, random.choice(quotes) if quotes else {})
            elif self.path =="/quotes":
                self._send_json(200, fetch_all())
            else:
                self.send_response(404)
                self.end_headers()   
        except Exception as e:
            self._send_json(500, {"error":"database error"})
    
    def log_message(self, *args):
        pass 
    
if __name__ == "__main__":
    init_db()
    print("API running on port 5000")
    HTTPServer(("0.0.0.0", 5000), Handler).serve_forever()