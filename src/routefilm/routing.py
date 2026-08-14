"""OSRM adapter with deterministic cache and straight-line fallback."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

from .config import ProjectConfig
from .geo import Point, haversine
from .geocoding import resolve_project


@dataclass
class RoutedLeg:
    origin: str
    destination: str
    distance_km: float
    kind: str
    coordinates: list[Point]


def _fetch_json(url: str, user_agent: str, timeout: int = 90) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _cache_key(config: ProjectConfig) -> str:
    payload = [
        [(stop.name, stop.lon, stop.lat) for stop in config.stops],
        [leg.kind for leg in config.legs],
        config.map.router_url,
    ]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest()[:16]


def _known_ferry_pair(origin: str, destination: str) -> bool:
    names = {origin.rstrip("市县区"), destination.rstrip("市县区")}
    return names == {"海口", "徐闻"}


def _resolved_kind(spec_kind: str, origin: str, destination: str) -> str:
    if spec_kind != "auto":
        return spec_kind
    return "ferry" if _known_ferry_pair(origin, destination) else "driving"


def fetch_routes(config: ProjectConfig, refresh: bool = False) -> list[RoutedLeg]:
    config = resolve_project(config, refresh=refresh)
    cache_dir = config.map.cache_dir / "routes"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{_cache_key(config)}.json"
    if cache_path.exists() and not refresh:
        return [RoutedLeg(**item) for item in json.loads(cache_path.read_text(encoding="utf-8"))]

    result: list[RoutedLeg] = []
    for index, (origin, destination, spec) in enumerate(
        zip(config.stops, config.stops[1:], config.legs)
    ):
        if origin.lon is None or origin.lat is None or destination.lon is None or destination.lat is None:
            raise RuntimeError("route contains unresolved coordinates")
        route_kind = _resolved_kind(spec.kind, origin.name, destination.name)
        url = config.map.router_url.format(
            lon1=origin.lon, lat1=origin.lat, lon2=destination.lon, lat2=destination.lat
        )
        route = None
        for attempt in range(3):
            try:
                payload = _fetch_json(url, config.map.user_agent)
                if payload.get("code") == "Ok" and payload.get("routes"):
                    candidate = payload["routes"][0]
                    route = RoutedLeg(
                        origin.name,
                        destination.name,
                        round(float(candidate["distance"]) / 1000, 2),
                        route_kind,
                        [tuple(map(float, point)) for point in candidate["geometry"]["coordinates"]],
                    )
                    break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
        if route is None:
            start, end = (origin.lon, origin.lat), (destination.lon, destination.lat)
            route = RoutedLeg(
                origin.name,
                destination.name,
                round(haversine(start, end), 2),
                "ferry" if route_kind == "ferry" else "fallback",
                [start, end],
            )
        result.append(route)
        cache_path.write_text(
            json.dumps([asdict(item) for item in result], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if index < len(config.legs) - 1:
            time.sleep(0.25)
    return result
