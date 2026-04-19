import subprocess
import shutil


def send(title: str, message: str, subtitle: str = "") -> None:
    """Send a macOS native notification. Falls back gracefully if tools unavailable."""
    if shutil.which("terminal-notifier"):
        cmd = [
            "terminal-notifier",
            "-title", title,
            "-message", message,
            "-sound", "default",
            "-group", "macmon",
        ]
        if subtitle:
            cmd += ["-subtitle", subtitle]
        try:
            subprocess.run(cmd, timeout=5, capture_output=True)
            return
        except Exception:
            pass

    # osascript fallback (always available on macOS)
    safe_title = title.replace('"', '\\"')
    safe_msg = message.replace('"', '\\"')
    script = f'display notification "{safe_msg}" with title "{safe_title}"'
    if subtitle:
        safe_sub = subtitle.replace('"', '\\"')
        script = f'display notification "{safe_msg}" with title "{safe_title}" subtitle "{safe_sub}"'
    try:
        subprocess.run(["osascript", "-e", script], timeout=5, capture_output=True)
    except Exception:
        pass


def notify_slow(status: str, reason: str) -> None:
    if status == "critical":
        send("macmon — System Critical", reason, subtitle="Your Mac needs attention")
    elif status == "warning":
        send("macmon — System Warning", reason, subtitle="Performance degrading")
