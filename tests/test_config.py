from pathlib import Path

import pytest

from routefilm.config import load_project


def test_load_project_resolves_relative_paths(tmp_path: Path):
    project = tmp_path / "trip.yaml"
    project.write_text(
        """
stops:
  - {name: A, lon: 110, lat: 20}
  - {name: B, lon: 111, lat: 21}
legs:
  - {kind: ferry}
video:
  output: output/trip.mp4
""",
        encoding="utf-8",
    )
    config = load_project(project)
    assert config.legs[0].kind == "ferry"
    assert config.video.marker == "arrow"
    assert config.video.show_ferry is True
    assert config.video.output == (tmp_path / "output/trip.mp4").resolve()


def test_load_name_only_route_with_auto_legs(tmp_path: Path):
    project = tmp_path / "trip.yaml"
    project.write_text("route: [海口, 徐闻, 湛江]\n", encoding="utf-8")

    config = load_project(project)

    assert [stop.name for stop in config.stops] == ["海口", "徐闻", "湛江"]
    assert all(stop.lon is None and stop.lat is None for stop in config.stops)
    assert [leg.kind for leg in config.legs] == ["auto", "auto"]


def test_load_route_from_single_readable_string(tmp_path: Path):
    project = tmp_path / "trip.yaml"
    project.write_text("route: 海口、徐闻、湛江\n", encoding="utf-8")

    assert [stop.name for stop in load_project(project).stops] == ["海口", "徐闻", "湛江"]


def test_project_rejects_wrong_leg_count(tmp_path: Path):
    project = tmp_path / "trip.yaml"
    project.write_text(
        "stops: [{name: A, lon: 1, lat: 1}, {name: B, lon: 2, lat: 2}]\nlegs: []\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="legs"):
        load_project(project)


def test_black_suv_preset_and_ferry_toggle(tmp_path: Path):
    project = tmp_path / "trip.yaml"
    project.write_text(
        "stops: [{name: A, lon: 1, lat: 1}, {name: B, lon: 2, lat: 2}]\n"
        "video: {marker: black-suv, show_ferry: false}\n",
        encoding="utf-8",
    )

    config = load_project(project)
    assert config.video.marker == "black-suv"
    assert config.video.show_ferry is False
