import json
import os
import re
import shutil
import psutil
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

_cpu_history: list[float] = []
_last_slow_notification = 0.0
NOTIFICATION_COOLDOWN = 300  # seconds between repeat notifications


def _get_cpu() -> dict[str, Any]:
    percent = psutil.cpu_percent(interval=0.5)
    _cpu_history.append(percent)
    if len(_cpu_history) > 30:
        _cpu_history.pop(0)
    return {"percent": round(percent, 1), "cores": psutil.cpu_count()}


def _get_memory() -> dict[str, Any]:
    vm = psutil.virtual_memory()
    # macOS compressed memory via vm_stat
    compressed_gb = 0.0
    try:
        out = subprocess.check_output(["vm_stat"], text=True)
        page_size = 16384  # default — overridden by vm_stat header if present
        for line in out.splitlines():
            if "page size of" in line:
                m = re.search(r"page size of (\d+)", line)
                if m:
                    page_size = int(m.group(1))
            if "stored in compressor" in line:
                pages = int(line.split(":")[1].strip().rstrip("."))
                compressed_gb = round(pages * page_size / 1e9, 2)
                break
    except Exception:
        pass
    return {
        "total_gb": round(vm.total / 1e9, 1),
        "used_gb": round(vm.used / 1e9, 2),
        "free_gb": round(vm.available / 1e9, 2),
        "percent": round(vm.percent, 1),
        "compressed_gb": compressed_gb,
    }


def _get_swap() -> dict[str, Any]:
    sw = psutil.swap_memory()
    return {
        "total_gb": round(sw.total / 1e9, 2),
        "used_gb": round(sw.used / 1e9, 2),
        "percent": round(sw.percent, 1),
    }


def _get_disk() -> dict[str, Any]:
    d = psutil.disk_usage("/")
    return {
        "total_gb": round(d.total / 1e9, 1),
        "used_gb": round(d.used / 1e9, 1),
        "free_gb": round(d.free / 1e9, 1),
        "percent": round(d.percent, 1),
    }


# macmon's own PID — shown but flagged as self so UI can warn
_OWN_PID = os.getpid()

# Seed psutil's per-process CPU% baseline — without this the first call always returns 0.0
psutil.cpu_percent(interval=None)
for _p in psutil.process_iter(["cpu_percent"]):
    try:
        _p.cpu_percent(interval=None)
    except Exception:
        pass

_KNOWN_SERVICES_FILE = Path.home() / ".macmon_known_services"

def _load_known_services() -> set[str]:
    try:
        return set(_KNOWN_SERVICES_FILE.read_text().splitlines())
    except Exception:
        return set()

def _save_known_services(names: set[str]) -> None:
    try:
        _KNOWN_SERVICES_FILE.write_text("\n".join(sorted(names)))
    except Exception:
        pass

_seen_service_names: set[str] = _load_known_services()


