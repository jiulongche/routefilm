"""Landmark selection during arrival showcases."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFont

from routefilm import renderer as renderer_module
from routefilm.config import LegSpec, ProjectConfig, Stop, VideoSettings
from routefilm.renderer import Renderer
from routefilm.routing import RoutedLeg


class _StubFonts:
    """Keep the renderer independent of whichever CJK font the host happens to ship."""

    def __init__(self, path: Path, scale: float) -> None:
        default = ImageFont.load_default()
        self.hero = self.city = self.body = self.small = self.tiny = default


def _landmark_file(directory: Path, name: str) -> Path:
    path = directory / f"{name}.png"
    Image.new("RGBA", (24, 24), (200, 160, 60, 255)).save(path)
    return path


def _project(tmp_path: Path) -> tuple[ProjectConfig, list[RoutedLeg]]:
    stops = (
        Stop("上海", 121.47, 31.23, landmark_asset=_landmark_file(tmp_path, "shanghai")),
        Stop("南京", 118.78, 32.04, landmark_asset=_landmark_file(tmp_path, "nanjing")),
    )
    config = ProjectConfig(
        stops=stops,
        legs=(LegSpec(),),
        video=VideoSettings(font_path=None),
    )
    routes = [
        RoutedLeg("上海", "南京", 297.0, "road", [(121.47, 31.23), (120.0, 31.6), (118.78, 32.04)])
    ]
    return config, routes


def _record_landmarks(monkeypatch) -> list[str]:
    seen: list[str] = []
    monkeypatch.setattr(renderer_module, "_font_path", lambda configured: Path("stub.ttc"))
    monkeypatch.setattr(renderer_module, "Fonts", _StubFonts)
    monkeypatch.setattr(
        renderer_module,
        "render_basemap",
        lambda *args, **kwargs: Image.new("RGB", args[3] if len(args) > 3 else (100, 100), (240, 240, 240)),
    )
    monkeypatch.setattr(
        Renderer,
        "_landmark",
        lambda self, layer, stop, phase, repeated: seen.append(stop.name),
    )
    return seen


def test_arrival_showcase_defaults_to_leg_destination(tmp_path: Path, monkeypatch):
    config, routes = _project(tmp_path)
    seen = _record_landmarks(monkeypatch)
    renderer = Renderer(config, routes)

    renderer.frame(renderer.cameras[0], 0, 1, 1, arrival_phase=0.5)

    assert seen == ["南京"]


def test_origin_showcase_uses_origin_landmark(tmp_path: Path, monkeypatch):
    """The opening showcase runs at leg_index 0 but belongs to the first stop, not the destination."""
    config, routes = _project(tmp_path)
    seen = _record_landmarks(monkeypatch)
    renderer = Renderer(config, routes)

    renderer.frame(
        renderer.cameras[0], 0, 0, 0, arrival_phase=0.5, arrival_stop=config.stops[0]
    )

    assert seen == ["上海"]
