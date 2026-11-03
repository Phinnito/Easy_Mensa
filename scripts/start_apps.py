from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APPS = [
    ("ChefHuang", "apps/admin_app.py", 8501, Path("/tmp/easy_mensa_admin.log")),
    ("Chaetzli", "apps/user_app.py", 8502, Path("/tmp/easy_mensa_user.log")),
]


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def stop_old_processes() -> None:
    for _name, app, _port, _log in APPS:
        subprocess.run(
            ["pkill", "-f", f"streamlit run {app}"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def start_app(name: str, app: str, port: int, log_path: Path) -> subprocess.Popen:
    log_handle = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            app,
            "--server.address",
            "0.0.0.0",
            "--server.port",
            str(port),
            "--server.headless",
            "true",
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print(f"Started {name} on port {port} (pid={process.pid})", flush=True)
    return process


def show_log(path: Path) -> None:
    if not path.exists():
        return
    print(f"\n--- {path} ---", flush=True)
    try:
        print(path.read_text(encoding="utf-8")[-5000:], flush=True)
    except OSError:
        pass


def main() -> int:
    stop_old_processes()

    processes = [
        (name, port, log_path, start_app(name, app, port, log_path))
        for name, app, port, log_path in APPS
    ]

    deadline = time.time() + 45
    while time.time() < deadline:
        if all(port_open(port) for _name, port, _log, _process in processes):
            print("Easy_Mensa apps are ready.", flush=True)
            return 0

        for name, port, log_path, process in processes:
            if process.poll() is not None and not port_open(port):
                print(f"{name} exited before port {port} opened.", flush=True)
                show_log(log_path)
                return 1

        time.sleep(1)

    print("Timed out waiting for Streamlit ports.", flush=True)
    for _name, _port, log_path, _process in processes:
        show_log(log_path)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
