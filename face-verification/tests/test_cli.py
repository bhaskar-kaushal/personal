"""Tests for CLI error handling."""

from face_verification.cli import EXIT_INCONCLUSIVE, main


def test_missing_models_reports_error(tmp_path, capsys):
    code = main(
        ["verify", "--models-dir", str(tmp_path), "--person-id", "a", "--image", "x.jpg"]
    )

    assert code == EXIT_INCONCLUSIVE
    assert "download-models" in capsys.readouterr().err
