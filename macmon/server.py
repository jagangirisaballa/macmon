import asyncio
import json
import os
import secrets
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional, Set
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import metrics, notifications, actions

app = FastAPI(title="macmon", version="1.1.4")

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_clients: Set[WebSocket] = set()
SESSION_TOKEN = os.environ.get("MACMON_SESSION_TOKEN") or secrets.token_urlsafe(32)


def _normalize_host(host: Optional[str]) -> str:
    if not host:
        return ""
    host = host.strip()
    if host.startswith("[") and "]" in host:
        return host[1 : host.index("]")]
    return host.split(":", 1)[0].lower()


def _is_loopback_host(host: str) -> bool:
    return host in {"127.0.0.1", "::1", "localhost"}


def _validate_origin(origin: Optional[str], host: Optional[str]) -> bool:
    host_name = _normalize_host(host)
    if not _is_loopback_host(host_name):
        return False
    if not origin:
        return True
    parsed = urlparse(origin)
    origin_host = _normalize_host(parsed.netloc)
    return _is_loopback_host(origin_host)


def _require_session_token(token: Optional[str]) -> None:
    if not token or not secrets.compare_digest(token, SESSION_TOKEN):
        raise HTTPException(status_code=403, detail="Invalid macmon session token")


def _guard_mutation(request: Request) -> None:
    if not _validate_origin(request.headers.get("origin"), request.headers.get("host")):
        raise HTTPException(status_code=403, detail="Rejected non-local request")
    _require_session_token(request.headers.get("x-macmon-token"))


@app.get("/", response_class=HTMLResponse)
async def index():
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        html = html_file.read_text()
        return HTMLResponse(content=html.replace('"__MACMON_TOKEN__"', json.dumps(SESSION_TOKEN)))
    return HTMLResponse("<h1>macmon</h1><p>Static files not found.</p>")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    if not _validate_origin(ws.headers.get("origin"), ws.headers.get("host")):
        await ws.close(code=1008, reason="Rejected non-local websocket origin")
        return
    try:
        _require_session_token(ws.query_params.get("token"))
    except HTTPException:
        await ws.close(code=1008, reason="Invalid macmon session token")
        return
    await ws.accept()
    _clients.add(ws)
    # Send first snapshot immediately so UI doesn't wait 2s
    try:
        data = metrics.collect()
        await ws.send_text(json.dumps(data))
    except Exception:
        pass
    try:
        while True:
            # Keep alive — receive with timeout, ignore content
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                pass
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        _clients.discard(ws)


@app.post("/api/service/{name}/stop")
async def api_stop_service(name: str, request: Request):
    _guard_mutation(request)
    result = actions.stop_service(name)
    return JSONResponse(result)


@app.post("/api/service/{name}/start")
async def api_start_service(name: str, request: Request):
    _guard_mutation(request)
    result = actions.start_service(name)
    return JSONResponse(result)


@app.post("/api/service/stop-pid/{pid}")
async def api_stop_pid(pid: int, request: Request):
    _guard_mutation(request)
    result = actions.stop_pid(pid)
    return JSONResponse(result)


@app.post("/api/process/{pid}/kill")
async def api_kill_process(pid: int, request: Request):
    _guard_mutation(request)
    result = actions.kill_process(pid)
    return JSONResponse(result)


@app.post("/api/action/{action_id}")
async def api_execute_action(action_id: str, request: Request):
    _guard_mutation(request)
    if action_id == "purge_memory":
        result = actions.purge_memory()
    else:
        raise HTTPException(status_code=404, detail=f"Unknown action: {action_id}")
    return JSONResponse(result)


@app.get("/api/snapshot")
async def api_snapshot():
    data = metrics.collect()
    return JSONResponse(data)


def _spawn_server(port: int):
    """Spawn a new detached uvicorn process and write its PID to the pidfile."""
    from pathlib import Path as _Path
    logfile = _Path.home() / ".macmon.log"
    pidfile = _Path.home() / ".macmon.pid"
    env = os.environ.copy()
    env["MACMON_SESSION_TOKEN"] = SESSION_TOKEN
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "macmon.server:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        stdout=open(logfile, "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
        cwd=str(_Path(__file__).parent.parent),
        env=env,
    )
    pidfile.write_text(str(proc.pid))
    return proc.pid


@app.post("/api/restart")
async def api_restart(request: Request, port: int = 9999):
    _guard_mutation(request)
    new_pid = _spawn_server(port)
    asyncio.get_event_loop().call_later(0.5, lambda: os.kill(os.getpid(), signal.SIGTERM))
    return JSONResponse({"success": True, "message": "Server restarting", "new_pid": new_pid})


@app.post("/api/shutdown")
async def api_shutdown(request: Request):
    _guard_mutation(request)
    asyncio.get_event_loop().call_later(0.3, lambda: os.kill(os.getpid(), signal.SIGTERM))
    return JSONResponse({"success": True, "message": "macmon stopped"})


async def broadcast_loop():
    while True:
        try:
            data = metrics.collect()
            if metrics.should_notify(data["status"]):
                notifications.notify_slow(data["status"], data["status_reason"])

            if _clients:
                payload = json.dumps(data)
                dead = set()
                for ws in list(_clients):
                    try:
                        await ws.send_text(payload)
                    except Exception:
                        dead.add(ws)
                for ws in dead:
                    _clients.discard(ws)
        except Exception as e:
            print(f"[macmon] broadcast error: {e}")
        await asyncio.sleep(2)


@app.on_event("startup")
async def startup():
    asyncio.create_task(broadcast_loop())
