#!/usr/bin/env python3
"""
日本語 Dashboard — Local Server with system tray icon.

Runs hidden in the system tray. Click the icon to open the dashboard,
right-click for menu (Auto-start, Quit, etc.).
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
import threading
import urllib.request
import urllib.parse

PORT = 8080

# ────────────────────────────────────────────────────────────────
# File / path helpers
# ────────────────────────────────────────────────────────────────
def find_dashboard_dir():
    """Find dashboard.html — try near the exe, in PyInstaller temp, then near script."""
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(os.path.dirname(os.path.abspath(sys.executable)))
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
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            f"dashboard.html not found in:\n{script_dir}\n\nMake sure it sits next to this exe.",
            "Nihongo Dashboard — Error",
            0x10,
        )
    except Exception:
        pass
    sys.exit(1)
html_file = html_files[0]


# ────────────────────────────────────────────────────────────────
# Port handling
# ────────────────────────────────────────────────────────────────
def kill_port(port):
    try:
        import subprocess
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True, capture_output=True, text=True,
            startupinfo=startupinfo,
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if parts and parts[-1].isdigit():
                subprocess.run(
                    f'taskkill /PID {parts[-1]} /F',
                    shell=True, capture_output=True,
                    startupinfo=startupinfo,
                )
    except Exception:
        pass


def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0


# ────────────────────────────────────────────────────────────────
# Jisho proxies
# ────────────────────────────────────────────────────────────────
def scrape_jisho_kanji(char):
    url = f"https://jisho.org/search/{urllib.parse.quote(char)}%20%23kanji"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return {"error": str(e)}

    result = {"char": char, "meaning": "", "on": "", "kun": ""}
    m = re.search(r'<div class="kanji-details__main-meanings"[^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        result["meaning"] = re.sub(r'\s+', ' ', m.group(1)).strip()
    on_block = re.search(r'<dl[^>]*class="[^"]*on_yomi[^"]*"[^>]*>(.*?)</dl>', html, re.DOTALL)
    if on_block:
        readings = re.findall(r'<a[^>]*>([^<]+)</a>', on_block.group(1))
        result["on"] = "・".join(r.strip() for r in readings if r.strip())
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


# ────────────────────────────────────────────────────────────────
# Server thread
# ────────────────────────────────────────────────────────────────
DASHBOARD_URL = f"http://localhost:{PORT}/{html_file}"
_httpd = None


def run_server():
    global _httpd
    socketserver.TCPServer.allow_reuse_address = True
    if not is_port_free(PORT):
        kill_port(PORT)
        import time; time.sleep(1)
    try:
        _httpd = socketserver.TCPServer(("", PORT), Handler)
        _httpd.serve_forever()
    except OSError:
        pass


def stop_server():
    global _httpd
    try:
        if _httpd:
            _httpd.shutdown()
            _httpd.server_close()
    except Exception:
        pass


# ────────────────────────────────────────────────────────────────
# Auto-start (Windows registry, no admin needed)
# ────────────────────────────────────────────────────────────────
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "NihongoDashboard"


def _exe_path():
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}" --silent'
    return f'"{sys.executable}" "{os.path.abspath(__file__)}" --silent'


def is_autostart_enabled():
    if sys.platform != 'win32':
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            try:
                winreg.QueryValueEx(k, APP_NAME)
                return True
            except FileNotFoundError:
                return False
    except Exception:
        return False


def set_autostart(enable):
    if sys.platform != 'win32':
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if enable:
                winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _exe_path())
            else:
                try:
                    winreg.DeleteValue(k, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


# ────────────────────────────────────────────────────────────────
# Tray icon
# ────────────────────────────────────────────────────────────────
def make_icon_image():
    """Inline tray icon — kanji 日 on circular background."""
    from PIL import Image, ImageDraw, ImageFont
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, size - 2, size - 2), fill=(168, 57, 47, 255))
    text = "日"
    fnt = None
    for path in (
        "C:/Windows/Fonts/YuGothM.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
    ):
        try:
            fnt = ImageFont.truetype(path, 38)
            break
        except Exception:
            continue
    if fnt is None:
        try:
            fnt = ImageFont.load_default()
            text = "JP"
        except Exception:
            return img
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
              text, font=fnt, fill=(245, 240, 232, 255))
    return img


def open_dashboard(*_):
    webbrowser.open(DASHBOARD_URL)


def quit_app(icon, *_):
    stop_server()
    icon.stop()


def toggle_autostart(icon, item):
    set_autostart(not is_autostart_enabled())
    icon.update_menu()


def run_tray():
    try:
        import pystray
    except ImportError:
        webbrowser.open(DASHBOARD_URL)
        try:
            while True:
                import time; time.sleep(60)
        except KeyboardInterrupt:
            stop_server()
        return

    menu = pystray.Menu(
        pystray.MenuItem("Open Dashboard", open_dashboard, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Start with Windows",
            toggle_autostart,
            checked=lambda item: is_autostart_enabled(),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )
    icon = pystray.Icon(
        "NihongoDashboard",
        icon=make_icon_image(),
        title="Nihongo Dashboard",
        menu=menu,
    )
    icon.run()


# ────────────────────────────────────────────────────────────────
# Entry
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Open browser unless --silent (used for auto-start at boot)
    if '--silent' not in sys.argv:
        def open_when_ready():
            import time
            for _ in range(20):
                time.sleep(0.1)
                if not is_port_free(PORT):
                    webbrowser.open(DASHBOARD_URL)
                    return
        threading.Thread(target=open_when_ready, daemon=True).start()

    run_tray()
