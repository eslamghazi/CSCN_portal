"""Run the FastAPI app with uvicorn behind a small status window.

The server runs in a background thread; the main thread shows a Tkinter window
with the local URL, the LAN URL (for other PCs), and Open / Copy / Stop buttons.
Uses the pure-Python asyncio + h11 stack only (uvloop/httptools are unavailable
on Windows / py3.8 / 32-bit). If the window can't start, it falls back to running
the server in the foreground.
"""
import os
import socket
import threading
import webbrowser

import uvicorn
from loguru import logger

from api.config_api import HOST, DEFAULT_PORT, resolve_resource

APP_TITLE = "نظام إدارة مركز الخدمة المجتمعية"


def _ensure_firewall(web_port: int):
    """Open the web (and peer) port in Windows Firewall so other PCs on the LAN
    can reach the portal at http://<this-ip>:<port>/. Tries silently first (works
    if elevated); otherwise asks once via UAC and remembers it asked."""
    try:
        from application.services import firewall
        if not firewall.is_windows():
            return
        try:
            from application.services.peer_server import DEFAULT_PORT as PEER_PORT
        except Exception:
            PEER_PORT = 50525
        ports = [web_port, PEER_PORT]
        if firewall.try_add_rule_silent(ports):
            return
        from config.settings import DATA_DIR
        marker = DATA_DIR / ".firewall_prompted"
        if marker.exists():
            return
        firewall.allow_ports(ports)   # one-time UAC prompt
        try:
            marker.write_text("1", encoding="utf-8")
        except OSError:
            pass
    except Exception as e:
        logger.debug("Firewall setup skipped: {}", e)


def _find_free_port(preferred: int, host: str = "127.0.0.1") -> int:
    for port in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    return preferred


