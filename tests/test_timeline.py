from routefilm.timeline import arrival_times, build_leg_timings, leg_seconds


def test_long_distance_is_faster_and_short_distance_is_slower():
    assert leg_seconds(40) > leg_seconds(500)
    assert leg_seconds(30, "ferry") == 11.0


def test_arrival_times_include_holds():
    timings = build_leg_timings([40, 500], ["driving", "driving"], arrival_seconds=2.2)
    arrivals = arrival_times(timings, intro_seconds=8.2)
    assert arrivals[0] == 12.2
    assert arrivals[1] == 17.4
