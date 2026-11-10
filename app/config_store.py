"""Lee y guarda config.json. Los umbrales se pueden cambiar con la pantalla abierta."""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from pathlib import Path

from app.decode import WORD_ORDERS

REQUIRED_IDS = ("total", "cajas_min", "paros_min", "paros_veces", "minutos_turno")
WIDTHS = {"uint16": 1, "uint32": 2}


class ConfigError(Exception):
    pass


class ConfigStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._data = _load(path)

    def get(self) -> dict:
        with self._lock:
            return deepcopy(self._data)

    def update_settings(
        self,
        green_at: int,
        red_below: int,
        stop_gap_seconds: int,
        demo: bool,
        show_promedio: bool,
    ) -> dict:
        with self._lock:
            self._data["thresholds"]["green_at"] = green_at
            self._data["thresholds"]["red_below"] = red_below
            self._data["plc"]["stop_gap_seconds"] = stop_gap_seconds
            self._data["demo"] = demo
            self._data["show_promedio"] = show_promedio
            _validate(self._data)
            text = json.dumps(self._data, indent=2, ensure_ascii=False) + "\n"
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(self.path)
            return deepcopy(self._data)


def _load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"No existe {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"config.json no es JSON válido: {exc}") from exc
    _validate(data)
    return data


def _validate(data: dict) -> None:
    try:
        order = data["plc"]["word_order"]
        gap = data["plc"]["stop_gap_seconds"]
        green = data["thresholds"]["green_at"]
        red = data["thresholds"]["red_below"]
        variables = data["variables"]
    except (KeyError, TypeError) as exc:
        raise ConfigError(f"config.json incompleto: {exc}") from exc
    if order not in WORD_ORDERS:
        raise ConfigError("plc.word_order tiene que ser ABCD o CDAB")
    if not isinstance(gap, int) or not 1 <= gap <= 3600:
        raise ConfigError("plc.stop_gap_seconds tiene que ser un entero de 1 a 3600")
    if not isinstance(green, int) or not isinstance(red, int):
        raise ConfigError("Los umbrales tienen que ser enteros")
    if green <= red:
        raise ConfigError("thresholds.green_at tiene que ser mayor que red_below")
    if "demo" in data and not isinstance(data["demo"], bool):
        raise ConfigError("demo tiene que ser true o false")
    if "show_promedio" in data and not isinstance(data["show_promedio"], bool):
        raise ConfigError("show_promedio tiene que ser true o false")
    ids = [item.get("id") for item in variables]
    missing = [name for name in REQUIRED_IDS if name not in ids]
    if missing:
        raise ConfigError(f"Faltan variables: {', '.join(missing)}")
    for item in variables:
        if item.get("type") not in WIDTHS:
            raise ConfigError(f"Tipo no soportado en {item.get('id')}")
        if not isinstance(item.get("address"), int) or item["address"] < 0:
            raise ConfigError(f"Dirección inválida en {item.get('id')}")
