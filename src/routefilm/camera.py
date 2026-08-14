"""Distance-aware camera planning in Web Mercator space."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .geo import Point, clamp, lonlat_from_world, normalized_world, smootherstep


@dataclass(frozen=True)
class Camera:
    center: Point
    zoom: float


def fit_geometry(
    points: Sequence[Point],
    distance_km: float,
    viewport: tuple[int, int],
    padding: tuple[float, float] = (0.68, 0.68),
) -> Camera:
    worlds = [normalized_world(*point) for point in points]
    xs, ys = zip(*worlds)
    span_x = max(max(xs) - min(xs), 1e-7)
    span_y = max(max(ys) - min(ys), 1e-7)
    width, height = viewport
    zoom = math.log2(min(width * padding[0] / (256 * span_x), height * padding[1] / (256 * span_y)))
    if distance_km > 420:
        zoom -= 0.72
    elif distance_km > 280:
        zoom -= 0.32
    elif distance_km < 55:
        zoom += 0.58
    elif distance_km < 120:
        zoom += 0.34
    center = lonlat_from_world((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    return Camera(center, clamp(zoom, 4.6, 11.5))


def interpolate(start: Camera, end: Camera, progress: float) -> Camera:
    if progress <= 0:
        return start
    if progress >= 1:
        return end
    amount = smootherstep(progress)
    ax, ay = normalized_world(*start.center)
    bx, by = normalized_world(*end.center)
    center = lonlat_from_world(ax + (bx - ax) * amount, ay + (by - ay) * amount)
    zoom = math.exp(math.log(start.zoom) * (1 - amount) + math.log(end.zoom) * amount)
    return Camera(center, zoom)


def china_national_camera() -> Camera:
    """A stable portrait framing that includes the full Taiwan island."""
    return Camera((104.6, 34.7), 3.92)
