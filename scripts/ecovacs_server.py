"""
ecovacs_server.py - Local HTTP server for DEEBOT joystick dashboard
Supports Cloudflare Tunnel for remote access.
Usage: python ecovacs_server.py
"""
import json
import subprocess
import sys
import os
import re
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PYTHON = sys.executable
SCRIPT = str(Path(__file__).parent / "ecovacs.py")
PORT   = 8765
CLOUDFLARED = str(Path(__file__).parent / "cloudflared.exe")
TUNNEL_URL_FILE = str(Path(__file__).parent / "tunnel_url.txt")

def run_ecovacs(cmd, arg=None):
    try:
        args = [PYTHON, SCRIPT, cmd]
        if arg: args.append(arg)
        result = subprocess.run(
            args,
            capture_output=True, text=True, timeout=35
        )
        out = result.stdout.strip()
        lines = out.split('\n')
        json_start = next((i for i, l in enumerate(lines) if l.strip().startswith('{')), None)
        if json_start is not None:
            return json.loads('\n'.join(lines[json_start:]))
        return {"error": "No JSON output", "raw": out}
    except Exception as e:
        return {"error": str(e)}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self._serve_file(Path(__file__).parent.parent / "ecovacs-joystick" / "index.html", 'text/html; charset=utf-8')
        elif self.path == '/tunnel':
            # Return current tunnel URL
            url = ''
            try:
                with open(TUNNEL_URL_FILE) as f:
                    url = f.read().strip()
            except:
                pass
            self._json({'url': url})
        elif self.path.startswith('/api/'):
            parts = self.path[5:].split('/', 1)
            cmd = parts[0]
            arg = parts[1] if len(parts) > 1 else None
            valid = ['status','clean','stop','pause','resume','charge','sound','fan_speed','water','mode','volume','count']
            if cmd not in valid:
                self._json({'error': f'Unknown: {cmd}'}, 400)
                return
            self._json(run_ecovacs(cmd, arg))
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_file(self, path, ct):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self._cors()
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404); self.end_headers()
            self.wfile.write(b'Not found')

    def _json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._cors()
        self.end_headers()
        self.wfile.write(body)

def start_tunnel():
    if not os.path.exists(CLOUDFLARED):
        print("cloudflared not found, skipping tunnel")
        return
    print("Starting Cloudflare tunnel...")
    proc = subprocess.Popen(
        [CLOUDFLARED, 'tunnel', '--url', f'http://localhost:{PORT}'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in proc.stdout:
        m = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
        if m:
            url = m.group(0)
            print(f"Tunnel URL: {url}")
            with open(TUNNEL_URL_FILE, 'w') as f:
                f.write(url)
            break

if __name__ == '__main__':
    # Start tunnel in background thread
    t = threading.Thread(target=start_tunnel, daemon=True)
    t.start()

    print(f"DEEBOT server running at http://localhost:{PORT}")
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    server.serve_forever()
