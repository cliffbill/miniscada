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
    raw = {
        "plc_online": True,
        "has_data": True,
        "timestamp": "t",
        "cajas": 120,
        "gpm": 80.5,
        "paros": 4,
        "tiempo_paro": 45,
        "machine_on": True,
    }
    snap = build_snapshot(raw, cfg)
    if snap["cajas"] != 120 or snap["paros"] != 4 or snap["tiempo_paro"] != 45 or abs(snap["gpm"] - 80.5) > 0.001 or snap["machine_on"] is not True:
        failures.append(f"snapshot dio {snap}")
    if snap["rate_color"] != "green":
        failures.append(f"GPM 80.5 quedó {snap['rate_color']}")

    offline = build_snapshot({**raw, "plc_online": False}, cfg)
    if offline["rate_color"] != "neutral" or offline["quality"] != "stale" or offline["cajas"] != 120:
        failures.append("al perder el PLC las cajas se conservan y el color queda neutro")

    cold = build_snapshot(
        {
            "plc_online": False,
            "has_data": False,
            "timestamp": None,
            "cajas": None,
            "gpm": None,
            "paros": None,
            "tiempo_paro": None,
            "machine_on": None,
        },
        cfg,
    )
    if cold["cajas"] is not None or cold["gpm"] is not None or cold["paros"] is not None or cold["tiempo_paro"] is not None or cold["machine_on"] is not None or cold["plc_online"]:
        failures.append("sin PLC la foto inicial no debe inventar números")

    # %MDn y %MFn empiezan en %MWn. %MW28 paros, %MF128 GPM, %MD134 cajas, %MD138 tiempo en paro.
    configured = [
        {"id": "paros", "address": 28, "type": "uint16"},
        {"id": "gpm", "address": 128, "type": "float32"},
        {"id": "cajas", "address": 134, "type": "int32"},
        {"id": "tiempo_paro", "address": 138, "type": "int32"},
    ]
    block = [0] * 112
    block[0] = 4
    block[100] = 0x0000
    block[101] = 0x42C6
    block[106] = 99
    block[107] = 0
    block[110] = 45
    block[111] = 0
    live = decode_block(block, 28, configured, "CDAB")
    if live.get("paros") != 4 or live.get("cajas") != 99 or live.get("tiempo_paro") != 45 or abs(live.get("gpm", 0) - 99.0) > 0.0001:
        failures.append(f"mapa final dio {live}")
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
