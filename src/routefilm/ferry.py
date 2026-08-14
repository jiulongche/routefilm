"""Direction-neutral staged vehicle/ferry handoff."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from .geo import Point, cumulative_distances, position_at_distance, smoothstep

FerryStage = Literal["approach", "boarding", "sailing", "exiting", "destination"]


@dataclass(frozen=True)
class FerryState:
    stage: FerryStage
    stage_progress: float
    route_progress: float


def sea_gap_boundaries(points: Sequence[Point]) -> tuple[float, float]:
    """Infer the sea span from the longest unsampled gap in route geometry."""
    cumulative = cumulative_distances(points)
    if len(points) < 2 or cumulative[-1] <= 0:
        return 0.0, 1.0
    spans = cumulative[1:] - cumulative[:-1]
    index = int(spans.argmax())
    return float(cumulative[index] / cumulative[-1]), float(cumulative[index + 1] / cumulative[-1])


def ferry_state(points: Sequence[Point], local: float) -> FerryState:
    embark, disembark = sea_gap_boundaries(points)
    local = min(1.0, max(0.0, local))
    if local < 0.23:
        phase = smoothstep(local / 0.23)
        return FerryState("approach", phase, embark * phase)
    if local < 0.35:
        return FerryState("boarding", smoothstep((local - 0.23) / 0.12), embark)
    if local < 0.68:
        phase = smoothstep((local - 0.35) / 0.33)
        return FerryState("sailing", phase, embark + (disembark - embark) * phase)
    if local < 0.80:
        return FerryState("exiting", smoothstep((local - 0.68) / 0.12), disembark)
    phase = smoothstep((local - 0.80) / 0.20)
    return FerryState("destination", phase, disembark + (1.0 - disembark) * phase)


def boundary_positions(points: Sequence[Point]) -> tuple[Point, Point]:
    cumulative = cumulative_distances(points)
    embark, disembark = sea_gap_boundaries(points)
    return (
        position_at_distance(points, cumulative, cumulative[-1] * embark),
        position_at_distance(points, cumulative, cumulative[-1] * disembark),
    )