def _get_brew_services() -> tuple[dict[str, str], bool, Optional[str]]:
    """Returns ({brew_name: status}, homebrew_available, warning_message)."""
    if not shutil.which("brew"):
        return {}, False, "Homebrew is not installed or not on PATH"
    try:
        result = subprocess.run(
            ["brew", "services", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            if len(detail) > 140:
                detail = detail[:137] + "..."
            return {}, False, detail or "brew services list failed"
        out = result.stdout
        result = {}
        for line in out.splitlines()[1:]:  # skip header
            parts = line.split()
            if parts:
                result[parts[0]] = parts[1] if len(parts) > 1 else "none"
        return result, True, None
    except Exception as exc:
        return {}, False, str(exc)


def _get_launch_agents() -> dict[str, str]:
    """Returns {label: plist_path} for all user LaunchAgents."""
    agents = {}
    la_dir = Path.home() / "Library/LaunchAgents"
    try:
        for plist in la_dir.glob("*.plist"):
            label = plist.stem
            agents[label] = str(plist)
    except Exception:
        pass
    return agents


def _get_services() -> list[dict[str, Any]]:
    services: list[dict[str, Any]] = []
    matched_pids: set[int] = set()

    # Build a process lookup for fast matching
    all_procs = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "cpu_percent", "memory_info", "create_time"]):
        try:
            all_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def find_proc(patterns: list[str]):
        for proc in all_procs:
            try:
                if proc.pid in matched_pids:
                    continue
                cmdline = " ".join(proc.info["cmdline"] or [])
                pname = proc.info["name"] or ""
                if any(p in cmdline or p in pname for p in patterns):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return None

    # 1. Homebrew services — full list including stopped
    brew_all, brew_available, brew_warning = _get_brew_services()
    if not brew_available:
        services.append({
            "name": "Homebrew unavailable", "type": "warning", "pid": None,
            "running": False, "cpu_percent": 0.0, "memory_mb": 0.0,
            "uptime_minutes": None, "is_self": False,
            "detail": brew_warning or "brew services could not be queried",
        })
    _BREW_DISPLAY = {
        "mongodb-community": "MongoDB",
        "postgresql@15": "PostgreSQL",
        "postgresql@16": "PostgreSQL",
        "redis": "Redis",
        "dolt": "Dolt",
        "php": "PHP",
        "openvpn": "OpenVPN",
        "unbound": "Unbound",
        "nginx": "Nginx",
        "mysql": "MySQL",
    }
    _BREW_PROC_PATTERNS = {
        "mongodb-community": ["mongod"],
        "postgresql@15": ["postgres"],
        "postgresql@16": ["postgres"],
        "redis": ["redis-server"],
        "nginx": ["nginx"],
        "mysql": ["mysqld"],
        "php": ["php-fpm"],
    }
    seen_display_names: set[str] = set()
    for brew_name, status in brew_all.items():
        display = _BREW_DISPLAY.get(brew_name, brew_name)
        if display in seen_display_names:
            continue
        seen_display_names.add(display)
        running = status == "started"
        proc = find_proc(_BREW_PROC_PATTERNS.get(brew_name, [brew_name])) if running else None
        if proc:
            matched_pids.add(proc.pid)
            cpu = proc.info["cpu_percent"] or 0.0
            mem_mb = round((proc.info["memory_info"].rss if proc.info["memory_info"] else 0) / 1e6, 1)
            uptime = round((time.time() - proc.info["create_time"]) / 60)
        else:
            cpu, mem_mb, uptime = 0.0, 0.0, None
        services.append({
            "name": display, "type": "homebrew", "brew_name": brew_name,
            "pid": proc.pid if proc else None,
            "running": running, "cpu_percent": round(cpu, 1),
            "memory_mb": mem_mb, "uptime_minutes": uptime, "is_self": False,
        })

    # 2. LaunchAgents — user-installed background agents
    _AGENT_DISPLAY = {
        "com.openai.atlas.update-helper": ("OpenAI Atlas", ["atlas"]),
    }
    launch_agents = _get_launch_agents()
    for label, plist_path in launch_agents.items():
        if label.startswith("homebrew."):
            continue  # already covered by brew services
        display, patterns = _AGENT_DISPLAY.get(label, (label.split(".")[-1], [label.split(".")[-1]]))
        proc = find_proc(patterns)
        running = proc is not None
        if proc:
            matched_pids.add(proc.pid)
            cpu = proc.info["cpu_percent"] or 0.0
            mem_mb = round((proc.info["memory_info"].rss if proc.info["memory_info"] else 0) / 1e6, 1)
            uptime = round((time.time() - proc.info["create_time"]) / 60)
        else:
            cpu, mem_mb, uptime = 0.0, 0.0, None
        services.append({
            "name": display, "type": "agent", "plist": plist_path, "label": label,
            "pid": proc.pid if proc else None,
            "running": running, "cpu_percent": round(cpu, 1),
            "memory_mb": mem_mb, "uptime_minutes": uptime, "is_self": False,
        })

    # 3. macmon self-detection
    macmon_proc = find_proc(["uvicorn macmon.server"])
    if macmon_proc:
        matched_pids.add(macmon_proc.pid)
        cpu = macmon_proc.info["cpu_percent"] or 0.0
        mem_mb = round((macmon_proc.info["memory_info"].rss if macmon_proc.info["memory_info"] else 0) / 1e6, 1)
        uptime = round((time.time() - macmon_proc.info["create_time"]) / 60)
        services.append({
            "name": "macmon", "type": "self", "pid": macmon_proc.pid,
            "running": True, "cpu_percent": round(cpu, 1),
            "memory_mb": mem_mb, "uptime_minutes": uptime, "is_self": True,
        })
    elif "macmon" in _seen_service_names:
        services.append({
            "name": "macmon", "type": "self", "pid": None,
            "running": False, "cpu_percent": 0.0, "memory_mb": 0.0,
            "uptime_minutes": None, "is_self": True,
        })

    # 4. MCP server auto-discovery — match actual worker processes (not npm exec wrappers)
    def _mcp_name(cmdline: str, parts: list[str]) -> str:
        # Try to extract project-ref for disambiguation
        project_ref = None
        for i, part in enumerate(parts):
            if part == "--project-ref" and i + 1 < len(parts):
                project_ref = parts[i + 1][:8]  # first 8 chars of ref
                break
        for part in parts:
            if "/.bin/mcp-" in part or "/mcp-server-" in part:
                base = part.rsplit("/", 1)[-1]
                for prefix in ("mcp-server-", "mcp-"):
                    if base.startswith(prefix):
                        base = base[len(prefix):]
                        break
                label = "MCP " + base.replace("-", " ").title()
                if project_ref:
                    label += f" ({project_ref})"
                return label
        return "MCP server"

    for proc in all_procs:
        try:
            if proc.pid in matched_pids:
                continue
            cmd_parts = proc.info["cmdline"] or []
            cmdline = " ".join(cmd_parts)
            pname = proc.info["name"] or ""
            # Skip npm exec wrappers — only match the actual node worker
            if "npm" in pname or cmdline.startswith("npm "):
                continue
            is_mcp = (
                "/.bin/mcp-" in cmdline
                or "/mcp-server-" in cmdline
                or "mcp-server-" in pname
            )
            if not is_mcp:
                continue
            matched_pids.add(proc.pid)
            name = _mcp_name(cmdline, cmd_parts)
            cpu = proc.info["cpu_percent"] or 0.0
            mem_mb = round((proc.info["memory_info"].rss if proc.info["memory_info"] else 0) / 1e6, 1)
            uptime = round((time.time() - proc.info["create_time"]) / 60)
            services.append({
                "name": name, "type": "mcp-claude", "pid": proc.pid,
                "running": True, "cpu_percent": round(cpu, 1),
                "memory_mb": mem_mb, "uptime_minutes": uptime, "is_self": False,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # 5. Node/Bun/Deno dev server auto-discovery
    # Only match intentional dev servers — exclude Electron helpers and npx cache runners
    _NODE_DEV_SIGNALS = (
        "npm start", "npm run", "ng serve", "next dev", "next start",
        "vite", "nest start", "ts-node", "nodemon", "tsx watch", "tsx ",
    )
    _NVM_CACHE_MARKER = "/.npm/_npx/"  # npm exec cache path — these are MCP/tool wrappers, not app servers

    def _node_display_name(proc) -> str:
        cmdline = " ".join(proc.info["cmdline"] or [])
        try:
            cwd = proc.cwd()
            pkg = Path(cwd) / "package.json"
            if pkg.exists():
                data = json.loads(pkg.read_text())
                if data.get("name"):
                    return data["name"]
        except Exception:
            pass
        # Fallback: last meaningful arg
        parts = (proc.info["cmdline"] or [])
        for part in reversed(parts):
            if part.endswith(".js") or part.endswith(".ts"):
                return Path(part).stem
        return proc.info["name"] or "node"

    for proc in all_procs:
        try:
            if proc.pid in matched_pids:
                continue
            pname = proc.info["name"] or ""
            if pname not in ("node", "bun", "deno"):
                continue
            cmdline = " ".join(proc.info["cmdline"] or [])
            # Skip npx cache runners (MCP wrappers, one-off tools)
            if _NVM_CACHE_MARKER in cmdline:
                continue
            # Require a known dev server signal in the cmdline
            if not any(sig in cmdline for sig in _NODE_DEV_SIGNALS):
                continue
            # Skip if parent process is already a matched dev server (e.g. ng serve child of npm start)
            try:
                ppid = proc.ppid()
                if ppid in matched_pids:
                    continue
            except Exception:
                pass
            matched_pids.add(proc.pid)
            name = _node_display_name(proc)
            cpu = proc.info["cpu_percent"] or 0.0
            mem_mb = round((proc.info["memory_info"].rss if proc.info["memory_info"] else 0) / 1e6, 1)
            uptime = round((time.time() - proc.info["create_time"]) / 60)
            services.append({
                "name": name, "type": "node", "pid": proc.pid,
                "running": True, "cpu_percent": round(cpu, 1),
                "memory_mb": mem_mb, "uptime_minutes": uptime, "is_self": False,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # 6. Python server auto-discovery (uvicorn/gunicorn/flask/django)
    _PYTHON_SERVER_SIGNALS = ("uvicorn ", "gunicorn ", "flask run", "manage.py runserver")

    def _python_display_name(cmdline: str) -> str:
        parts = cmdline.split()
        for i, part in enumerate(parts):
            if part in ("uvicorn", "gunicorn") and i + 1 < len(parts):
                app_arg = parts[i + 1]
                # e.g. "macmon.server:app" → "macmon"
                module = app_arg.split(":")[0].split(".")[0]
                if module and not module.startswith("-"):
                    return module
        return "python server"

    for proc in all_procs:
        try:
            if proc.pid in matched_pids:
                continue
            cmdline = " ".join(proc.info["cmdline"] or [])
            is_py_server = any(sig in cmdline for sig in _PYTHON_SERVER_SIGNALS)
            if not is_py_server:
                continue
            matched_pids.add(proc.pid)
            name = _python_display_name(cmdline)
            cpu = proc.info["cpu_percent"] or 0.0
            mem_mb = round((proc.info["memory_info"].rss if proc.info["memory_info"] else 0) / 1e6, 1)
            uptime = round((time.time() - proc.info["create_time"]) / 60)
            services.append({
                "name": name, "type": "python", "pid": proc.pid,
                "running": True, "cpu_percent": round(cpu, 1),
                "memory_mb": mem_mb, "uptime_minutes": uptime, "is_self": False,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Update persistent known services
    new_names = {s["name"] for s in services if s["running"]}
    if new_names - _seen_service_names:
        _seen_service_names.update(new_names)
        _save_known_services(_seen_service_names)
    else:
        _seen_service_names.update(new_names)

    return services


def _get_top_processes() -> list[dict[str, Any]]:
    procs = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status", "create_time"]):
        try:
            mem_mb = round((proc.info["memory_info"].rss if proc.info["memory_info"] else 0) / 1e6, 1)
            if mem_mb < 10:
                continue
            procs.append({
                "pid": proc.pid,
                "name": proc.info["name"] or "unknown",
                "cpu_percent": round(proc.info["cpu_percent"] or 0.0, 1),
                "memory_mb": mem_mb,
                "status": proc.info["status"] or "unknown",
                "started": datetime.fromtimestamp(proc.info["create_time"], tz=timezone.utc).isoformat() if proc.info["create_time"] else None,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x["memory_mb"], reverse=True)
    return procs[:10]


def _get_status(memory: dict, swap: dict, cpu: dict) -> tuple[str, str]:
    """Returns (status, primary_reason)"""
    if swap["percent"] > 50 or memory["free_gb"] < 0.5:
        if swap["percent"] > 50:
            return "critical", f"Swap {swap['percent']}% full — system is compressing memory heavily"
        return "critical", f"Only {memory['free_gb']} GB RAM free — system is under severe memory pressure"
    if swap["percent"] > 20 or memory["percent"] > 75 or (len(_cpu_history) >= 5 and sum(_cpu_history[-5:]) / 5 > 80):
        if swap["percent"] > 20:
            return "warning", f"Swap {swap['percent']}% used — memory pressure building"
        if memory["percent"] > 75:
            return "warning", f"Memory {memory['percent']}% used — getting low"
        return "warning", "Sustained high CPU load detected"
    return "normal", ""


def _get_recommendations(memory: dict, swap: dict, services: list, processes: list) -> list[dict[str, Any]]:
    recs = []
    swap_pct = swap["percent"]
    free_gb = memory["free_gb"]

    # Swap pressure — purge only helps if swap < 30% (inactive file pages).
    # Above that, real app memory is the culprit — stop services instead.
    if 5 < swap_pct <= 30:
        recs.append({
            "id": "purge_inactive",
            "priority": "high",
            "title": "Purge inactive memory",
            "description": f"Swap at {swap_pct}% — purging inactive file pages can free RAM immediately",
            "action": "purge_memory",
            "target": None,
        })
    elif swap_pct > 30:
        # Swap this high = real app memory pressure. Identify top memory consumers.
        top = sorted(processes, key=lambda p: p["memory_mb"], reverse=True)[:3]
        top_names = ", ".join(p["name"] for p in top)
        recs.append({
            "id": "swap_pressure",
            "priority": "high",
            "title": "High swap — stop background services",
            "description": f"Swap at {swap_pct}% is caused by running apps. Stop unused services below to free RAM. Top consumers: {top_names}.",
            "action": "none",
            "target": None,
        })

    # Stoppable dev services — these directly free RAM
    for svc in services:
        if not svc["running"]:
            continue
        uptime = svc.get("uptime_minutes") or 0
        mem = svc["memory_mb"]
        svc_type = svc.get("type", "")
        if svc_type == "homebrew" and mem > 5:
            priority = "high" if swap_pct > 30 else "medium"
            recs.append({
                "id": f"stop_{svc['name'].lower().replace(' ', '_')}",
                "priority": priority,
                "title": f"Stop {svc['name']}",
                "description": f"Consuming {mem} MB — stop if not actively developing to free RAM and reduce swap",
                "action": "stop_service",
                "target": svc["name"],
            })
        if svc_type in ("node", "python") and uptime > 60 and mem > 30:
            recs.append({
                "id": f"stop_{svc['name'].lower().replace(' ', '_')}_{svc.get('pid', '')}",
                "priority": "high" if swap_pct > 30 else "medium",
                "title": f"Stop {svc['name']}",
                "description": f"Running for {uptime}m consuming {mem} MB — stop if not actively developing",
                "action": "stop_pid",
                "target": svc.get("pid"),
            })

    # Chrome
    chrome_procs = [p for p in processes if "Chrome" in p["name"] or "chrome" in p["name"].lower()]
    chrome_total = sum(p["memory_mb"] for p in chrome_procs)
    if chrome_total > 300:
        recs.append({
            "id": "reduce_chrome",
            "priority": "high" if swap_pct > 30 else "medium",
            "title": "Reduce Chrome tabs",
            "description": f"Chrome using {round(chrome_total)} MB across {len(chrome_procs)} processes — closing tabs directly frees RAM and reduces swap",
            "action": "none",
            "target": None,
        })

    # MCP servers
    mcp_services = [s for s in services if s["type"] == "mcp-claude" and s["running"]]
    mcp_total = sum(s["memory_mb"] for s in mcp_services)
    if mcp_total > 50:
        recs.append({
            "id": "stop_mcp",
            "priority": "low",
            "title": "Stop MCP servers",
            "description": f"{len(mcp_services)} MCP servers using {round(mcp_total)} MB — stop if not actively using these tools to free RAM",
            "action": "none",
            "target": None,
        })

    priority_order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda r: priority_order.get(r["priority"], 9))
    return recs


def collect() -> dict[str, Any]:
    cpu = _get_cpu()
    memory = _get_memory()
    swap = _get_swap()
    disk = _get_disk()
    services = _get_services()
    processes = _get_top_processes()
    status, reason = _get_status(memory, swap, cpu)
    recommendations = _get_recommendations(memory, swap, services, processes)

    return {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "status": status,
        "status_reason": reason,
        "cpu": cpu,
        "memory": memory,
        "swap": swap,
        "disk": disk,
        "processes": processes,
        "services": services,
        "recommendations": recommendations,
    }


def should_notify(status: str) -> bool:
    global _last_slow_notification
    if status == "normal":
        return False
    now = time.time()
    if now - _last_slow_notification > NOTIFICATION_COOLDOWN:
        _last_slow_notification = now
        return True
    return False
