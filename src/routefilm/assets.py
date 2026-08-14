"""Built-in marker art and optional GPT Image 2 vehicle generation."""

from __future__ import annotations

import base64
import json
import os
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

IMAGE_MODEL = "gpt-image-2"
DATA_DIR = Path(__file__).with_name("data")


def builtin_marker(name: str) -> Image.Image:
    """Load a bundled route marker by its stable preset name."""
    if name == "arrow":
        path = DATA_DIR / "marker-arrow.png"
    elif name == "black-suv":
        path = DATA_DIR / "marker-black-suv.png"
    else:
        raise ValueError(f"unknown marker preset: {name}")
    return Image.open(path).convert("RGBA")


def builtin_ferry() -> Image.Image:
    """Load the bundled top-down roll-on/roll-off ferry."""
    return Image.open(DATA_DIR / "ferry-ro-ro.png").convert("RGBA")


def default_arrow(size: int = 192) -> Image.Image:
    """Return the bundled generated arrow on a square transparent canvas."""
    marker = builtin_marker("arrow")
    marker.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(
        marker,
        ((size - marker.width) // 2, (size - marker.height) // 2),
    )
    return canvas


def save_default_arrow(path: Path, size: int = 512) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    default_arrow(size).save(path)
    return path


def vehicle_prompt(description: str) -> str:
    return f"""Create one map-animation vehicle sprite: {description}.
Strict true bird's-eye orthographic view, camera exactly 90 degrees above.
The vehicle nose points exactly to the right. Center one complete vehicle in a square canvas,
occupying about 68% of the width with generous even padding. Premium semi-realistic miniature,
crisp silhouette readable at 48 pixels, realistic materials, restrained highlights.
Background must be one flat chroma green color #00FF00 edge to edge.
Exactly one vehicle; no road, map, people, scenery, text, logo, watermark, cast shadow,
contact shadow, motion blur, perspective view, or cropped body."""


def landmark_prompt(city: str, landmark: str) -> str:
    return f"""Create one map-animation landmark miniature for {city}: {landmark}.
Show one recognizable landmark as a polished semi-realistic miniature diorama, viewed from a
slightly elevated orthographic angle. Keep the silhouette accurate and readable when reduced,
with crisp architectural detail and restrained natural color. Center the complete landmark with
generous padding on a perfectly flat chroma green #00FF00 background edge to edge.
No city name, caption, letters, logo, watermark, people, map, road, frame, cast shadow, contact
shadow, background scenery, gradient, or cropped structure."""


def image_api_status(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
) -> dict[str, bool | str]:
    """Report image-generation readiness without exposing credential values."""
    endpoint = base_url or os.getenv("ROUTEFILM_IMAGE_BASE_URL")
    key = api_key or os.getenv("ROUTEFILM_IMAGE_API_KEY") or os.getenv("OPENAI_API_KEY")
    return {
        "model": IMAGE_MODEL,
        "url_configured": bool(endpoint),
        "key_configured": bool(key),
        "generation_enabled": bool(endpoint and key),
    }


def _image_api_credentials(
    base_url: str | None,
    api_key: str | None,
) -> tuple[str, str]:
    endpoint = base_url or os.getenv("ROUTEFILM_IMAGE_BASE_URL")
    key = api_key or os.getenv("ROUTEFILM_IMAGE_API_KEY") or os.getenv("OPENAI_API_KEY")
    missing = []
    if not endpoint:
        missing.append("ROUTEFILM_IMAGE_BASE_URL")
    if not key:
        missing.append("ROUTEFILM_IMAGE_API_KEY (or OPENAI_API_KEY)")
    if missing:
        raise RuntimeError(
            "image generation is disabled; configure both image API URL and key: "
            + ", ".join(missing)
        )
    return endpoint.rstrip("/"), key


def _remove_chroma(image: Image.Image) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA")).copy()
    rgb = rgba[:, :, :3].astype(np.int32)
    border = np.concatenate(
        (rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]),
        axis=0,
    )
    key = np.median(border, axis=0)
    key_distance = np.sqrt(((rgb - key) ** 2).sum(axis=2))
    distance_alpha = np.clip((key_distance - 14) * (255 / 116), 0, 255)
    dominant_green = np.maximum(rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2]), 0)
    dominance_alpha = np.clip((100 - dominant_green) * (255 / 70), 0, 255)
    dominance_alpha = np.where(rgb[:, :, 1] >= 70, dominance_alpha, 255)
    alpha = np.minimum(distance_alpha, dominance_alpha).astype(np.uint8)
    partial = 1.0 - alpha.astype(np.float32) / 255
    rgba[:, :, 1] = np.clip(
        rgb[:, :, 1] - dominant_green * partial,
        0,
        255,
    ).astype(np.uint8)
    rgba[:, :, 3] = np.minimum(rgba[:, :, 3], alpha)
    result = Image.fromarray(rgba, "RGBA")
    bbox = result.getchannel("A").getbbox()
    return result.crop(bbox) if bbox else result


