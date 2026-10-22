"""Windows launcher: a small control window owns one loopback-only app server."""

import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import tomllib
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import webbrowser

from version import APP_NAME, __version__


def application_directory() -> Path:
    """Source runs use this folder; frozen runs use an explicit bundled allowlist."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "application"
    return Path(__file__).resolve().parent


def default_data_directory() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    return (Path(base) if base else Path.home() / ".local" / "share") / "LifeDirectionAgent"


def unused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def theme_options(root: Path) -> dict:
    """Read public theme settings, never a user's private secrets.toml."""
    config = tomllib.loads((root / ".streamlit/config.toml").read_text(encoding="utf-8"))
    result = {}
    def flatten(prefix, values):
        for name, value in values.items():
            dotted = f"{prefix}.{name}" if prefix else name
            if isinstance(value, dict):
                flatten(dotted, value)
            else:
                result[dotted] = value
    flatten("", config)
    return result


def serve(port: int, data_directory: Path, *, smoke: bool = False) -> None:
    """Run the public Streamlit server API; no shell or external Python is needed."""
    root = application_directory()
    data_directory.mkdir(parents=True, exist_ok=True)
    os.chdir(data_directory)
    sys.path.insert(0, str(root))
    # A windowed PyInstaller program has no console streams. Logging libraries
    # still expect a writable object, so give them an app-local stream.
    log = None
    if sys.stdout is None or sys.stderr is None:
        log = (data_directory / "desktop.log").open("a", encoding="utf-8")
        sys.stdout = sys.stdout or log
        sys.stderr = sys.stderr or log
    import streamlit as st
    options = theme_options(root)
    options.update({
        "server.address": "127.0.0.1",
        "server.port": port,
        "server.headless": True,
        "server.fileWatcherType": "none",
        "server.runOnSave": False,
        "browser.gatherUsageStats": False,
        "global.developmentMode": False,
    })
    if smoke:
        # Pinned Streamlit 1.66 smoke testing only; not an application API.
        options["server.scriptHealthCheckEnabled"] = True
    st.App(str(root / "app.py")).run(config=options)


def start_server(port: int, data_directory: Path, *, smoke: bool = False):
    data_directory.mkdir(parents=True, exist_ok=True)
    command = [sys.executable]
    if not getattr(sys, "frozen", False):
        command.append(str(Path(__file__).resolve()))
    command.extend(["--serve", "--port", str(port), "--data-dir", str(data_directory)])
    if smoke:
        command.append("--smoke")
    log = (data_directory / "desktop.log").open("a", encoding="utf-8")
    try:
        return subprocess.Popen(
            command, stdout=log, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    finally:
        log.close()


def stop_server(child) -> None:
    """Stop only the process this launcher created, including on smoke failure."""
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=10)


def read_local(url: str, *, timeout: float = 2.0) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": "LifeDirectionAgent-local-check"}), timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError("Local app did not return a successful response.")
        return response.read()


def wait_until_ready(child, url: str, *, seconds: float = 90) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise RuntimeError("The local app stopped during startup. See desktop.log in the app data folder.")
        try:
            read_local(url + "/_stcore/health", timeout=0.5)
            return
        except (OSError, URLError):
            time.sleep(0.15)
    raise RuntimeError("The local app did not finish starting. See desktop.log in the app data folder.")


