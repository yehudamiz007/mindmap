"""
lgtv_server.py - LG WebOS TV control server
Port: 8766
API: POST /api/cmd  {"cmd": "...", "arg": "..."}
"""
import asyncio, json, os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

try:
    from aiowebostv import WebOsClient
except ImportError:
    print("ERROR: aiowebostv not installed. Run: pip install aiowebostv")
    sys.exit(1)

TV_IP = os.environ.get("LGTV_IP", "192.168.68.111")  # change if needed
CLIENT_KEY_FILE = os.path.join(os.path.dirname(__file__), "lgtv_key.txt")

def load_client_key():
    if os.path.exists(CLIENT_KEY_FILE):
        with open(CLIENT_KEY_FILE) as f:
            return f.read().strip() or None
    return None

def save_client_key(key):
    with open(CLIENT_KEY_FILE, "w") as f:
        f.write(key or "")

async def run_tv_command(cmd, arg=None):
    client_key = load_client_key()
    client = WebOsClient(TV_IP, client_key=client_key)
    
    try:
        await client.connect()
        
        # Save new client key if we got one
        if client.client_key and client.client_key != client_key:
            save_client_key(client.client_key)
        
        result = {"ok": True, "cmd": cmd}
        
        if cmd == "power_off":
            await client.power_off()
        elif cmd == "volume_up":
            await client.volume_up()
        elif cmd == "volume_down":
            await client.volume_down()
        elif cmd == "mute":
            await client.set_mute(True)
        elif cmd == "unmute":
            await client.set_mute(False)
        elif cmd == "set_volume":
            await client.set_volume(int(arg or 10))
        elif cmd == "channel_up":
            await client.channel_up()
        elif cmd == "channel_down":
            await client.channel_down()
        elif cmd == "home":
            await client.send_button("HOME")
        elif cmd == "back":
            await client.send_button("BACK")
        elif cmd == "ok":
            await client.send_button("ENTER")
        elif cmd == "up":
            await client.send_button("UP")
        elif cmd == "down":
            await client.send_button("DOWN")
        elif cmd == "left":
            await client.send_button("LEFT")
        elif cmd == "right":
            await client.send_button("RIGHT")
        elif cmd == "num":
            btn = f"{'0' if not arg else arg}"
            await client.send_button(f"DIGIT_{btn}")
        elif cmd == "netflix":
            await client.launch_app("netflix")
        elif cmd == "youtube":
            await client.launch_app("youtube.leanback.v4")
        elif cmd == "disney":
            await client.launch_app("com.disney.disneyplus-prod")
        elif cmd == "prime":
            await client.launch_app("amazon")
        elif cmd == "status":
            info = await client.get_current_app()
            volume = await client.get_volume()
            result["app"] = str(info)
            result["volume"] = str(volume)
        elif cmd == "open_url":
            await client.open_url(arg or "https://google.com")
        elif cmd == "play":
            await client.send_button("PLAY")
        elif cmd == "pause":
            await client.send_button("PAUSE")
        elif cmd == "stop":
            await client.send_button("STOP")
        elif cmd == "rewind":
            await client.send_button("REWIND")
        elif cmd == "fast_forward":
            await client.send_button("FAST_FORWARD")
        else:
            result = {"ok": False, "error": f"Unknown command: {cmd}"}
        
        await client.disconnect()
        return result
        
    except Exception as e:
        try:
            await client.disconnect()
        except:
            pass
        return {"ok": False, "error": str(e)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Suppress access logs

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json({"ok": True, "tv_ip": TV_IP})
        elif parsed.path == "/tv_ip":
            self._json({"ip": TV_IP})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        
        try:
            data = json.loads(body)
        except:
            data = {}

        if parsed.path == "/api/cmd":
            cmd = data.get("cmd", "")
            arg = data.get("arg")
            result = asyncio.run(run_tv_command(cmd, arg))
            self._json(result)
        elif parsed.path == "/api/set_ip":
            new_ip = data.get("ip", "")
            if new_ip:
                global TV_IP
                TV_IP = new_ip
                self._json({"ok": True, "ip": TV_IP})
            else:
                self._json({"ok": False, "error": "No IP provided"})
        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = 8766
    print(f"LG TV Server running on port {port}")
    print(f"Target TV: {TV_IP}")
    print(f"Client key: {'loaded' if load_client_key() else 'none (will pair on first connect)'}")
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()
