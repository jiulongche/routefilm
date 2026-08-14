"""YAML project configuration with strict, public-safe defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Stop:
    name: str
    lon: float | None = None
    lat: float | None = None
    landmark: str | None = None
    landmark_asset: Path | None = None


@dataclass(frozen=True)
class LegSpec:
    kind: str = "auto"
    duration_seconds: float | None = None


@dataclass(frozen=True)
class MapSettings:
    tile_url: str = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    router_url: str = (
        "https://router.project-osrm.org/route/v1/driving/"
        "{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    )
    user_agent: str = "RouteFilm/0.1 (+https://github.com/jiulongche/routefilm)"
    country_code: str = "cn"
    cache_dir: Path = Path(".cache/routefilm")
    national_center: tuple[float, float] | None = None
    national_zoom: float | None = None


@dataclass(frozen=True)
class VideoSettings:
    width: int = 720
    height: int = 1280
    fps: int = 15
    crf: int = 18
    title: str = "Road Trip"
    output: Path = Path("output/routefilm.mp4")
    font_path: Path | None = None
    marker: str = "arrow"
    show_ferry: bool = True
    vehicle_asset: Path | None = None
    ferry_asset: Path | None = None
    intro_hold_seconds: float = 1.8
    dive_seconds: float = 4.2
    arrival_seconds: float = 2.2
    outro_seconds: float = 6.0
    final_hold_seconds: float = 3.0


@dataclass(frozen=True)
class ProjectConfig:
    stops: tuple[Stop, ...]
    legs: tuple[LegSpec, ...]
    map: MapSettings = field(default_factory=MapSettings)
    video: VideoSettings = field(default_factory=VideoSettings)
    source_path: Path | None = None


def _path(base: Path, value: Any) -> Path | None:
    if value in (None, ""):
        return None
    candidate = Path(str(value)).expanduser()
    return candidate if candidate.is_absolute() else (base / candidate).resolve()


def _route_items(raw: dict[str, Any]) -> list[Any]:
    if "route" in raw and "stops" in raw:
        raise ValueError("use either route or stops, not both")
    items = raw.get("route", raw.get("stops", []))
    if isinstance(items, str):
        for separator in ("、", "，", ","):
            items = items.replace(separator, "|")
        return [name.strip() for name in items.split("|") if name.strip()]
    if not isinstance(items, list):
        raise TypeError("route must be an ordered list of place names")
    return items


def _stop(item: Any, base: Path) -> Stop:
    if isinstance(item, str):
        name = item.strip()
        if not name:
            raise ValueError("route contains an empty place name")
        return Stop(name=name)
    if not isinstance(item, dict) or not item.get("name"):
        raise ValueError("each route item must be a place name or a mapping with name")
    lon = float(item["lon"]) if item.get("lon") is not None else None
    lat = float(item["lat"]) if item.get("lat") is not None else None
    if (lon is None) != (lat is None):
        raise ValueError(f"{item['name']}: provide both lon and lat, or neither")
    return Stop(
        name=str(item["name"]).strip(),
        lon=lon,
        lat=lat,
        landmark=item.get("landmark"),
        landmark_asset=_path(base, item.get("landmark_asset")),
    )


def load_project(path: str | Path) -> ProjectConfig:
    source = Path(path).expanduser().resolve()
    raw = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    base = source.parent
    stops = tuple(_stop(item, base) for item in _route_items(raw))
    if len(stops) < 2:
        raise ValueError("project needs at least two ordered stops")
    raw_legs = raw.get("legs")
    if raw_legs is None:
        raw_legs = [{} for _ in range(len(stops) - 1)]
    if len(raw_legs) != len(stops) - 1:
        raise ValueError("legs must contain exactly len(stops) - 1 entries")
    legs = tuple(
        LegSpec(
            str(item.get("kind", "auto")),
            float(item["duration_seconds"]) if item.get("duration_seconds") is not None else None,
        )
        for item in raw_legs
    )
    for leg in legs:
        if leg.kind not in {"auto", "driving", "ferry", "fallback"}:
            raise ValueError(f"unsupported leg kind: {leg.kind}")

    map_raw = raw.get("map", {})
    center = map_raw.get("national_center")
    map_settings = MapSettings(
        tile_url=map_raw.get("tile_url", MapSettings.tile_url),
        router_url=map_raw.get("router_url", MapSettings.router_url),
        user_agent=map_raw.get("user_agent", MapSettings.user_agent),
        country_code=str(map_raw.get("country_code", "cn")),
        cache_dir=_path(base, map_raw.get("cache_dir", ".cache/routefilm")) or Path(".cache/routefilm"),
        national_center=tuple(map(float, center)) if center else None,
        national_zoom=float(map_raw["national_zoom"]) if "national_zoom" in map_raw else None,
    )
    video_raw = raw.get("video", {})
    video = VideoSettings(
        width=int(video_raw.get("width", 720)),
        height=int(video_raw.get("height", 1280)),
        fps=int(video_raw.get("fps", 15)),
        crf=int(video_raw.get("crf", 18)),
        title=str(video_raw.get("title", "Road Trip")),
        output=_path(base, video_raw.get("output", "output/routefilm.mp4")) or Path("output/routefilm.mp4"),
        font_path=_path(base, video_raw.get("font_path")),
        marker=str(video_raw.get("marker", "arrow")),
        show_ferry=bool(video_raw.get("show_ferry", True)),
        vehicle_asset=_path(base, video_raw.get("vehicle_asset")),
        ferry_asset=_path(base, video_raw.get("ferry_asset")),
        intro_hold_seconds=float(video_raw.get("intro_hold_seconds", 1.8)),
        dive_seconds=float(video_raw.get("dive_seconds", 4.2)),
        arrival_seconds=float(video_raw.get("arrival_seconds", 2.2)),
        outro_seconds=float(video_raw.get("outro_seconds", 6.0)),
        final_hold_seconds=float(video_raw.get("final_hold_seconds", 3.0)),
    )
    if video.width < 320 or video.height < 320 or video.fps < 1:
        raise ValueError("video dimensions or fps are invalid")
    if video.marker not in {"arrow", "black-suv"}:
        raise ValueError("video.marker must be arrow or black-suv")
    return ProjectConfig(stops, legs, map_settings, video, source)
