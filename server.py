#!/usr/bin/env python3
"""
日本語 Dashboard — Local Server (with Jisho kanji-page proxy)
"""
import http.server
import socketserver
import webbrowser
import os
import sys
import socket
import glob
import json
import re
import urllib.request
import urllib.parse

PORT = 8080

# Find the directory containing dashboard.html. When running as a PyInstaller
# bundled .exe, files live next to the .exe (sys.executable), not next to
# the bundled __file__. Try both locations.
def find_dashboard_dir():
    candidates = []
    if getattr(sys, 'frozen', False):
        # Running as bundled exe — look next to the .exe
        candidates.append(os.path.dirname(os.path.abspath(sys.executable)))
        # Also check PyInstaller's _MEIPASS temp extraction dir
        if hasattr(sys, '_MEIPASS'):
            candidates.append(sys._MEIPASS)
    candidates.append(os.path.dirname(os.path.abspath(__file__)))
    for d in candidates:
        if os.path.exists(os.path.join(d, 'dashboard.html')):
            return d
    return candidates[0]

script_dir = find_dashboard_dir()
os.chdir(script_dir)

html_files = sorted(glob.glob("dashboard.html"), reverse=True)
if not html_files:
    print(f"\n  ERROR: dashboard.html not found in {script_dir}")
    print(f"  Make sure dashboard.html sits next to this exe / script.")
    input("\n  Press Enter to exit...")
    sys.exit(1)
html_file = html_files[0]

def kill_port(port):
    try:
        import subprocess
        result = subprocess.run(f'netstat -ano | findstr :{port}', shell=True, capture_output=True, text=True)
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if parts and parts[-1].isdigit():
                subprocess.run(f'taskkill /PID {parts[-1]} /F', shell=True, capture_output=True)
    except Exception:
        pass

def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

if not is_port_free(PORT):
    print(f"\n  Port {PORT} in use — freeing...")
    kill_port(PORT)
    import time; time.sleep(1)


def scrape_jisho_kanji(char):
    """Scrape Jisho's kanji detail page for meaning and readings."""
    url = f"https://jisho.org/search/{urllib.parse.quote(char)}%20%23kanji"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return {"error": str(e)}

    result = {"char": char, "meaning": "", "on": "", "kun": ""}

    # Meaning: <div class="kanji-details__main-meanings">  text  </div>
    m = re.search(r'<div class="kanji-details__main-meanings"[^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        result["meaning"] = re.sub(r'\s+', ' ', m.group(1)).strip()

    # On readings: dl with class containing on_yomi, then <a class="...">reading</a>
    on_block = re.search(r'<dl[^>]*class="[^"]*on_yomi[^"]*"[^>]*>(.*?)</dl>', html, re.DOTALL)
    if on_block:
        readings = re.findall(r'<a[^>]*>([^<]+)</a>', on_block.group(1))
        result["on"] = "・".join(r.strip() for r in readings if r.strip())

    # Kun readings
    kun_block = re.search(r'<dl[^>]*class="[^"]*kun_yomi[^"]*"[^>]*>(.*?)</dl>', html, re.DOTALL)
    if kun_block:
        readings = re.findall(r'<a[^>]*>([^<]+)</a>', kun_block.group(1))
        result["kun"] = "・".join(r.strip() for r in readings if r.strip())

    return result


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200); self.end_headers()

    def _json_response(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # /jisho?keyword=X — proxy to official Jisho API (for word search)
        if self.path.startswith('/jisho?'):
            try:
                qs = urllib.parse.urlparse(self.path).query
                keyword = urllib.parse.parse_qs(qs).get('keyword', [''])[0]
                if not keyword:
                    return self._json_response({"error": "missing keyword"}, 400)
                api = f"https://jisho.org/api/v1/search/words?keyword={urllib.parse.quote(keyword)}"
                req = urllib.request.Request(api, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    body = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                return self._json_response({"error": str(e)}, 500)

        # /kanji?char=X — scrape kanji-detail page for meaning + readings
        if self.path.startswith('/kanji?'):
            try:
                qs = urllib.parse.urlparse(self.path).query
                char = urllib.parse.parse_qs(qs).get('char', [''])[0]
                if not char:
                    return self._json_response({"error": "missing char"}, 400)
                return self._json_response(scrape_jisho_kanji(char))
            except Exception as e:
                return self._json_response({"error": str(e)}, 500)

        return super().do_GET()

    def log_message(self, format, *args):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    url = f"http://localhost:{PORT}/{html_file}"
    print(f"\n  日本語 Dashboard")
    print(f"  ─────────────────────────────")
    print(f"  File   : {html_file}")
    print(f"  URL    : {url}")
    print(f"  Endpts : /jisho?keyword=X    /kanji?char=X")
    print(f"  ─────────────────────────────")
    print(f"  Press Ctrl+C to stop.\n")
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        sys.exit(0)
