"""Arma el JSON que ven la pantalla y el WebSocket."""

from __future__ import annotations

from app.logic import promedio, promedio_color, rate_color


def build_snapshot(raw: dict, cfg: dict) -> dict:
    green_at = cfg["thresholds"]["green_at"]
    red_below = cfg["thresholds"]["red_below"]
    has_data = bool(raw.get("has_data"))
    online = bool(raw.get("plc_online"))
    total = raw.get("total") if has_data else None
    minutos = raw.get("minutos_turno") if has_data else None
    value = promedio(total, minutos) if has_data else None
    cajas = raw.get("cajas_min") if has_data else None
    return {
        "timestamp": raw.get("timestamp"),
        "plc_online": online,
        "quality": "ok" if online else "stale",
        "has_data": has_data,
        "cajas_min": cajas,
        "paros_min": raw.get("paros_min") if has_data else None,
        "paros_veces": raw.get("paros_veces") if has_data else None,
        "total": total,
        "minutos_turno": minutos,
        "promedio": value,
        "promedio_color": promedio_color(value, minutos, online, green_at, red_below),
        "rate_color": rate_color(cajas, online, green_at, red_below),
        "show_promedio": bool(cfg.get("show_promedio", False)),
        "thresholds": {"green_at": green_at, "red_below": red_below},
        "stop_gap_seconds": cfg["plc"]["stop_gap_seconds"],
        "demo": bool(cfg.get("demo", False)),
    }
