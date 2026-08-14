"""Projection, distance sampling, and vehicle-heading primitives."""

from __future__ import annotations

import math
from bisect import bisect_right
from collections.abc import Sequence

import numpy as np

Point = tuple[float, float]
EARTH_RADIUS_KM = 6371.0088
MAX_MERCATOR_LAT = 85.05112878


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def smoothstep(value: float) -> float:
    value = clamp(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def smootherstep(value: float) -> float:
    value = clamp(value, 0.0, 1.0)
    return value**3 * (value * (value * 6.0 - 15.0) + 10.0)


def normalized_world(lon: float, lat: float) -> Point:
    """Convert WGS84 lon/lat to normalized Web Mercator coordinates."""
    lat = clamp(lat, -MAX_MERCATOR_LAT, MAX_MERCATOR_LAT)
    x = (lon + 180.0) / 360.0
    sin_lat = math.sin(math.radians(lat))
    y = 0.5 - math.log((1.0 + sin_lat) / (1.0 - sin_lat)) / (4.0 * math.pi)
    return x, y


def lonlat_from_world(x: float, y: float) -> Point:
    return x * 360.0 - 180.0, math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y))))


def haversine(a: Point, b: Point) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    dlon, dlat = lon2 - lon1, lat2 - lat1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(value))


def cumulative_distances(points: Sequence[Point]) -> np.ndarray:
    if not points:
        raise ValueError("route must contain at least one point")
    result = np.zeros(len(points), dtype=float)
    for index in range(1, len(points)):
        result[index] = result[index - 1] + haversine(points[index - 1], points[index])
    return result


def position_at_distance(
    points: Sequence[Point], cumulative: Sequence[float], distance_km: float
) -> Point:
    if len(points) != len(cumulative):
        raise ValueError("points and cumulative lengths differ")
    if len(points) == 1 or cumulative[-1] <= 0:
        return points[0]
    target = clamp(distance_km, 0.0, float(cumulative[-1]))
    index = min(len(points) - 2, max(0, bisect_right(cumulative, target) - 1))
    span = cumulative[index + 1] - cumulative[index]
    amount = 0.0 if span <= 0 else (target - cumulative[index]) / span
    return (
        points[index][0] + (points[index + 1][0] - points[index][0]) * amount,
        points[index][1] + (points[index + 1][1] - points[index][1]) * amount,
    )


def sample_by_distance(points: Sequence[Point], count: int) -> np.ndarray:
    """Sample a route at equal traveled-distance intervals."""
    if count < 2:
        raise ValueError("count must be at least 2")
    cumulative = cumulative_distances(points)
    targets = np.linspace(0.0, cumulative[-1], count)
    return np.asarray([position_at_distance(points, cumulative, value) for value in targets])


def gaussian_smooth(values: np.ndarray, radius: int = 4, sigma: float = 1.7) -> np.ndarray:
    if radius <= 0 or len(values) < 3:
        return values.copy()
    axis = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-(axis * axis) / (2 * sigma * sigma))
    kernel /= kernel.sum()
    channels = []
    for channel in range(values.shape[1]):
        padded = np.pad(values[:, channel], (radius, radius), mode="edge")
        channels.append(np.convolve(padded, kernel, mode="valid"))
    result = np.column_stack(channels)
    result[0], result[-1] = values[0], values[-1]
    return result


def vehicle_motion_series(points: Sequence[Point], count: int) -> tuple[np.ndarray, np.ndarray]:
    """Return a smoothed lon/lat path and headings from that exact same path.

    Position and heading share one trajectory, which prevents the sideways-slide
    artifact caused by smoothing them independently.
    """
    sampled = sample_by_distance(points, count)
    world = np.asarray([normalized_world(lon, lat) for lon, lat in sampled])
    radius = min(5, max(1, count // 12))
    world = gaussian_smooth(world, radius=radius, sigma=max(1.0, radius / 2.2))
    positions = np.asarray([lonlat_from_world(x, y) for x, y in world])
    tangents = np.empty_like(world)
    tangents[:-1] = world[1:] - world[:-1]
    tangents[-1] = tangents[-2]
    headings = np.arctan2(tangents[:, 1], tangents[:, 0])
    return positions, headings


def heading_displacement_error(positions: np.ndarray, headings: np.ndarray) -> float:
    """Return maximum heading/displacement disagreement in degrees."""
    world = np.asarray([normalized_world(lon, lat) for lon, lat in positions])
    errors: list[float] = []
    for index in range(len(world) - 1):
        delta = world[index + 1] - world[index]
        if np.linalg.norm(delta) < 1e-12:
            continue
        actual = math.atan2(delta[1], delta[0])
        expected = float(headings[index])
        error = abs((actual - expected + math.pi) % (2 * math.pi) - math.pi)
        errors.append(math.degrees(error))
    return max(errors, default=0.0)
