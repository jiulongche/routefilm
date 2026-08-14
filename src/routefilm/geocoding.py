"""Automatic, cached Nominatim resolution for ordered place names."""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .config import ProjectConfig, Stop

DEFAULT_USER_AGENT = "RouteFilm/0.1 (+https://github.com/jiulongche/routefilm)"


class PlaceResolutionError(ValueError):
    """Raised when a place name cannot be resolved."""


class AmbiguousPlaceError(PlaceResolutionError):
    def __init__(self, query: str, candidates: list[GeocodeCandidate]) -> None:
        self.query = query
        self.candidates = candidates
        choices = "; ".join(candidate.display_name for candidate in candidates[:3])
        super().__init__(f"地名“{query}”有多个同等匹配：{choices}。请说明具体是哪个地点。")


@dataclass(frozen=True)
class GeocodeCandidate:
    name: str
    lon: float
    lat: float
    display_name: str
    osm_type: str | None
    osm_id: int | None
    result_name: str = ""
    place_type: str | None = None
    importance: float = 0.0
    address: dict[str, str] | None = None


def search_place(
    name: str,
    *,
    country_code: str = "cn",
    user_agent: str = DEFAULT_USER_AGENT,
    limit: int = 3,
) -> list[GeocodeCandidate]:
    params = urllib.parse.urlencode(
        {
            "q": name,
            "format": "jsonv2",
            "addressdetails": 1,
            "countrycodes": country_code,
            "limit": min(limit, 5),
        }
    )
    request = urllib.request.Request(
        "https://nominatim.openstreetmap.org/search?" + params,
        headers={"User-Agent": user_agent},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [
        GeocodeCandidate(
            name,
            float(item["lon"]),
            float(item["lat"]),
            item["display_name"],
            item.get("osm_type"),
            item.get("osm_id"),
            str(item.get("name", "")),
            item.get("addresstype") or item.get("type"),
            float(item.get("importance", 0.0)),
            item.get("address") or {},
        )
        for item in payload
    ]


def _normalise_name(value: str) -> str:
    value = re.sub(r"[\s·・]", "", value).casefold()
    for suffix in ("特别行政区", "自治州", "自治区", "自治县", "地区", "新区", "市", "县", "区", "镇", "乡"):
        if value.endswith(suffix):
            return value[: -len(suffix)]
    return value


def _candidate_score(candidate: GeocodeCandidate) -> tuple[int, int, float]:
    query = _normalise_name(candidate.name)
    first_label = candidate.display_name.split(",", 1)[0]
    candidate_name = candidate.result_name or first_label
    exact = int(_normalise_name(candidate_name) == query or _normalise_name(first_label) == query)
    type_rank = {
        "city": 8,
        "municipality": 8,
        "county": 7,
        "district": 6,
        "town": 5,
        "village": 4,
        "administrative": 3,
    }.get(candidate.place_type or "", 1)
    return exact, type_rank, round(candidate.importance, 6)


def choose_candidate(query: str, candidates: list[GeocodeCandidate]) -> GeocodeCandidate:
    if not candidates:
        raise PlaceResolutionError(f"找不到地名“{query}”，请补充省、市或区县名称后重试。")
    ranked = sorted(candidates, key=_candidate_score, reverse=True)
    if len(ranked) > 1:
        first_score = _candidate_score(ranked[0])
        second_score = _candidate_score(ranked[1])
        indistinguishable = (
            first_score[:2] == second_score[:2]
            and abs(first_score[2] - second_score[2]) < 0.005
            and (ranked[0].lon, ranked[0].lat) != (ranked[1].lon, ranked[1].lat)
        )
        if indistinguishable:
            raise AmbiguousPlaceError(query, ranked)
    return ranked[0]


def _query_cache_path(cache_dir: Path, name: str, country_code: str) -> Path:
    digest = hashlib.sha256(f"{country_code}\0{name}".encode()).hexdigest()[:16]
    return cache_dir / f"place-{digest}.json"


def _load_candidates(path: Path) -> list[GeocodeCandidate]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [GeocodeCandidate(**item) for item in payload.get("candidates", [])]


def _save_candidates(path: Path, name: str, candidates: list[GeocodeCandidate]) -> None:
    payload = {
        "provider": "OpenStreetMap Nominatim",
        "query": name,
        "candidates": [asdict(item) for item in candidates],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_project(config: ProjectConfig, refresh: bool = False) -> ProjectConfig:
    """Resolve all missing stop coordinates and retain a technical audit report."""
    if all(stop.lon is not None and stop.lat is not None for stop in config.stops):
        return config

    cache_dir = config.map.cache_dir / "geocoding"
    cache_dir.mkdir(parents=True, exist_ok=True)
    resolved_by_name: dict[str, GeocodeCandidate] = {}
    resolved_stops: list[Stop] = []
    report: list[dict[str, object]] = []
    last_request_at: float | None = None

    for stop in config.stops:
        if stop.lon is not None and stop.lat is not None:
            resolved_stops.append(stop)
            report.append({"query": stop.name, "source": "explicit", "chosen": {"lon": stop.lon, "lat": stop.lat}})
            continue
        if stop.name in resolved_by_name:
            chosen = resolved_by_name[stop.name]
            source = "route-reuse"
        else:
            cache_path = _query_cache_path(cache_dir, stop.name, config.map.country_code)
            if cache_path.exists() and not refresh:
                candidates = _load_candidates(cache_path)
                source = "cache"
            else:
                if last_request_at is not None:
                    time.sleep(max(0.0, 1.05 - (time.monotonic() - last_request_at)))
                candidates = search_place(
                    stop.name,
                    country_code=config.map.country_code,
                    user_agent=config.map.user_agent,
                    limit=5,
                )
                last_request_at = time.monotonic()
                _save_candidates(cache_path, stop.name, candidates)
                source = "network"
            chosen = choose_candidate(stop.name, candidates)
            resolved_by_name[stop.name] = chosen
        resolved_stops.append(replace(stop, lon=chosen.lon, lat=chosen.lat))
        report.append({"query": stop.name, "source": source, "chosen": asdict(chosen)})

    route_digest = hashlib.sha256(
        "\0".join(stop.name for stop in config.stops).encode()
    ).hexdigest()[:16]
    report_path = cache_dir / f"resolution-{route_digest}.json"
    report_path.write_text(
        json.dumps(
            {
                "provider": "OpenStreetMap Nominatim",
                "attribution": "© OpenStreetMap contributors",
                "results": report,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return replace(config, stops=tuple(resolved_stops))


def geocode_route(
    names: list[str],
    output: Path,
    *,
    country_code: str,
    user_agent: str = DEFAULT_USER_AGENT,
) -> Path:
    records = []
    for index, name in enumerate(names):
        candidates = search_place(name, country_code=country_code, user_agent=user_agent)
        try:
            chosen = choose_candidate(name, candidates)
            needs_review = False
        except AmbiguousPlaceError:
            chosen = candidates[0] if candidates else None
            needs_review = True
        records.append(
            {
                "query": name,
                "chosen": asdict(chosen) if chosen else None,
                "alternatives": [asdict(item) for item in candidates if item != chosen],
                "needs_review": needs_review,
            }
        )
        if index < len(names) - 1:
            time.sleep(1.05)
    payload = {
        "provider": "OpenStreetMap Nominatim",
        "attribution": "© OpenStreetMap contributors",
        "warning": "Only entries marked needs_review require place-name clarification.",
        "results": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
