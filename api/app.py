import json
import os
import random
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer

DB_FILE = "/data/quotes.db"
SEED_FILE = "/app/quotes.json"
CHARACTER_FILE="/app/characters.json"

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
            char TEXT NOT NULL,
            character_id INTEGER 
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
        
    conn.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            anime TEXT NOT NULL
        )
    """)
    conn.commit()
    
    count = conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
    if count == 0 and os.path.exists(CHARACTER_FILE):
        with open(CHARACTER_FILE,"r", encoding="utf-8") as f:
            seed = json.load(f)
        conn.executemany(
            "INSERT INTO characters (name, anime) VALUES (?, ?)",
            [(c["name"], c["anime"]) for c in seed]
        )
        conn.commit()
        print(f"Seeded {len(seed)} characters from characters.json")
    conn.close()

def fetch_all():
    conn = get_db()
    rows = conn.execute("SELECT id, text, char, character_id FROM quotes").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_characters():
    conn = get_db()
    rows = conn.execute("SELECT id, name, anime FROM characters").fetchall()
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
            elif self.path == "/characters":
                self._send_json(200, fetch_characters()) 
            else:
                self.send_response(404)
                self.end_headers()   
        except Exception as e:
            self._send_json(500, {"error":"database error"}) 
               
    def do_POST(self):
        if self.path == "/quotes":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                text = body.get("text", "").strip()
                char = body.get("char", "").strip()
                character_id = body.get("character_id")
                if not text or not char:
                    self._send_json(400, {"error": "text and char are required"})
                    return
                conn = get_db()
                conn.execute("INSERT INTO quotes (text, char, character_id) VALUES(?,?, ?)" ,(text, char, character_id))
                conn.commit()
                conn.close()
                self._send_json(201, {"text": text, "char": char})
            except Exception as e:
                print("POST /quotes error:", repr(e))
                self._send_json(500, {"error": "could not save quote"})
        elif self.path == "/characters":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                name = body.get("name", "").strip()
                anime = body.get("anime", "").strip()
                if not name or not anime:
                    self._send_json(400, {"error": "name and anime are required"})
                    return
                conn = get_db()
                conn.execute("INSERT INTO characters (name, anime) VALUES(?,?)" ,(name, anime))
                conn.commit()
                conn.close()
                self._send_json(201, {"name": name, "anime": anime})
            except Exception:
                self._send_json(500, {"error":"could not save character"})
        else:
            self.send_response(404)
            self.end_headers()
            
    def do_DELETE(self):
        if self.path.startswith("/quotes/"):
            try:
                quote_id = int(self.path.split("/")[-1])
                conn = get_db()
                conn.execute("DELETE FROM quotes WHERE id=?",(quote_id,))
                conn.commit()
                conn.close()
                self._send_json(200, {"deleted": quote_id})
            except Exception:
                self._send_json(500, {"error":"could not delete quote"})
        elif self.path.startswith("/characters/"):
            try:
                char_id = int(self.path.split("/")[-1])
                conn = get_db()
                conn.execute("DELETE FROM characters WHERE id=?",(char_id,))
                conn.commit()
                conn.close()
                self._send_json(200, {"deleted": char_id})
            except Exception:
                self._send_json(500, {"error":"could not delete characters"})
        else:
            self.send_response(404)
            self.end_headers()
            
    def log_message(self, *args):
        pass 
    
if __name__ == "__main__":
    init_db()
    print("API running on port 5000")
    HTTPServer(("0.0.0.0", 5000), Handler).serve_forever()