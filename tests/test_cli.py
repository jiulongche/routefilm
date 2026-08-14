import json

import pytest

from routefilm.cli import main


def test_cli_reports_expected_user_error_without_traceback(capsys):
    with pytest.raises(SystemExit) as raised:
        main(["fetch", "missing-project.yaml"])

    assert raised.value.code == 2
    error = capsys.readouterr().err
    assert error.startswith("routefilm: error:")
    assert "Traceback" not in error


def test_image_configure_prepares_project_dotenv(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ROUTEFILM_IMAGE_BASE_URL", raising=False)
    monkeypatch.delenv("ROUTEFILM_IMAGE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ROUTEFILM_ENV_FILE", raising=False)

    assert main(
        [
            "image",
            "configure",
            "--base-url",
            "https://api.openai.com/v1",
            "--scope",
            "project",
        ]
    ) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["config_path"] == str(tmp_path / ".env")
    assert result["url_configured"] is True
    assert result["key_configured"] is False
    assert "set ROUTEFILM_IMAGE_API_KEY" in result["next_step"]
