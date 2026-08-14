import math

import numpy as np

from routefilm.geo import (
    heading_displacement_error,
    lonlat_from_world,
    normalized_world,
    sample_by_distance,
    vehicle_motion_series,
)


def test_mercator_round_trip():
    for point in [(110.2, 20.04), (121.47, 31.23), (104.6, 34.7)]:
        restored = lonlat_from_world(*normalized_world(*point))
        assert math.isclose(restored[0], point[0], abs_tol=1e-9)
        assert math.isclose(restored[1], point[1], abs_tol=1e-9)


def test_distance_sampling_keeps_endpoints_and_spreads_samples():
    points = [(110.0, 20.0), (110.01, 20.0), (111.0, 20.0)]
    sampled = sample_by_distance(points, 5)
    assert np.allclose(sampled[0], points[0])
    assert np.allclose(sampled[-1], points[-1])
    assert sampled[1][0] > 110.1


def test_heading_uses_same_smoothed_trajectory():
    route = [(110.0, 20.0), (110.1, 20.0), (110.2, 20.05), (110.3, 20.18)]
    positions, headings = vehicle_motion_series(route, 80)
    assert heading_displacement_error(positions, headings) < 1e-8
