from pathlib import Path

import pytest

from routefilm.config import load_project
from routefilm.routing import fetch_routes


def test_auto_classifies_haikou_xuwen_as_ferry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    project = tmp_path / "trip.yaml"
    project.write_text(
        """
stops:
  - {name: 海口, lon: 110.2, lat: 20.04}
  - {name: 徐闻, lon: 110.18, lat: 20.33}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "routefilm.routing._fetch_json",
        lambda *_args, **_kwargs: {
            "code": "Ok",
            "routes": [
                {
                    "distance": 42000,
                    "geometry": {"coordinates": [[110.2, 20.04], [110.18, 20.33]]},
                }
            ],
        },
    )

    assert fetch_routes(load_project(project))[0].kind == "ferry"


def test_explicit_driving_override_is_preserved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    project = tmp_path / "trip.yaml"
    project.write_text(
        """
stops:
  - {name: 海口, lon: 110.2, lat: 20.04}
  - {name: 徐闻, lon: 110.18, lat: 20.33}
legs:
  - {kind: driving}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "routefilm.routing._fetch_json",
        lambda *_args, **_kwargs: {
            "code": "Ok",
            "routes": [
                {
                    "distance": 42000,
                    "geometry": {"coordinates": [[110.2, 20.04], [110.18, 20.33]]},
                }
            ],
        },
    )

    assert fetch_routes(load_project(project))[0].kind == "driving"
