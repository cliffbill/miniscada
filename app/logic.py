"""Promedio del turno y color del recuadro."""

from __future__ import annotations


def promedio(total: int | None, minutos: int | None) -> int | None:
    if total is None or minutos is None:
        return None
    if minutos <= 0:
        return 0
    return int(total / minutos + 0.5)


def rate_color(value: int | None, online: bool, green_at: int, red_below: int) -> str:
    if not online or value is None:
        return "neutral"
    if value >= green_at:
        return "green"
    if value < red_below:
        return "red"
    return "amber"


def promedio_color(
    value: int | None,
    minutos: int | None,
    online: bool,
    green_at: int,
    red_below: int,
) -> str:
    if not online or not minutos or value is None:
        return "neutral"
    if value >= green_at:
        return "green"
    if value < red_below:
        return "red"
    return "amber"


def self_check() -> list[str]:
    failures: list[str] = []
    if promedio(16935, 20) != 847:
        failures.append(f"promedio 16935/20 dio {promedio(16935, 20)}")
    if promedio(0, 0) != 0:
        failures.append("promedio con turno en cero debe ser 0")
    if promedio(None, None) is not None:
        failures.append("promedio sin datos debe ser vacío")

    checks = [
        (75, 20, True, "green"),
        (74, 20, True, "amber"),
        (60, 20, True, "amber"),
        (59, 20, True, "red"),
        (100, 0, True, "neutral"),
        (100, 20, False, "neutral"),
    ]
    for value, minutos, online, expected in checks:
        got = promedio_color(value, minutos, online, 75, 60)
        if got != expected:
            failures.append(f"color {value} min={minutos} online={online} dio {got}, esperaba {expected}")
    if rate_color(170, True, 75, 60) != "green":
        failures.append("cajas/min 170 debe quedar en verde")
    if rate_color(70, True, 75, 60) != "amber":
        failures.append("cajas/min 70 debe quedar en ámbar")
    if rate_color(170, False, 75, 60) != "neutral":
        failures.append("sin PLC el color de cajas/min queda neutro")
    return failures
