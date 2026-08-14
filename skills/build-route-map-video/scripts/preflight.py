#!/usr/bin/env python3
"""Report RouteFilm prerequisites without exposing credential values."""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys


def main() -> int:
    image_url = bool(os.getenv("ROUTEFILM_IMAGE_BASE_URL"))
    image_key = bool(os.getenv("ROUTEFILM_IMAGE_API_KEY") or os.getenv("OPENAI_API_KEY"))
    checks = {
        "python>=3.10": sys.version_info >= (3, 10),
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "numpy": importlib.util.find_spec("numpy") is not None,
        "Pillow": importlib.util.find_spec("PIL") is not None,
        "PyYAML": importlib.util.find_spec("yaml") is not None,
        "rembg(optional)": importlib.util.find_spec("rembg") is not None,
        "GPT Image URL(optional)": image_url,
        "GPT Image key(optional)": image_key,
        "GPT Image generation(optional)": image_url and image_key,
    }
    for name, available in checks.items():
        print(f"{'OK' if available else 'MISSING'}  {name}")
    required = ["python>=3.10", "ffmpeg", "ffprobe", "numpy", "Pillow", "PyYAML"]
    return 0 if all(checks[name] for name in required) else 1


if __name__ == "__main__":
    raise SystemExit(main())
