"""Video decode, stream, black-frame, and silence checks."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def require_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"required executable not found: {name}")
    return path


def probe_video(path: Path) -> dict[str, Any]:
    require_binary("ffprobe")
    completed = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return json.loads(completed.stdout)


def decode_check(path: Path) -> None:
    require_binary("ffmpeg")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], check=True
    )


def black_frames(path: Path) -> list[dict[str, float]]:
    completed = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-i", str(path), "-vf",
            "blackdetect=d=0.25:pix_th=0.04", "-an", "-f", "null", "-",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    pattern = re.compile(r"black_start:(\S+) black_end:(\S+) black_duration:(\S+)")
    return [
        {"start": float(a), "end": float(b), "duration": float(c)}
        for a, b, c in pattern.findall(completed.stderr)
    ]


def inspect(path: Path, full_decode: bool = True) -> dict[str, Any]:
    if full_decode:
        decode_check(path)
    probe = probe_video(path)
    video = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
    audio = next((stream for stream in probe["streams"] if stream["codec_type"] == "audio"), None)
    if video is None:
        raise RuntimeError("file has no video stream")
    return {
        "path": str(path),
        "decode_ok": True,
        "duration_seconds": float(probe["format"].get("duration", 0)),
        "video": {
            "codec": video.get("codec_name"),
            "width": video.get("width"),
            "height": video.get("height"),
            "pixel_format": video.get("pix_fmt"),
        },
        "audio": None if audio is None else {"codec": audio.get("codec_name"), "sample_rate": audio.get("sample_rate")},
        "black_frames": black_frames(path),
    }
