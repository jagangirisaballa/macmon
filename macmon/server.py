import asyncio
import json
import os
from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import metrics, notifications, actions

app = FastAPI(title="macmon", version="1.0.0")

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_clients: Set[WebSocket] = set()


@app.get("/", response_class=HTMLResponse)
async def index():
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text())
    return HTMLResponse("<h1>macmon</h1><p>Static files not found.</p>")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
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
async def api_stop_service(name: str):
    result = actions.stop_service(name)
    return JSONResponse(result)


@app.post("/api/service/{name}/start")
async def api_start_service(name: str):
    result = actions.start_service(name)
    return JSONResponse(result)


@app.post("/api/process/{pid}/kill")
async def api_kill_process(pid: int):
    result = actions.kill_process(pid)
    return JSONResponse(result)


@app.post("/api/action/{action_id}")
async def api_execute_action(action_id: str):
    if action_id == "purge_memory":
        result = actions.purge_memory()
    else:
        raise HTTPException(status_code=404, detail=f"Unknown action: {action_id}")
    return JSONResponse(result)


@app.get("/api/snapshot")
async def api_snapshot():
    data = metrics.collect()
    return JSONResponse(data)


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
