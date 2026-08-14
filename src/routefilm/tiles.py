"""Small, policy-conscious raster tile client and Web Mercator compositor."""

from __future__ import annotations

import io
import math
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .geo import Point, normalized_world

TILE_SIZE = 256


class TileStore:
    def __init__(
        self,
        cache_dir: Path,
        tile_url: str,
        user_agent: str,
        max_memory: int = 192,
    ) -> None:
        self.cache_dir = cache_dir / "tiles"
        self.tile_url = tile_url
        self.user_agent = user_agent
        self.max_memory = max_memory
        self.memory: OrderedDict[tuple[int, int, int], Image.Image] = OrderedDict()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, z: int, x: int, y: int) -> Image.Image:
        count = 2**z
        x %= count
        if y < 0 or y >= count:
            return Image.new("RGB", (TILE_SIZE, TILE_SIZE), (220, 230, 232))
        key = z, x, y
        if key in self.memory:
            image = self.memory.pop(key)
            self.memory[key] = image
            return image
        path = self.cache_dir / str(z) / str(x) / f"{y}.png"
        if path.exists():
            image = Image.open(path).convert("RGB")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            request = urllib.request.Request(
                self.tile_url.format(z=z, x=x, y=y), headers={"User-Agent": self.user_agent}
            )
            last_error: Exception | None = None
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(request, timeout=45) as response:
                        image = Image.open(io.BytesIO(response.read())).convert("RGB")
                    image.save(path, optimize=True)
                    break
                except (urllib.error.URLError, TimeoutError, OSError, UnidentifiedImageError) as error:
                    last_error = error
                    time.sleep(1.0 + attempt)
            else:
                raise RuntimeError(f"tile unavailable {z}/{x}/{y}: {last_error}")
        self.memory[key] = image
        while len(self.memory) > self.max_memory:
            self.memory.popitem(last=False)
        return image


def render_basemap(
    store: TileStore, center: Point, zoom: float, size: tuple[int, int]
) -> Image.Image:
    width, height = size
    tile_zoom = max(2, min(18, math.ceil(zoom)))
    scale = 2 ** (zoom - tile_zoom)
    world_size = TILE_SIZE * (2**tile_zoom)
    cx, cy = normalized_world(*center)
    cx, cy = cx * world_size, cy * world_size
    source_w, source_h = width / scale, height / scale
    left, top = cx - source_w / 2, cy - source_h / 2
    right, bottom = left + source_w, top + source_h
    tx0, ty0 = math.floor(left / TILE_SIZE), math.floor(top / TILE_SIZE)
    tx1, ty1 = math.floor((right - 1) / TILE_SIZE), math.floor((bottom - 1) / TILE_SIZE)
    mosaic = Image.new("RGB", ((tx1 - tx0 + 1) * TILE_SIZE, (ty1 - ty0 + 1) * TILE_SIZE))
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            mosaic.paste(store.get(tile_zoom, tx, ty), ((tx - tx0) * TILE_SIZE, (ty - ty0) * TILE_SIZE))
    crop = mosaic.crop(
        (left - tx0 * TILE_SIZE, top - ty0 * TILE_SIZE, right - tx0 * TILE_SIZE, bottom - ty0 * TILE_SIZE)
    )
    return crop.resize((width, height), Image.Resampling.LANCZOS)


def screen_point(point: Point, center: Point, zoom: float, rect: tuple[int, int, int, int]) -> Point:
    left, top, right, bottom = rect
    world_size = TILE_SIZE * (2**zoom)
    x, y = normalized_world(*point)
    cx, cy = normalized_world(*center)
    return (
        left + (right - left) / 2 + (x - cx) * world_size,
        top + (bottom - top) / 2 + (y - cy) * world_size,
    )
