import pytest

from routefilm.camera import (
    Camera,
    china_national_camera,
    fit_geometry,
    interpolate,
    route_overview_camera,
)
from routefilm.tiles import screen_point


def test_long_leg_is_higher_than_same_short_geometry():
    geometry = [(110.0, 20.0), (111.0, 21.0)]
    short = fit_geometry(geometry, 50, (672, 874))
    long = fit_geometry(geometry, 500, (672, 874))
    assert short.zoom > long.zoom + 1.0


def test_camera_interpolation_keeps_endpoints():
    start = Camera((104.6, 34.7), 3.92)
    end = Camera((120.0, 31.0), 8.0)
    assert interpolate(start, end, 0) == start
    result = interpolate(start, end, 1)
    assert abs(result.center[0] - end.center[0]) < 1e-9
    assert abs(result.center[1] - end.center[1]) < 1e-9
    assert abs(result.zoom - end.zoom) < 1e-9


def test_regional_china_route_uses_tight_full_route_overview():
    route = [(121.47, 31.23), (118.80, 32.06), (117.12, 36.65), (116.41, 39.90)]
    viewport = (672, 874)

    camera = route_overview_camera(route, viewport)

    assert camera.zoom > 5.5
    assert camera != china_national_camera()
    screen = [screen_point(point, camera.center, camera.zoom, (0, 0, *viewport)) for point in route]
    assert all(34 <= x <= viewport[0] - 34 for x, _ in screen)
    assert all(44 <= y <= viewport[1] - 44 for _, y in screen)


def test_broad_china_route_uses_national_overview():
    route = [(110.20, 20.04), (106.23, 38.49), (121.47, 31.23), (116.41, 39.90)]

    assert route_overview_camera(route, (672, 874)) == china_national_camera()


def test_overview_override_remains_authoritative():
    route = [(121.47, 31.23), (116.41, 39.90)]

    camera = route_overview_camera(
        route, (672, 874), override_center=(112.0, 35.0), override_zoom=4.75
    )

    assert camera == Camera((112.0, 35.0), 4.75)


def test_overview_override_requires_center_and_zoom_together():
    with pytest.raises(ValueError, match="both center and zoom"):
        route_overview_camera([(121.47, 31.23)], (672, 874), override_zoom=5.0)
