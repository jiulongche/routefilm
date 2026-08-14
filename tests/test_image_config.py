import os
import stat
from pathlib import Path

from routefilm.image_config import configure_image_environment, resolve_image_credentials


def test_dotenv_resolves_without_mutating_process_environment(tmp_path: Path, monkeypatch):
    config = tmp_path / ".env"
    config.write_text(
        "ROUTEFILM_IMAGE_BASE_URL=https://images.example/v1\n"
        "ROUTEFILM_IMAGE_API_KEY=file-secret\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ROUTEFILM_ENV_FILE", str(config))
    monkeypatch.delenv("ROUTEFILM_IMAGE_BASE_URL", raising=False)
    monkeypatch.delenv("ROUTEFILM_IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert resolve_image_credentials() == ("https://images.example/v1", "file-secret")
    assert "ROUTEFILM_IMAGE_BASE_URL" not in os.environ
    assert "ROUTEFILM_IMAGE_API_KEY" not in os.environ


def test_process_environment_takes_precedence_over_dotenv(tmp_path: Path, monkeypatch):
    config = tmp_path / ".env"
    config.write_text(
        "ROUTEFILM_IMAGE_BASE_URL=https://file.example/v1\n"
        "ROUTEFILM_IMAGE_API_KEY=file-secret\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ROUTEFILM_ENV_FILE", str(config))
    monkeypatch.setenv("ROUTEFILM_IMAGE_BASE_URL", "https://process.example/v1")
    monkeypatch.setenv("ROUTEFILM_IMAGE_API_KEY", "process-secret")

    assert resolve_image_credentials() == ("https://process.example/v1", "process-secret")


def test_configure_creates_private_file_and_preserves_existing_values(tmp_path: Path):
    config = tmp_path / ".env"
    config.write_text("OTHER_SETTING=keep-me\n", encoding="utf-8")

    output = configure_image_environment(
        "https://api.openai.com/v1/", scope="project", cwd=tmp_path
    )

    text = output.read_text(encoding="utf-8")
    assert "OTHER_SETTING=keep-me" in text
    assert "ROUTEFILM_IMAGE_BASE_URL=https://api.openai.com/v1" in text
    assert "ROUTEFILM_IMAGE_API_KEY=" in text
    assert stat.S_IMODE(output.stat().st_mode) == 0o600


def test_configure_rejects_non_http_endpoint(tmp_path: Path):
    try:
        configure_image_environment("file:///secret", scope="project", cwd=tmp_path)
    except ValueError as error:
        assert "http(s)" in str(error)
    else:
        raise AssertionError("unsafe endpoint was accepted")


def test_configure_rejects_credentials_embedded_in_url(tmp_path: Path):
    try:
        configure_image_environment(
            "https://user:secret@images.example/v1", scope="project", cwd=tmp_path
        )
    except ValueError as error:
        assert "must not be embedded" in str(error)
    else:
        raise AssertionError("URL credentials were accepted")


def test_configure_reuses_existing_process_endpoint(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ROUTEFILM_IMAGE_BASE_URL", "https://existing.example/v1")

    output = configure_image_environment(scope="project", cwd=tmp_path)

    assert "ROUTEFILM_IMAGE_BASE_URL=https://existing.example/v1" in output.read_text(
        encoding="utf-8"
    )
