import pytest

from routefilm.cli import main


def test_cli_reports_expected_user_error_without_traceback(capsys):
    with pytest.raises(SystemExit) as raised:
        main(["fetch", "missing-project.yaml"])

    assert raised.value.code == 2
    error = capsys.readouterr().err
    assert error.startswith("routefilm: error:")
    assert "Traceback" not in error
