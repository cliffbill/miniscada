"""Una sola conexión Modbus TCP. Si el PLC no contesta, conserva el último valor."""

from __future__ import annotations

import inspect
import logging
import threading
from datetime import datetime
from typing import Callable

from pymodbus.client import ModbusTcpClient

from app.decode import decode_u16, decode_u32

log = logging.getLogger("miniscada.poller")

WIDTHS = {"uint16": 1, "uint32": 2}
RAW_KEYS = ("total", "cajas_min", "paros_min", "paros_veces", "minutos_turno")


def empty_raw() -> dict:
    raw = {
        "plc_online": False,
        "has_data": False,
        "timestamp": None,
    }
    for key in RAW_KEYS:
        raw[key] = None
    return raw


def decode_block(registers: list[int], start: int, variables: list[dict], word_order: str) -> dict:
    by_address = {start + index: value & 0xFFFF for index, value in enumerate(registers)}
    values: dict = {}
    for item in variables:
        address = item["address"]
        kind = item["type"]
        if kind == "uint16":
            values[item["id"]] = decode_u16(by_address[address])
        elif kind == "uint32":
            values[item["id"]] = decode_u32(by_address[address], by_address[address + 1], word_order)
        else:
            raise ValueError(f"Tipo no soportado: {kind}")
    missing = [key for key in RAW_KEYS if key not in values]
    if missing:
        raise ValueError(f"La lectura no trajo: {', '.join(missing)}")
    return {key: values[key] for key in RAW_KEYS}


def register_span(variables: list[dict]) -> tuple[int, int]:
    start = min(item["address"] for item in variables)
    end = max(item["address"] + WIDTHS[item["type"]] for item in variables)
    return start, end - start


class Poller:
    def __init__(self, cfg: dict, on_update: Callable[[dict], None], demo_enabled: Callable[[], bool] | None = None):
        plc = cfg["plc"]
        self.host = plc["host"]
        self.port = int(plc["port"])
        self.unit_id = int(plc["unit_id"])
        self.poll_s = max(int(plc["poll_ms"]), 100) / 1000
        self.word_order = plc["word_order"]
        self.variables = cfg["variables"]
        self.on_update = on_update
        self._demo_enabled = demo_enabled or (lambda: False)
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._lock = threading.Lock()
        self._raw = empty_raw()

    def snapshot_raw(self) -> dict:
        with self._lock:
            return dict(self._raw)

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()

    def wake(self) -> None:
        self._wake.set()

    def show_demo(self) -> dict:
        raw = demo_raw()
        with self._lock:
            self._raw = raw
        self.on_update(dict(raw))
        self._wake.set()
        return dict(raw)

    def clear_demo(self) -> dict:
        with self._lock:
            self._raw = empty_raw()
            self._raw["timestamp"] = _now()
            raw = dict(self._raw)
        self.on_update(raw)
        self._wake.set()
        return raw

    def run(self) -> None:
        backoff = 1.0
        client: ModbusTcpClient | None = None
        was_online = False
        was_demo = False
        while not self._stop.is_set():
            if self._demo_enabled():
                if client is not None:
                    client.close()
                    client = None
                if not was_demo:
                    log.info("Simulación activa, sin leer el PLC")
                was_demo = True
                was_online = False
                raw = demo_raw()
                with self._lock:
                    self._raw = raw
                self.on_update(dict(raw))
                self._wait(self.poll_s)
                continue
            if was_demo:
                log.info("Simulación apagada")
                was_demo = False
            try:
                if client is None:
                    client = ModbusTcpClient(self.host, port=self.port, timeout=2, retries=1)
                    if not client.connect():
                        raise ConnectionError(f"sin conexión a {self.host}:{self.port}")
                start, count = register_span(self.variables)
                registers = _read_range(client, start, count, self.unit_id)
                values = decode_block(registers, start, self.variables, self.word_order)
                raw = {
                    "plc_online": True,
                    "has_data": True,
                    "timestamp": _now(),
                    **values,
                }
                with self._lock:
                    self._raw = raw
                if not was_online:
                    log.info("PLC en línea %s:%s", self.host, self.port)
                was_online = True
                backoff = 1.0
                self.on_update(dict(raw))
                self._wait(self.poll_s)
            except Exception as exc:
                if self._demo_enabled():
                    continue
                if was_online:
                    log.warning("PLC no responde: %s", exc)
                else:
                    log.info("Reintento PLC fallido: %s", exc)
                was_online = False
                raw = self._mark_offline()
                self.on_update(raw)
                if client is not None:
                    client.close()
                    client = None
                self._wait(backoff)
                backoff = min(backoff * 2, 10.0)

    def _wait(self, seconds: float) -> None:
        self._wake.wait(seconds)
        self._wake.clear()

    def _mark_offline(self) -> dict:
        with self._lock:
            self._raw["plc_online"] = False
            self._raw["timestamp"] = _now()
            return dict(self._raw)


def demo_raw() -> dict:
    # 16935 cajas en 242 minutos dan promedio 70, el número de la foto.
    return {
        "plc_online": True,
        "has_data": True,
        "timestamp": _now(),
        "total": 16935,
        "cajas_min": 170,
        "paros_min": 98,
        "paros_veces": 59,
        "minutos_turno": 242,
    }


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_range(client: ModbusTcpClient, start: int, count: int, unit_id: int) -> list[int]:
    registers: list[int] = []
    offset = 0
    while offset < count:
        chunk = min(120, count - offset)
        response = _read_holding(client, start + offset, chunk, unit_id)
        if response is None or response.isError():
            raise ConnectionError(f"el PLC rechazó la lectura en %MW{start + offset}")
        piece = list(response.registers)
        if len(piece) < chunk:
            raise ConnectionError("respuesta Modbus incompleta")
        registers.extend(piece)
        offset += chunk
    return registers


def _read_holding(client: ModbusTcpClient, address: int, count: int, unit_id: int):
    parameters = inspect.signature(client.read_holding_registers).parameters
    kwargs = {"address": address, "count": count}
    if "device_id" in parameters:
        kwargs["device_id"] = unit_id
    elif "slave" in parameters:
        kwargs["slave"] = unit_id
    return client.read_holding_registers(**kwargs)
