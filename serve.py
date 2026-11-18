"""Arranque del programa. PyInstaller usa este archivo como entrada."""

from __future__ import annotations

import multiprocessing


def main() -> None:
    multiprocessing.freeze_support()
    import uvicorn

    from app.main import app, store

    server = store.get()["server"]
    uvicorn.run(app, host=str(server["host"]), port=int(server["port"]))


if __name__ == "__main__":
    main()