def self_test(data_directory: Path) -> dict:
    """Exercise bundled code, frontend assets, and the script with no paid call."""
    from mentors import MENTORS
    from models import PlanValidationError, parse_plan
    import tkinter as tk
    probe = tk.Tk()
    probe.withdraw()
    probe.update_idletasks()
    probe.destroy()
    task = {"title": "Choose a next step", "action": "Write a short note.", "start_day": 1, "end_day": 1, "reason": "Clarifies a priority.", "completion_criterion": "One note written."}
    raw = json.dumps({"summary": "A short exploration.", "assumptions": [], "duration_days": 1, "tasks": [task, task, task]})
    parse_plan(raw, expected_days=1)
    try:
        parse_plan(raw, expected_days=2)
    except PlanValidationError:
        pass
    else:
        raise RuntimeError("Bundled plan validation failed.")
    port = unused_port()
    url = f"http://127.0.0.1:{port}"
    child = start_server(port, data_directory, smoke=True)
    try:
        wait_until_ready(child, url)
        document = read_local(url + "/").decode("utf-8")
        match = re.search(r'<script[^>]+src=["\']([^"\']+)', document)
        if not match:
            raise RuntimeError("The bundled frontend script was not found.")
        asset = urljoin(url + "/", match.group(1))
        if not asset.startswith(url + "/"):
            raise RuntimeError("The app unexpectedly required an external frontend asset.")
        if not read_local(asset):
            raise RuntimeError("The bundled frontend asset was empty.")
        read_local(url + "/_stcore/script-health-check", timeout=30)
        return {"ok": True, "version": __version__, "mentor_count": len(MENTORS), "native_launcher": "passed", "plan_validation": "passed", "server_health": "passed", "frontend_asset": "passed", "app_script": "passed", "paid_api_requests": 0}
    finally:
        stop_server(child)


def show_control_window(data_directory: Path) -> None:
    """Keep server ownership visible; closing this window stops the local app."""
    import tkinter as tk
    from tkinter import messagebox, ttk
    window = tk.Tk()
    window.title(APP_NAME)
    window.geometry("440x220")
    window.resizable(False, False)
    frame = ttk.Frame(window, padding=24)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=APP_NAME, font=("Segoe UI", 17, "bold")).pack(anchor="w")
    ttk.Label(frame, text=f"Version {__version__}").pack(anchor="w", pady=(4, 12))
    status = tk.StringVar(value="Starting your app...")
    ttk.Label(frame, textvariable=status, wraplength=380).pack(anchor="w")
    ttk.Label(frame, text="Closing this window stops the app.").pack(anchor="w", pady=(8, 12))
    row = ttk.Frame(frame)
    row.pack(anchor="w")
    port = unused_port()
    url = f"http://127.0.0.1:{port}"
    child = start_server(port, data_directory)
    opened = False
    deadline = time.monotonic() + 90
    open_button = ttk.Button(row, text="Open app", state="disabled", command=lambda: webbrowser.open(url))
    open_button.pack(side="left", padx=(0, 10))
    def close():
        stop_server(child)
        window.destroy()
    ttk.Button(row, text="Quit", command=close).pack(side="left")
    window.protocol("WM_DELETE_WINDOW", close)
    def poll():
        nonlocal opened
        if child.poll() is not None:
            status.set("The local app has stopped.")
            if not opened:
                messagebox.showerror(APP_NAME, "The app could not start. See desktop.log in the app data folder.")
            return
        if not opened:
            try:
                read_local(url + "/_stcore/health", timeout=0.25)
            except (OSError, URLError):
                if time.monotonic() > deadline:
                    status.set("Startup took too long. Quit and try again.")
                    stop_server(child)
                    return
            else:
                opened = True
                status.set("Ready. Your app is running locally in your browser.")
                open_button.configure(state="normal")
                webbrowser.open(url)
        window.after(750, poll)
    window.after(150, poll)
    try:
        window.mainloop()
    finally:
        stop_server(child)


def main() -> int:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, default=8501, help=argparse.SUPPRESS)
    parser.add_argument("--data-dir", type=Path, default=default_data_directory(), help=argparse.SUPPRESS)
    parser.add_argument("--smoke", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--self-test", action="store_true", help="Check the bundled app without calling DeepSeek.")
    parser.add_argument("--report", type=Path, help="Write the self-test result to this file.")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("The local port must be from 1 to 65535.")
    if args.serve:
        serve(args.port, args.data_dir, smoke=args.smoke)
        return 0
    if args.self_test:
        try:
            report = self_test(args.data_dir)
        except Exception as error:
            report = {"ok": False, "version": __version__, "error_type": type(error).__name__, "message": "The bundled app check failed; inspect the local desktop.log."}
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        elif sys.stdout:
            print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1
    show_control_window(args.data_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
