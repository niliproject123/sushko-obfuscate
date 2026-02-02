"""Desktop launcher — starts the FastAPI server and opens the browser."""

import os
import sys
import socket
import threading
import webbrowser
from pathlib import Path

import uvicorn


def get_base_dir() -> Path:
    """Return the base directory (works both frozen and unfrozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


def find_free_port() -> int:
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    base = get_base_dir()

    # Point the app at the bundled static files
    static_dir = base / "static"
    os.environ["STATIC_DIR"] = str(static_dir)

    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    # Open the browser after a short delay to let the server start
    threading.Timer(1.5, webbrowser.open, args=[url]).start()

    print(f"Starting Sushko on {url}")
    print("Close this window to stop the application.")

    uvicorn.run("api.main:app", host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
