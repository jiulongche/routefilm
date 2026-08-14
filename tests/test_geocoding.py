from pathlib import Path

import pytest

from routefilm.config import load_project
from routefilm.geocoding import (
    AmbiguousPlaceError,
    GeocodeCandidate,
    choose_candidate,
    resolve_project,
)


def _candidate(query: str, lon: float, lat: float, importance: float = 0.8):
    return GeocodeCandidate(
        query,
        lon,
        lat,
        f"{query}市, 中国",
        "relation",
        round(lon * 1000),
        f"{query}市",
        "city",
        importance,
        {"country_code": "cn"},
    )


def test_resolve_project_uses_network_once_per_unique_name_and_then_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    project = tmp_path / "trip.yaml"
    project.write_text("route: [海口, 徐闻, 海口]\n", encoding="utf-8")
    calls: list[str] = []

    def fake_search(name: str, **_kwargs):
        calls.append(name)
        return [_candidate(name, 110.0 + len(calls), 20.0 + len(calls))]

    monkeypatch.setattr("routefilm.geocoding.search_place", fake_search)
    resolved = resolve_project(load_project(project))

    assert calls == ["海口", "徐闻"]
    assert resolved.stops[0].lon == resolved.stops[2].lon
    assert list((tmp_path / ".cache/routefilm/geocoding").glob("resolution-*.json"))

    monkeypatch.setattr(
        "routefilm.geocoding.search_place",
        lambda *_args, **_kwargs: pytest.fail("cached resolution should not use network"),
    )
    cached = resolve_project(load_project(project))
    assert [stop.lon for stop in cached.stops] == [stop.lon for stop in resolved.stops]


def test_only_indistinguishable_candidates_require_clarification():
    candidates = [_candidate("临平", 120.3, 30.4), _candidate("临平", 113.7, 34.6)]

    with pytest.raises(AmbiguousPlaceError, match="请说明具体是哪个地点"):
        choose_candidate("临平", candidates)


def test_importance_breaks_otherwise_equal_place_names():
    candidates = [
        _candidate("南京", 118.8, 32.1, 0.82),
        _candidate("南京", 117.2, 25.1, 0.21),
    ]

    assert choose_candidate("南京", candidates).lon == 118.8
