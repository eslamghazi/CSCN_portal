"""Run the FastAPI app with uvicorn behind a system-tray icon.

The server runs in a background thread; the main thread shows a tray icon with
the local URL, an "Open" action, and a "Quit" action. Uses the pure-Python
asyncio + h11 stack only (uvloop/httptools are unavailable on Windows / py3.8 /
32-bit). If the tray can't start (no Pillow/pystray), it falls back to running
the server in the foreground.
"""
import socket
import threading
import webbrowser

import uvicorn
from loguru import logger

from api.config_api import HOST, DEFAULT_PORT, resolve_resource


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


def _tray_image():
    """Load the app icon for the tray, falling back to a drawn teal disc."""
    from PIL import Image, ImageDraw
    for name in ("ui/resources/icons/app.png", "ui/resources/icons/app.ico"):
        try:
            path = resolve_resource(name)
            if path.exists():
                return Image.open(str(path)).convert("RGBA")
        except Exception:
            pass
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 60, 60), fill=(15, 118, 110, 255))   # teal #0F766E
    d.text((22, 20), "C", fill=(255, 255, 255, 255))
    return img


def _run_with_tray(server, port: int) -> bool:
    """Show a tray icon; returns False if the tray couldn't be created."""
    try:
        import pystray
    except Exception as e:
        logger.warning("Tray unavailable ({}); running server in foreground.", e)
        return False

    url = f"http://127.0.0.1:{port}/"

    def on_open(icon, item):
        try:
            webbrowser.open(url)
        except Exception:
            pass

    def on_quit(icon, item):
        logger.info("Quit requested from tray; shutting down server.")
        server.should_exit = True
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(f"العنوان: {url}", None, enabled=False),
        pystray.MenuItem("فتح البوابة", on_open, default=True),
        pystray.MenuItem("إنهاء", on_quit),
    )
    try:
        icon = pystray.Icon("cscn_portal", _tray_image(), "بوابة CSCN", menu)
        icon.run()  # blocks the main thread until on_quit -> icon.stop()
        return True
    except Exception as e:
        logger.warning("Tray icon failed to start ({}); running in foreground.", e)
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
    logger.info("Starting CSCN_portal web server on http://{}:{}/ (LAN) — local: http://127.0.0.1:{}/",
                host, port, port)

    # log_config=None: don't let uvicorn install its own logging (its colourized
    # formatter calls sys.stdout.isatty(), which fails in a --windowed build).
    config = uvicorn.Config(app, host=host, port=port, loop="asyncio", http="h11",
                            log_config=None, log_level="warning", access_log=False)
    server = uvicorn.Server(config)

    # Run the server in a background thread so the tray can own the main thread.
    server_thread = threading.Thread(target=server.run, daemon=True, name="uvicorn")
    server_thread.start()

    if open_browser:
        _open_browser_when_ready(port)

    # Tray on the main thread (Windows requirement). Fall back to foreground.
    if not _run_with_tray(server, port):
        try:
            server_thread.join()
        except KeyboardInterrupt:
            server.should_exit = True
