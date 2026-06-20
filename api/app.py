import json
import random
from http.server import BaseHTTPRequestHandler, HTTPServer

QUOTES_FILE = "/data/quotes.json"

def load_quotes():
    with open(QUOTES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/quote":
            try:
                quotes = load_quotes()
                quote = random.choice(quotes)
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.end_headers()
                self.wfile.write(json.dumps(quote).encode())
            except Exception:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error":"could not load quotes"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, *args):
        pass 
    
if __name__ == "__main__":
    print("API running on port 5000")
    HTTPServer(("0.0.0.0", 5000), Handler).serve_forever()