def _already_running(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def _open_browser_when_ready(port: int):
    url = f"http://127.0.0.1:{port}/"

    def _wait_and_open():
        for _ in range(100):  # up to ~10s
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                    break
            except OSError:
                threading.Event().wait(0.1)
        try:
            webbrowser.open(url)
        except Exception:
            logger.warning("Could not open a browser automatically. Open: {}", url)

    threading.Thread(target=_wait_and_open, daemon=True).start()


def _lan_ip() -> str:
    """Best-effort primary LAN IPv4 of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def _run_with_window(server, port: int) -> bool:
    """Show a small status window (Tkinter). Returns False if it can't start."""
    try:
        import tkinter as tk
    except Exception as e:
        logger.warning("Status window unavailable ({}); running in foreground.", e)
        return False

    local_url = f"http://localhost:{port}"
    net_url = f"http://{_lan_ip()}:{port}"

    # Palette (teal/emerald) to match the app.
    PRIMARY, PRIMARY_HOVER, INK, MUTED = "#0F766E", "#0D9488", "#14201E", "#6B7B78"
    BG, BOX_BG, BORDER, DANGER = "#F6F8F8", "#EEF4F3", "#D7E0DE", "#B91C1C"

    try:
        root = tk.Tk()
    except Exception as e:
        logger.warning("Tk init failed ({}); running in foreground.", e)
        return False

    root.title(APP_TITLE)
    root.configure(bg=BG)
    root.resizable(False, False)
    try:
        ico = resolve_resource("ui/resources/icons/app.ico")
        if ico.exists():
            root.iconbitmap(str(ico))
    except Exception:
        pass

    W, H = 540, 380
    root.update_idletasks()
    x = (root.winfo_screenwidth() - W) // 2
    y = (root.winfo_screenheight() - H) // 3
    root.geometry(f"{W}x{H}+{x}+{y}")

    FA = ("Segoe UI", 11)
    pad = {"bg": BG}

    tk.Label(root, text=APP_TITLE, font=("Segoe UI", 15, "bold"), fg=PRIMARY, **pad).pack(pady=(22, 4))
    tk.Label(root, text="البرنامج يعمل. اترك هذه النافذة مفتوحة أثناء الاستخدام.",
             font=("Segoe UI", 10), fg=MUTED, **pad).pack(pady=(0, 14))

    def url_block(label_text, url_text):
        tk.Label(root, text=label_text, font=FA, fg=INK, anchor="e", **pad).pack(fill="x", padx=40)
        box = tk.Frame(root, bg=BOX_BG, highlightbackground=BORDER, highlightthickness=1)
        box.pack(fill="x", padx=40, pady=(3, 12))
        e = tk.Entry(box, font=("Consolas", 11), fg=PRIMARY, bg=BOX_BG, bd=0,
                     readonlybackground=BOX_BG, justify="center")
        e.insert(0, url_text)
        e.configure(state="readonly")
        e.pack(fill="x", ipady=7, padx=6)
        return e

    url_block("العنوان على هذا الجهاز:", local_url)
    url_block("العنوان على الشبكة (للأجهزة الأخرى):", net_url)

    def do_open():
        try:
            webbrowser.open(local_url + "/")
        except Exception:
            pass

    def do_copy():
        root.clipboard_clear()
        root.clipboard_append(net_url)
        copy_btn.config(text="✓ تم النسخ")
        root.after(1500, lambda: copy_btn.config(text="نسخ عنوان الشبكة"))

    def do_quit():
        logger.info("Stop requested from status window; shutting down server.")
        server.should_exit = True
        try:
            root.destroy()
        except Exception:
            pass

    def mkbtn(parent, text, cmd, bg, fg="#FFFFFF", hover=None):
        b = tk.Button(parent, text=text, command=cmd, font=("Segoe UI", 10, "bold"),
                      bg=bg, fg=fg, activebackground=hover or bg, activeforeground=fg,
                      relief="flat", bd=0, padx=14, pady=9, cursor="hand2")
        if hover:
            b.bind("<Enter>", lambda _e: b.config(bg=hover))
            b.bind("<Leave>", lambda _e: b.config(bg=bg))
        return b

    btns = tk.Frame(root, bg=BG)
    btns.pack(pady=(8, 0))
    mkbtn(btns, "فتح في المتصفح", do_open, PRIMARY, hover=PRIMARY_HOVER).pack(side="right", padx=5)
    copy_btn = mkbtn(btns, "نسخ عنوان الشبكة", do_copy, "#FFFFFF", fg=INK, hover="#E9F0EF")
    copy_btn.config(highlightbackground=BORDER)
    copy_btn.pack(side="right", padx=5)
    mkbtn(btns, "إيقاف وإغلاق", do_quit, "#FDEAEA", fg=DANGER, hover="#F8DADA").pack(side="right", padx=5)

    root.protocol("WM_DELETE_WINDOW", do_quit)
    try:
        root.mainloop()
        return True
    except Exception as e:
        logger.warning("Status window loop failed ({}); running in foreground.", e)
        return False


def run(app, host: str = HOST, port: int = DEFAULT_PORT, open_browser: bool = True):
    # Single-instance: if a portal already answers on the default port, just
    # reopen the browser instead of starting a second server.
    if _already_running(port):
        logger.info("CSCN portal already running on :{}; opening browser.", port)
        try:
            webbrowser.open(f"http://127.0.0.1:{port}/")
        except Exception:
            pass
        return

    port = _find_free_port(port)
    os.environ["CSCN_portal_ACTIVE_PORT"] = str(port)   # so the API can report the real port
    _ensure_firewall(port)
    logger.info("Starting CSCN_portal web server on http://{}:{}/ (LAN) — local: http://127.0.0.1:{}/",
                host, port, port)

    # log_config=None: don't let uvicorn install its own logging (its colourized
    # formatter calls sys.stdout.isatty(), which fails in a --windowed build).
    config = uvicorn.Config(app, host=host, port=port, loop="asyncio", http="h11",
                            log_config=None, log_level="warning", access_log=False)
    server = uvicorn.Server(config)

    # Run the server in a background thread so the window can own the main thread.
    server_thread = threading.Thread(target=server.run, daemon=True, name="uvicorn")
    server_thread.start()

    if open_browser:
        _open_browser_when_ready(port)

    # Status window on the main thread. Fall back to foreground if it can't start.
    if not _run_with_window(server, port):
        try:
            server_thread.join()
        except KeyboardInterrupt:
            server.should_exit = True