def remove_background(image: Image.Image, method: str = "auto") -> Image.Image:
    """Cut out an asset with rembg when available, then fall back to chroma keying."""
    if method not in {"auto", "rembg", "chroma"}:
        raise ValueError("method must be auto, rembg, or chroma")
    if method in {"auto", "rembg"}:
        try:
            from rembg import remove  # optional dependency

            result = remove(image.convert("RGBA"), alpha_matting=True)
            if not isinstance(result, Image.Image):
                raise TypeError("rembg returned non-image data")
            bbox = result.getchannel("A").getbbox()
            return result.crop(bbox) if bbox else result
        except ImportError:
            if method == "rembg":
                raise RuntimeError("install routefilm[cutout] to use rembg") from None
    return _remove_chroma(image)


def cutout_file(source: Path, output: Path, method: str = "auto") -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    remove_background(Image.open(source), method).save(output)
    return output


def _generate_asset(
    prompt: str,
    output: Path,
    *,
    asset_kind: str,
    base_url: str | None = None,
    api_key: str | None = None,
    quality: str = "high",
) -> tuple[Path, Path]:
    endpoint, key = _image_api_credentials(base_url, api_key)
    payload = json.dumps(
        {
            "model": IMAGE_MODEL,
            "prompt": prompt,
            "size": "1024x1024",
            "quality": quality,
            "output_format": "png",
        }
    ).encode()
    request = urllib.request.Request(
        f"{endpoint}/images/generations",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))
    image_bytes = base64.b64decode(result["data"][0]["b64_json"])
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = output.with_name(output.stem + "-chroma.png")
    raw.write_bytes(image_bytes)
    image = remove_background(Image.open(raw), "auto")
    image.save(output)
    record = output.with_suffix(".generation.json")
    record.write_text(
        json.dumps(
            {
                "asset_kind": asset_kind,
                "model": IMAGE_MODEL,
                "endpoint_configured": True,
                "prompt": prompt,
                "quality": quality,
                "raw": raw.name,
                "output": output.name,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return output, record


def generate_vehicle(
    description: str,
    output: Path,
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    quality: str = "high",
) -> tuple[Path, Path]:
    """Generate a custom marker with GPT Image 2 and record the exact prompt."""
    return _generate_asset(
        vehicle_prompt(description),
        output,
        asset_kind="vehicle",
        base_url=base_url,
        api_key=api_key,
        quality=quality,
    )


def generate_landmark(
    city: str,
    landmark: str,
    output: Path,
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    quality: str = "high",
) -> tuple[Path, Path]:
    """Generate a city landmark miniature with GPT Image 2."""
    return _generate_asset(
        landmark_prompt(city, landmark),
        output,
        asset_kind="landmark",
        base_url=base_url,
        api_key=api_key,
        quality=quality,
    )
