"""Rebuilder package — factory function"""

from translator.rebuilder.mv_rebuilder import MVRebuilder
from translator.rebuilder.vxa_rebuilder import VXARebuilder


def get_rebuilder(engine: str, game_dir: str):
    engine = engine.lower()
    if engine in ("mv", "mz"):
        return MVRebuilder(game_dir)
    elif engine == "vxa":
        return VXARebuilder(game_dir)
    else:
        raise ValueError(f"Engine không hỗ trợ: {engine}")
