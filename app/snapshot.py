"""Arma el JSON que ven la pantalla y el WebSocket."""

from __future__ import annotations

from app.logic import rate_color


def build_snapshot(raw: dict, cfg: dict) -> dict:
    green_at = cfg["thresholds"]["green_at"]
    red_below = cfg["thresholds"]["red_below"]
    has_data = bool(raw.get("has_data"))
    online = bool(raw.get("plc_online"))
    cajas = raw.get("cajas") if has_data else None
    gpm = raw.get("gpm") if has_data else None
    paros = raw.get("paros") if has_data else None
    tiempo_paro = raw.get("tiempo_paro") if has_data else None
    machine = raw.get("machine_on") if has_data else None
    return {
        "timestamp": raw.get("timestamp"),
        "plc_online": online,
        "quality": "ok" if online else "stale",
        "has_data": has_data,
        "cajas": cajas,
        "gpm": gpm,
        "paros": paros,
        "tiempo_paro": tiempo_paro,
        "machine_on": None if machine is None else bool(machine),
        "rate_color": rate_color(gpm, online, green_at, red_below),
        "thresholds": {"green_at": green_at, "red_below": red_below},
        "stop_gap_seconds": cfg["plc"]["stop_gap_seconds"],
        "demo": bool(cfg.get("demo", False)),
    }
