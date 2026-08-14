"""Curated, offline city landmark presets bundled with RouteFilm."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import Image

LANDMARK_DIR = Path(__file__).with_name("data") / "landmarks"
CATALOG_PATH = LANDMARK_DIR / "catalog.json"


@lru_cache(maxsize=1)
def landmark_catalog() -> dict[str, dict[str, Any]]:
    if not CATALOG_PATH.is_file():
        return {}
    records = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {str(item["city"]): item for item in records}


def landmark_preset(city: str) -> dict[str, Any] | None:
    """Return metadata for an exact city-name match."""
    return landmark_catalog().get(city)


def builtin_landmark(city: str) -> Image.Image | None:
    """Load a bundled landmark without requiring an image-generation service."""
    preset = landmark_preset(city)
    if preset is None:
        return None
    path = LANDMARK_DIR / str(preset["asset"])
    if not path.is_file():
        return None
    return Image.open(path).convert("RGBA")


def builtin_landmark_path(city: str) -> Path | None:
    preset = landmark_preset(city)
    if preset is None:
        return None
    path = LANDMARK_DIR / str(preset["asset"])
    return path if path.is_file() else None
