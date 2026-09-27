"""Tests for CLI argument validation and 1:N wiring."""

import json

import cv2
import numpy as np
import pytest

from face_verification.cli import EXIT_INCONCLUSIVE, EXIT_MATCH, EXIT_NO_MATCH, main
from face_verification.encoder import FaceEncoder
from tests.conftest import PixelEmbedder, StubDetector, face_at


def test_missing_models_reports_error(tmp_path, capsys):
    code = main(
        ["verify", "--models-dir", str(tmp_path), "--person-id", "a", "--image", "x.jpg"]
    )

    assert code == EXIT_INCONCLUSIVE
    assert "download-models" in capsys.readouterr().err


def test_verify_requires_person_id_unless_identify(tmp_path, capsys):
    code = main(["verify", "--models-dir", str(tmp_path), "--image", "x.jpg"])

    assert code == EXIT_INCONCLUSIVE
    assert "--identify" in capsys.readouterr().err


def test_enroll_requires_person_id_or_dataset(tmp_path, capsys):
    code = main(["enroll", "--models-dir", str(tmp_path)])

    assert code == EXIT_INCONCLUSIVE
    assert "--dataset" in capsys.readouterr().err


def test_enroll_rejects_dataset_combined_with_person_id(tmp_path, capsys):
    code = main(
        [
            "enroll",
            "--models-dir",
            str(tmp_path),
            "--person-id",
            "alice",
            "--dataset",
            str(tmp_path),
        ]
    )

    assert code == EXIT_INCONCLUSIVE
    assert "cannot be combined" in capsys.readouterr().err


def _write_face(path, bgr):
    image = np.full((300, 300, 3), bgr, np.uint8)
    cv2.imwrite(str(path), image)


@pytest.fixture
def stub_encoder(monkeypatch):
    """Route the CLI's encoder construction to fakes so no model files are needed."""
    encoder = FaceEncoder(StubDetector([face_at(50, 50)]), PixelEmbedder())
    monkeypatch.setattr("face_verification.cli.build_encoder", lambda models_dir: encoder)


def test_bulk_enroll_and_identify_round_trip(tmp_path, capsys, stub_encoder):
    dataset = tmp_path / "dataset"
    (dataset / "alice").mkdir(parents=True)
    (dataset / "bob").mkdir(parents=True)
    _write_face(dataset / "alice" / "a.jpg", (200, 20, 20))
    _write_face(dataset / "bob" / "b.jpg", (20, 200, 20))
    gallery = tmp_path / "gallery"
    models = tmp_path / "models"

    enroll_code = main(
        [
            "enroll",
            "--models-dir",
            str(models),
            "--gallery-dir",
            str(gallery),
            "--dataset",
            str(dataset),
        ]
    )
    enroll_report = json.loads(capsys.readouterr().out)

    assert enroll_code == 0
    assert {e["person_id"] for e in enroll_report["enrolled"]} == {"alice", "bob"}
    assert enroll_report["errors"] == []

    probe = tmp_path / "probe.jpg"
    _write_face(probe, (20, 200, 20))
    identify_code = main(
        [
            "verify",
            "--models-dir",
            str(models),
            "--gallery-dir",
            str(gallery),
            "--threshold",
            "0.99",
            "--identify",
            "--image",
            str(probe),
        ]
    )
    identify_report = json.loads(capsys.readouterr().out)

    assert identify_code == EXIT_MATCH
    assert identify_report == {
        "status": "match",
        "identified": True,
        "person_id": "bob",
        "score": pytest.approx(1.0),
        "threshold": 0.99,
        "num_candidates": 2,
    }


def test_identify_no_match_returns_exit_1(tmp_path, capsys, stub_encoder):
    gallery = tmp_path / "gallery"
    models = tmp_path / "models"
    enrolled = tmp_path / "alice.jpg"
    _write_face(enrolled, (200, 20, 20))
    main(
        [
            "enroll",
            "--models-dir",
            str(models),
            "--gallery-dir",
            str(gallery),
            "--person-id",
            "alice",
            "--images",
            str(enrolled),
        ]
    )
    capsys.readouterr()

    probe = tmp_path / "probe.jpg"
    _write_face(probe, (20, 20, 200))
    code = main(
        [
            "verify",
            "--models-dir",
            str(models),
            "--gallery-dir",
            str(gallery),
            "--threshold",
            "0.99",
            "--identify",
            "--image",
            str(probe),
        ]
    )

    assert code == EXIT_NO_MATCH
    assert json.loads(capsys.readouterr().out)["status"] == "no_match"
