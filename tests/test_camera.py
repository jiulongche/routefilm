from routefilm.camera import Camera, fit_geometry, interpolate


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
