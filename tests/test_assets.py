import base64
import io
import json

import pytest
from PIL import Image

from routefilm.assets import (
    builtin_ferry,
    builtin_marker,
    default_arrow,
    generate_vehicle,
    image_api_status,
    landmark_prompt,
    remove_background,
)


def test_default_arrow_has_transparency_and_visible_pixels():
    image = default_arrow(192)
    alpha = image.getchannel("A")
    assert alpha.getextrema() == (0, 255)
    assert alpha.getbbox() is not None


def test_bundled_marker_presets_and_ferry_have_transparency():
    for image in (builtin_marker("arrow"), builtin_marker("black-suv"), builtin_ferry()):
        assert image.mode == "RGBA"
        alpha = image.getchannel("A")
        assert alpha.getbbox() is not None
        assert alpha.getextrema()[0] == 0


def test_chroma_cutout_removes_green_background():
    image = Image.new("RGB", (64, 64), (0, 255, 0))
    for x in range(20, 44):
        for y in range(24, 40):
            image.putpixel((x, y), (10, 10, 10))
    result = remove_background(image, "chroma")
    assert result.getchannel("A").getextrema() == (255, 255)
    assert result.size == (24, 16)


def test_chroma_cutout_handles_shaded_green_background():
    image = Image.new("RGB", (80, 80), (3, 248, 16))
    for x in range(80):
        for y in range(80):
            image.putpixel((x, y), (3 + x // 8, 248 - y // 10, 16 + y // 8))
    for x in range(22, 58):
        for y in range(30, 50):
            image.putpixel((x, y), (218, 164, 53))

    result = remove_background(image, "chroma")
    alpha = result.getchannel("A")
    assert alpha.getpixel((result.width // 2, result.height // 2)) == 255
    assert result.size == (36, 20)


def test_image_generation_requires_both_url_and_key(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("ROUTEFILM_IMAGE_BASE_URL", raising=False)
    monkeypatch.delenv("ROUTEFILM_IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert image_api_status()["generation_enabled"] is False

    monkeypatch.setenv("ROUTEFILM_IMAGE_BASE_URL", "https://images.example/v1")
    status = image_api_status()
    assert status["url_configured"] is True
    assert status["key_configured"] is False
    with pytest.raises(RuntimeError, match="URL and key"):
        generate_vehicle("test", tmp_path / "vehicle.png")


def test_image_status_never_returns_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ROUTEFILM_IMAGE_BASE_URL", "https://images.example/v1")
    monkeypatch.setenv("ROUTEFILM_IMAGE_API_KEY", "secret-value")

    status = image_api_status()

    assert status["generation_enabled"] is True
    assert "secret-value" not in repr(status)
    assert "images.example" not in repr(status)


def test_generation_record_omits_endpoint_and_absolute_paths(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    source = Image.new("RGB", (24, 24), (0, 255, 0))
    for x in range(7, 17):
        for y in range(8, 16):
            source.putpixel((x, y), (20, 20, 20))
    buffer = io.BytesIO()
    source.save(buffer, format="PNG")
    response_payload = json.dumps(
        {"data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode()}]}
    ).encode()

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return response_payload

    monkeypatch.setattr("routefilm.assets.urllib.request.urlopen", lambda *_a, **_k: Response())
    output, record = generate_vehicle(
        "test", tmp_path / "vehicle.png", base_url="https://private.example/v1", api_key="secret"
    )

    metadata = json.loads(record.read_text(encoding="utf-8"))
    assert metadata["endpoint_configured"] is True
    assert "base_url" not in metadata
    assert metadata["raw"] == "vehicle-chroma.png"
    assert metadata["output"] == output.name
    assert str(tmp_path) not in record.read_text(encoding="utf-8")
    assert "private.example" not in record.read_text(encoding="utf-8")


def test_landmark_prompt_keeps_names_out_of_rendered_text():
    prompt = landmark_prompt("杭州", "西湖")
    assert "杭州" in prompt and "西湖" in prompt
    assert "No city name" in prompt
