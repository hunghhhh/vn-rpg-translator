"""Extractor package — factory function"""

from translator.extractor.mv_extractor import MVExtractor
from translator.extractor.vxa_extractor import VXAExtractor


def get_extractor(engine: str, game_dir: str, output_dir: str):
    engine = engine.lower()
    if engine in ("mv", "mz"):
        return MVExtractor(game_dir, output_dir)
    elif engine == "vxa":
        return VXAExtractor(game_dir, output_dir)
    else:
        raise ValueError(f"Engine không hỗ trợ: {engine}")
