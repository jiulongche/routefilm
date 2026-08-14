"""Timeline rules for long legs, dense city clusters, arrivals, and ferries."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class LegTiming:
    travel_seconds: float
    arrival_seconds: float


def leg_seconds(distance_km: float, kind: str = "driving") -> float:
    if kind == "ferry":
        return 11.0
    if distance_km < 55:
        return 4.0
    if distance_km < 120:
        return 3.6
    if distance_km < 280:
        return 3.3
    if distance_km < 420:
        return 3.15
    return 3.0


def build_leg_timings(
    distances: Sequence[float], kinds: Sequence[str], arrival_seconds: float = 2.2
) -> list[LegTiming]:
    if len(distances) != len(kinds):
        raise ValueError("distances and kinds must have equal length")
    return [LegTiming(leg_seconds(distance, kind), arrival_seconds) for distance, kind in zip(distances, kinds)]


def arrival_times(
    timings: Sequence[LegTiming], intro_seconds: float = 8.2
) -> list[float]:
    result: list[float] = []
    cursor = intro_seconds
    for timing in timings:
        cursor += timing.travel_seconds
        result.append(cursor)
        cursor += timing.arrival_seconds
    return result
