import json
import random
from http.server import BaseHTTPRequestHandler, HTTPServer

QUOTES = [
    {"text":"People's lives don't end when they die. It ends when they lose faith.", "char": "Itachi Uchiha"},
    {"text":"If you don't take risks, you can't create a future.", "char": "Monkey D. Luffy"},
    {"text":"A lesson without pain is meaningless.", "char": "Edward Elric"},
    {"text":"Hard work is worthless for those that don't believe in themselves.", "char": "Naruto Uzumaki"},
    {"text":"The world is not beautiful, therefore it is.", "char": "Kino"},
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/quote":
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps(random.choice(QUOTES)).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, *args):
        pass 
    
if __name__ == "__main__":
    print("API running on port 5000")
    HTTPServer(("0.0.0.0", 5000), Handler).serve_forever()