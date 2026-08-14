import numpy as np
import pytest

from routefilm.music import analyze_pcm, normalize_license


@pytest.mark.parametrize(
    ("source", "expected"),
    [("CC BY", "by"), ("CC-BY-SA", "by-sa"), ("Public Domain", "pdm"), ("CC0 1.0", "cc0")],
)
def test_normalize_license(source, expected):
    assert normalize_license(source) == expected


def test_click_track_bpm_estimate():
    sample_rate = 22050
    audio = np.zeros(sample_rate * 12, dtype=np.float32)
    for frame in range(0, len(audio), sample_rate // 2):
        length = min(400, len(audio) - frame)
        audio[frame:frame + length] = np.hanning(length)
    analysis = analyze_pcm(audio, sample_rate)
    assert 115 <= analysis["bpm"] <= 125
    assert len(analysis["beats"]) >= 15
