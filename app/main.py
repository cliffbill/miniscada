"""Servidor de la pantalla Andon. Solo lee el PLC."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config_store import ConfigStore
from app.poller import Poller
from app.snapshot import build_snapshot

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
STATIC = ROOT / "static" / "index.html"
LOG_DIR = ROOT / "logs"

log = logging.getLogger("miniscada")


class SettingsIn(BaseModel):
    green_at: int
    red_below: int
    stop_gap_seconds: int
    demo: bool = False
    show_promedio: bool = False


class Hub:
    def __init__(self) -> None:
        self.clients: set[WebSocket] = set()
        self.loop: asyncio.AbstractEventLoop | None = None

    async def broadcast(self, payload: dict) -> None:
        message = json.dumps(payload)
        dead: list[WebSocket] = []
        for socket in list(self.clients):
            try:
                await socket.send_text(message)
            except Exception:
                dead.append(socket)
        for socket in dead:
            self.clients.discard(socket)


def setup_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = RotatingFileHandler(
        LOG_DIR / "miniscada.log",
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    log.setLevel(logging.INFO)
    if not log.handlers:
        log.addHandler(file_handler)
        log.addHandler(stream)


store = ConfigStore(CONFIG_PATH)
hub = Hub()
poller: Poller


def publish(raw: dict) -> None:
    payload = build_snapshot(raw, store.get())
    loop = hub.loop
    if loop is not None and loop.is_running():
        asyncio.run_coroutine_threadsafe(hub.broadcast(payload), loop)


poller = Poller(store.get(), publish, demo_enabled=lambda: bool(store.get().get("demo", False)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    hub.loop = asyncio.get_running_loop()
    server = store.get()["server"]
    log.info("Pantalla en http://%s:%s", server["host"], server["port"])
    thread = threading.Thread(target=poller.run, name="modbus-poller", daemon=True)
    thread.start()
    yield
    poller.stop()
    thread.join(timeout=3)


app = FastAPI(title="MiniScada", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/snapshot")
def snapshot() -> dict:
    return build_snapshot(poller.snapshot_raw(), store.get())


@app.post("/api/settings")
async def save_settings(body: SettingsIn) -> dict:
    if not 0 <= body.green_at <= 100000 or not 0 <= body.red_below <= 100000:
        raise HTTPException(status_code=400, detail="Los umbrales tienen que estar entre 0 y 100000.")
    if body.green_at <= body.red_below:
        raise HTTPException(status_code=400, detail="El verde tiene que ser mayor que el rojo.")
    if not 1 <= body.stop_gap_seconds <= 3600:
        raise HTTPException(status_code=400, detail="Los segundos sin pulso tienen que estar entre 1 y 3600.")
    was_demo = bool(store.get().get("demo", False))
    store.update_settings(
        body.green_at,
        body.red_below,
        body.stop_gap_seconds,
        body.demo,
        body.show_promedio,
    )
    log.info(
        "Ajustes guardados: verde %s, rojo %s, segundos sin pulso %s, simulación %s, promedio %s",
        body.green_at,
        body.red_below,
        body.stop_gap_seconds,
        body.demo,
        body.show_promedio,
    )
    if body.demo:
        poller.show_demo()
    elif was_demo:
        poller.clear_demo()
    payload = build_snapshot(poller.snapshot_raw(), store.get())
    await hub.broadcast(payload)
    return payload


@app.websocket("/ws")
async def websocket_endpoint(socket: WebSocket) -> None:
    await socket.accept()
    hub.clients.add(socket)
    try:
        await socket.send_text(json.dumps(build_snapshot(poller.snapshot_raw(), store.get())))
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        hub.clients.discard(socket)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC, headers={"Cache-Control": "no-cache"})
