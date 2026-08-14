from routefilm.ferry import ferry_state, sea_gap_boundaries

ROUTE = [(110.20, 20.04), (110.19, 20.07), (110.18, 20.10), (110.17, 20.29), (110.18, 20.33)]


def test_longest_gap_is_sea_span():
    embark, disembark = sea_gap_boundaries(ROUTE)
    assert 0 < embark < disembark < 1


def test_ferry_stages_and_stationary_handoffs():
    assert ferry_state(ROUTE, 0.1).stage == "approach"
    boarding = ferry_state(ROUTE, 0.3)
    assert boarding.stage == "boarding"
    assert ferry_state(ROUTE, 0.5).stage == "sailing"
    exiting = ferry_state(ROUTE, 0.74)
    assert exiting.stage == "exiting"
    assert ferry_state(ROUTE, 0.9).stage == "destination"
    assert boarding.route_progress < exiting.route_progress


def test_reverse_route_keeps_story_order():
    reverse = list(reversed(ROUTE))
    assert [ferry_state(reverse, value).stage for value in (0.1, 0.3, 0.5, 0.74, 0.9)] == [
        "approach", "boarding", "sailing", "exiting", "destination"
    ]
