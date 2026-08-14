from routefilm.renderer import arrival_motion


def test_first_arrival_moves_to_center_holds_and_returns():
    start = arrival_motion(0.0)
    hold = arrival_motion(0.45)
    end = arrival_motion(1.0)

    assert start["center_progress"] == 0.0
    assert hold["center_progress"] == 1.0
    assert hold["scale"] == 2.9
    assert end["center_progress"] == 0.0
    assert end["scale"] == 1.0


def test_repeat_arrival_pulses_without_replaying_center_showcase():
    middle = arrival_motion(0.5, repeated=True)

    assert middle["center_progress"] == 0.0
    assert middle["compact"] is True
    assert middle["scale"] > 1.0
