"""Una sola conexión Modbus TCP. Si el PLC no contesta, conserva el último valor."""

from __future__ import annotations

import inspect
import logging
import math
import threading
import time
from datetime import datetime
from typing import Callable

from pymodbus.client import ModbusTcpClient

from app.decode import decode_f32, decode_i32, decode_u16, decode_u32

log = logging.getLogger("miniscada.poller")

WIDTHS = {"uint16": 1, "uint32": 2, "int32": 2, "float32": 2}
RAW_KEYS = ("cajas", "gpm", "paros", "tiempo_paro")


def empty_raw() -> dict:
    raw = {
        "plc_online": False,
        "has_data": False,
        "timestamp": None,
    }
    for key in RAW_KEYS:
        raw[key] = None
    raw["machine_on"] = None
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
        elif kind == "int32":
            values[item["id"]] = decode_i32(by_address[address], by_address[address + 1], word_order)
        elif kind == "float32":
            number = decode_f32(by_address[address], by_address[address + 1], word_order)
            values[item["id"]] = number if math.isfinite(number) else None
        else:
            raise ValueError(f"Tipo no soportado: {kind}")
    return values


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
        self.machine_address = int(cfg["machine"]["address"])
        self.on_update = on_update
        self._demo_enabled = demo_enabled or (lambda: False)
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._lock = threading.Lock()
        self._raw = empty_raw()
        self._write_pending = False
        self._write_address = 0
        self._write_done: threading.Event | None = None
        self._write_error: Exception | None = None

    def snapshot_raw(self) -> dict:
        with self._lock:
            return dict(self._raw)

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()

    def wake(self) -> None:
        self._wake.set()

    def pulse(self, address: int, timeout: float = 5.0) -> None:
        """Pulso corto: %M en 1 y enseguida en 0. No deja el bit activado."""
        if self._demo_enabled():
            raise RuntimeError("simulación")
        done = threading.Event()
        with self._lock:
            if self._write_pending:
                raise RuntimeError("ya hay una escritura en curso")
            self._write_done = done
            self._write_error = None
            self._write_address = int(address)
            self._write_pending = True
        self._wake.set()
        if not done.wait(timeout):
            with self._lock:
                self._write_pending = False
            raise TimeoutError("el PLC no confirmó el bit")
        with self._lock:
            error = self._write_error
        if error is not None:
            raise error

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
                self._finish_write(RuntimeError("simulación"))
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
                wrote = self._service_reset(client)
                start, count = register_span(self.variables)
                registers = _read_range(client, start, count, self.unit_id)
                decoded = decode_block(registers, start, self.variables, self.word_order)
                machine_on = _read_coil(client, self.machine_address, self.unit_id)
                raw = {
                    "plc_online": True,
                    "has_data": True,
                    "timestamp": _now(),
                    "machine_on": machine_on,
                    **{key: decoded.get(key) for key in RAW_KEYS},
                }
                with self._lock:
                    self._raw = raw
                if wrote:
                    self._finish_write(None)
                if not was_online:
                    log.info("PLC en línea %s:%s", self.host, self.port)
                was_online = True
                backoff = 1.0
                self.on_update(dict(raw))
                self._wait(self.poll_s)
            except Exception as exc:
                self._finish_write(exc)
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

    def _service_reset(self, client: ModbusTcpClient) -> bool:
        with self._lock:
            pending = self._write_pending
            address = self._write_address
        if not pending:
            return False
        try:
            _write_coil(client, address, True, self.unit_id)
            time.sleep(0.15)
            _write_coil(client, address, False, self.unit_id)
        except Exception as exc:
            self._finish_write(exc)
            return False
        log.info("Reset: pulso en %%M%s", address)
        return True

    def _finish_write(self, error: Exception | None) -> None:
        with self._lock:
            if not self._write_pending:
                return
            self._write_pending = False
            self._write_error = error
            done = self._write_done
        if done is not None:
            done.set()

    def _mark_offline(self) -> dict:
        with self._lock:
            self._raw["plc_online"] = False
            self._raw["timestamp"] = _now()
            return dict(self._raw)


def demo_raw() -> dict:
    return {
        "plc_online": True,
        "has_data": True,
        "timestamp": _now(),
        "cajas": 16935,
        "gpm": 170.0,
        "paros": 59,
        "tiempo_paro": 98,
        "machine_on": True,
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


def _read_coil(client: ModbusTcpClient, address: int, unit_id: int) -> bool:
    parameters = inspect.signature(client.read_coils).parameters
    kwargs = {"address": address, "count": 1}
    if "device_id" in parameters:
        kwargs["device_id"] = unit_id
    elif "slave" in parameters:
        kwargs["slave"] = unit_id
    response = client.read_coils(**kwargs)
    if response is None or response.isError() or not response.bits:
        raise ConnectionError(f"el PLC rechazó la lectura de %M{address}")
    return bool(response.bits[0])


def _write_coil(client: ModbusTcpClient, address: int, value: bool, unit_id: int) -> None:
    parameters = inspect.signature(client.write_coil).parameters
    kwargs = {"address": address, "value": value}
    if "device_id" in parameters:
        kwargs["device_id"] = unit_id
    elif "slave" in parameters:
        kwargs["slave"] = unit_id
    response = client.write_coil(**kwargs)
    if response is None or response.isError():
        raise ConnectionError(f"el PLC rechazó la escritura de %M{address}")


def _read_holding(client: ModbusTcpClient, address: int, count: int, unit_id: int):
    parameters = inspect.signature(client.read_holding_registers).parameters
    kwargs = {"address": address, "count": count}
    if "device_id" in parameters:
        kwargs["device_id"] = unit_id
    elif "slave" in parameters:
        kwargs["slave"] = unit_id
    return client.read_holding_registers(**kwargs)
