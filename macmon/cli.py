import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


PIDFILE = Path.home() / ".macmon.pid"
LOGFILE = Path.home() / ".macmon.log"


def _is_running() -> tuple[bool, int]:
    if not PIDFILE.exists():
        return False, 0
    try:
        pid = int(PIDFILE.read_text().strip())
        os.kill(pid, 0)  # check process exists
        return True, pid
    except (ProcessLookupError, ValueError, OSError):
        PIDFILE.unlink(missing_ok=True)
        return False, 0


def cmd_start(port: int, no_browser: bool):
    running, pid = _is_running()
    if running:
        print(f"macmon is already running (PID {pid}) → http://localhost:{port}")
        if not no_browser:
            subprocess.run(["open", f"http://localhost:{port}"])
        return

    print(f"Starting macmon on http://localhost:{port} ...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "macmon.server:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        stdout=open(LOGFILE, "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    PIDFILE.write_text(str(proc.pid))
    time.sleep(1.5)

    running, _ = _is_running()
    if running:
        print(f"macmon running (PID {proc.pid})")
        if not no_browser:
            subprocess.run(["open", f"http://localhost:{port}"])
    else:
        print("macmon failed to start. Check logs:")
        print(f"  cat {LOGFILE}")


def _find_macmon_pids() -> list[int]:
    """Find all running uvicorn macmon.server processes regardless of PID file."""
    import psutil
    pids = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = " ".join(proc.info["cmdline"] or [])
            if "uvicorn" in cmdline and "macmon.server" in cmdline:
                pids.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return pids


def cmd_stop():
    killed = []

    # Kill by PID file first
    running, pid = _is_running()
    if running:
        try:
            os.kill(pid, signal.SIGTERM)
            killed.append(pid)
        except ProcessLookupError:
            pass
    PIDFILE.unlink(missing_ok=True)

    # Always scan for any remaining macmon processes — catches restart-spawned or orphaned procs
    for pid in _find_macmon_pids():
        if pid not in killed:
            try:
                os.kill(pid, signal.SIGTERM)
                killed.append(pid)
            except (ProcessLookupError, PermissionError):
                pass

    if killed:
        print(f"macmon stopped (PID {', '.join(str(p) for p in killed)})")
    else:
        print("macmon is not running.")


def cmd_status(port: int):
    pids = _find_macmon_pids()
    if pids:
        print(f"macmon is running (PID {', '.join(str(p) for p in pids)}) → http://localhost:{port}")
    else:
        print("macmon is not running. Start with: macmon start")


def cmd_logs():
    if LOGFILE.exists():
        print(LOGFILE.read_text()[-4000:])
    else:
        print("No log file found.")


def main():
    parser = argparse.ArgumentParser(
        prog="macmon",
        description="macmon — Mac system monitoring dashboard",
    )
    sub = parser.add_subparsers(dest="command")

    p_start = sub.add_parser("start", help="Start the dashboard")
    p_start.add_argument("--port", type=int, default=9999, help="Port (default: 9999)")
    p_start.add_argument("--no-browser", action="store_true", help="Don't open browser")

    p_stop = sub.add_parser("stop", help="Stop the dashboard")

    p_status = sub.add_parser("status", help="Check if running")
    p_status.add_argument("--port", type=int, default=9999)

    sub.add_parser("logs", help="Show recent logs")

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args.port, args.no_browser)
    elif args.command == "stop":
        cmd_stop()
    elif args.command == "status":
        cmd_status(args.port)
    elif args.command == "logs":
        cmd_logs()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
