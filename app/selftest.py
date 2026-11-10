"""Pruebas sin PLC: orden de palabras, promedio y color."""

from __future__ import annotations

from app.decode import self_check as check_decode
from app.logic import self_check as check_logic
from app.poller import decode_block
from app.snapshot import build_snapshot


def check_block() -> list[str]:
    failures: list[str] = []
    variables = [
        {"id": "total", "address": 0, "type": "uint32"},
        {"id": "cajas_min", "address": 2, "type": "uint16"},
        {"id": "paros_min", "address": 4, "type": "uint16"},
        {"id": "paros_veces", "address": 6, "type": "uint16"},
        {"id": "minutos_turno", "address": 8, "type": "uint16"},
    ]
    # 16935 en CDAB: palabra baja 0x4227 en %MW0, palabra alta 0x0000 en %MW1.
    registers = [0x4227, 0x0000, 170, 0, 98, 0, 59, 0, 20]
    values = decode_block(registers, 0, variables, "CDAB")
    expected = {
        "total": 16935,
        "cajas_min": 170,
        "paros_min": 98,
        "paros_veces": 59,
        "minutos_turno": 20,
    }
    if values != expected:
        failures.append(f"bloque CDAB dio {values}")

    swapped = [0x0000, 0x4227, 170, 0, 98, 0, 59, 0, 20]
    abcd = decode_block(swapped, 0, variables, "ABCD")
    if abcd["total"] != 16935:
        failures.append(f"bloque ABCD dio total {abcd['total']}")

    cfg = {
        "thresholds": {"green_at": 75, "red_below": 60},
        "plc": {"stop_gap_seconds": 10},
    }
    raw = {"plc_online": True, "has_data": True, "timestamp": "t", **values}
    snap = build_snapshot(raw, cfg)
    if snap["promedio"] != 847 or snap["promedio_color"] != "green":
        failures.append(f"snapshot dio promedio {snap['promedio']} color {snap['promedio_color']}")

    offline = build_snapshot({**raw, "plc_online": False}, cfg)
    if offline["promedio_color"] != "neutral" or offline["quality"] != "stale":
        failures.append("al perder el PLC el promedio tiene que quedar neutro")

    cold = build_snapshot(
        {
            "plc_online": False,
            "has_data": False,
            "timestamp": None,
            "total": None,
            "cajas_min": None,
            "paros_min": None,
            "paros_veces": None,
            "minutos_turno": None,
        },
        cfg,
    )
    if cold["total"] is not None or cold["plc_online"]:
        failures.append("sin PLC la foto inicial no debe inventar números")
    return failures


def main() -> None:
    failures = check_decode() + check_logic() + check_block()
    if failures:
        for item in failures:
            print("FAIL", item)
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
