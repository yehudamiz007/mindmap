"""
deebot_autostart.py
Starts ecovacs_server.py + cloudflare tunnel,
waits for tunnel URL, then updates the GitHub Pages HTML automatically
via git push so the app always points to the right URL.
"""
import subprocess, sys, os, re, time, json
from pathlib import Path

PYTHON      = sys.executable
BASE        = Path(__file__).parent
SERVER      = BASE / "ecovacs_server.py"
CLOUDFLARED = BASE / "cloudflared.exe"
TUNNEL_FILE = BASE / "tunnel_url.txt"
HTML_FILE   = BASE.parent / "ecovacs-joystick" / "index.html"
REPO        = BASE.parent

def get_tunnel_url(timeout=60):
    """Start cloudflared and wait for tunnel URL."""
    proc = subprocess.Popen(
        [str(CLOUDFLARED), 'tunnel', '--url', 'http://localhost:8765'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding='utf-8', errors='replace'
    )
    deadline = time.time() + timeout
    for line in proc.stdout:
        m = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
        if m:
            return m.group(0), proc
        if time.time() > deadline:
            break
    return None, proc

def update_html(url):
    """Replace the tunnel URL in the HTML file - preserving UTF-8."""
    content = HTML_FILE.read_text(encoding='utf-8')
    updated = re.sub(r'https://[a-z0-9\-]+\.trycloudflare\.com', url, content)
    HTML_FILE.write_text(updated, encoding='utf-8', newline='\n')
    print(f"Updated HTML with: {url}")

def git_push(url):
    """Commit and push the updated HTML."""
    os.chdir(REPO)
    subprocess.run(['git', 'add', 'ecovacs-joystick/index.html'], check=True)
    subprocess.run(['git', 'commit', '-m', f'auto: update tunnel URL to {url}'], check=True)
    result = subprocess.run(['git', 'push', 'origin', 'main'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("Pushed to GitHub Pages - app updated!")
    else:
        print("Git push output:", result.stderr)

if __name__ == '__main__':
    print("Starting DEEBOT server...")

    # Start server
    server_proc = subprocess.Popen([PYTHON, str(SERVER)])
    time.sleep(2)

    print("Starting Cloudflare tunnel...")
    url, tunnel_proc = get_tunnel_url(timeout=60)

    if not url:
        print("ERROR: Could not get tunnel URL")
        sys.exit(1)

    print(f"\nTunnel URL: {url}")
    print(f"App: https://yehudamiz007.github.io/mindmap/ecovacs-joystick/\n")

    # Save URL
    TUNNEL_FILE.write_text(url)

    # Update GitHub Pages
    update_html(url)
    git_push(url)

    print("\nAll running! Open app on your phone.")
    print("Press Ctrl+C to stop.\n")

    try:
        server_proc.wait()
    except KeyboardInterrupt:
        server_proc.terminate()
        tunnel_proc.terminate()
        print("Stopped.")
