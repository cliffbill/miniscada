"""Decodificación de registros Modbus de 16 y 32 bits.

El orden de palabras no lo fija el protocolo. ABCD pone la palabra alta en la
dirección menor. CDAB pone la palabra baja en la dirección menor.
"""

from __future__ import annotations

import struct

WORD_ORDERS = ("ABCD", "CDAB")


def decode_u16(register: int) -> int:
    return register & 0xFFFF


def decode_u32(low_address: int, high_address: int, word_order: str) -> int:
    high, low = _words(low_address, high_address, word_order)
    return ((high & 0xFFFF) << 16) | (low & 0xFFFF)


def decode_f32(low_address: int, high_address: int, word_order: str) -> float:
    raw = decode_u32(low_address, high_address, word_order)
    return struct.unpack(">f", struct.pack(">I", raw))[0]


def _words(low_address: int, high_address: int, word_order: str) -> tuple[int, int]:
    if word_order == "ABCD":
        return low_address, high_address
    if word_order == "CDAB":
        return high_address, low_address
    raise ValueError(f"Orden de palabras no reconocido: {word_order}")


def self_check() -> list[str]:
    """25.0 es 0x41C80000. 16935 y 100000 cubren el total de cajas."""
    failures: list[str] = []
    float_cases = {
        "ABCD": (0x41C8, 0x0000),
        "CDAB": (0x0000, 0x41C8),
    }
    for order, (first, second) in float_cases.items():
        value = decode_f32(first, second, order)
        if abs(value - 25.0) > 0.0001:
            failures.append(f"float 25.0 {order} dio {value}")

    uint_cases = {
        16935: {"ABCD": (0x0000, 0x4227), "CDAB": (0x4227, 0x0000)},
        100000: {"ABCD": (0x0001, 0x86A0), "CDAB": (0x86A0, 0x0001)},
    }
    for expected, orders in uint_cases.items():
        for order, (first, second) in orders.items():
            value = decode_u32(first, second, order)
            if value != expected:
                failures.append(f"uint32 {expected} {order} dio {value}")
    return failures
