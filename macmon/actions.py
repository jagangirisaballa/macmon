import os
import subprocess
import psutil
from pathlib import Path
from typing import Any

# Maps service display name → homebrew service name or stop command
_HOMEBREW_SERVICES = {
    "MongoDB": "mongodb-community",
    "PostgreSQL": "postgresql@15",
    "Redis": "redis",
    "Dolt": "dolt",
    "PHP": "php",
    "OpenVPN": "openvpn",
    "Unbound": "unbound",
    "Nginx": "nginx",
    "MySQL": "mysql",
}

# LaunchAgent services — label + plist path for proper unload/load
_LAUNCH_AGENTS = {
    "OpenAI Atlas": {
        "label": "com.openai.atlas.update-helper",
        "plist": str(Path.home() / "Library/LaunchAgents/com.openai.atlas.update-helper.plist"),
    },
}



def stop_service(name: str) -> dict[str, Any]:
    if name in _HOMEBREW_SERVICES:
        brew_name = _HOMEBREW_SERVICES[name]
        result = subprocess.run(
            ["brew", "services", "stop", brew_name],
            capture_output=True, text=True, timeout=15
        )
        success = result.returncode == 0
        return {"success": success, "message": result.stdout.strip() or result.stderr.strip()}

    if name in _LAUNCH_AGENTS:
        info = _LAUNCH_AGENTS[name]
        domain = f"gui/{os.getuid()}"
        result = subprocess.run(
            ["launchctl", "bootout", domain, info["plist"]],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return {"success": True, "message": f"{name} stopped"}
        return {"success": False, "message": result.stderr.strip() or f"Could not stop {name}"}

    return {"success": False, "message": f"Unknown service: {name}"}


def start_service(name: str) -> dict[str, Any]:
    if name in _HOMEBREW_SERVICES:
        brew_name = _HOMEBREW_SERVICES[name]
        result = subprocess.run(
            ["brew", "services", "start", brew_name],
            capture_output=True, text=True, timeout=15
        )
        success = result.returncode == 0
        return {"success": success, "message": result.stdout.strip() or result.stderr.strip()}
    if name in _LAUNCH_AGENTS:
        info = _LAUNCH_AGENTS[name]
        domain = f"gui/{os.getuid()}"
        result = subprocess.run(
            ["launchctl", "bootstrap", domain, info["plist"]],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return {"success": True, "message": f"{name} started"}
        return {"success": False, "message": result.stderr.strip() or f"Could not start {name}"}
    return {"success": False, "message": f"Auto-start not supported for {name} — start it manually"}


def stop_pid(pid: int) -> dict[str, Any]:
    """Stop an auto-discovered service (node/python/mcp) by PID."""
    return kill_process(pid)


def kill_process(pid: int) -> dict[str, Any]:
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        proc.wait(timeout=5)
        return {"success": True, "message": f"Killed {name} (PID {pid})"}
    except psutil.NoSuchProcess:
        return {"success": False, "message": f"Process {pid} not found"}
    except psutil.AccessDenied:
        return {"success": False, "message": f"Permission denied — cannot kill PID {pid}"}
    except psutil.TimeoutExpired:
        try:
            psutil.Process(pid).kill()
            return {"success": True, "message": f"Force-killed PID {pid}"}
        except Exception as e:
            return {"success": False, "message": str(e)}


def purge_memory() -> dict[str, Any]:
    """Purge macOS inactive memory pages via GUI auth dialog."""
    # Try passwordless first (works if sudoers rule is set)
    result = subprocess.run(["sudo", "-n", "purge"], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        return {"success": True, "message": "Inactive memory purged successfully"}

    # Fall back to osascript GUI auth dialog — user sees a macOS password prompt
    script = 'do shell script "purge" with administrator privileges'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        return {"success": True, "message": "Inactive memory purged successfully"}
    if "User canceled" in result.stderr:
        return {"success": False, "message": "Cancelled — password dialog dismissed"}
    return {"success": False, "message": "Purge failed: " + result.stderr.strip()}
