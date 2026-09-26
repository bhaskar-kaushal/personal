"""Command-line interface: download-models, enroll, verify, evaluate."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

from face_verification.detection import ScrfdDetector
from face_verification.embedding import OnnxArcFaceEmbedder
from face_verification.encoder import FaceEncoder
from face_verification.evaluation import evaluate
from face_verification.gallery import FileEnrollmentStore
from face_verification.image_io import list_images, load_image
from face_verification.model_download import (
    DETECTOR_FILENAME,
    EMBEDDER_FILENAME,
    install_models,
)
from face_verification.pipeline import VerificationPipeline
from face_verification.verification import (
    DEFAULT_THRESHOLD,
    ThresholdVerifier,
    VerificationStatus,
)

DEFAULT_MODELS_DIR = Path("models")
DEFAULT_GALLERY_DIR = Path("data/gallery")
DEFAULT_TARGET_FAR = 1e-3

EXIT_MATCH = 0
EXIT_NO_MATCH = 1
EXIT_INCONCLUSIVE = 2


def build_encoder(models_dir: Path) -> FaceEncoder:
    """
    Construct the detector + embedder encoder from a local models directory.

    Raises:
        FileNotFoundError: If a model file is missing.
    """
    paths = [models_dir / DETECTOR_FILENAME, models_dir / EMBEDDER_FILENAME]
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing model files: {', '.join(missing)}. Run `face-verify download-models` first."
        )
    return FaceEncoder(ScrfdDetector.from_path(paths[0]), OnnxArcFaceEmbedder.from_path(paths[1]))


def _build_pipeline(args: argparse.Namespace) -> VerificationPipeline:
    return VerificationPipeline(
        encoder=build_encoder(args.models_dir),
        store=FileEnrollmentStore(args.gallery_dir),
        verifier=ThresholdVerifier(args.threshold),
    )


def _cmd_download_models(args: argparse.Namespace) -> int:
    install_models(args.models_dir, args.zip)
    print(f"Installed {DETECTOR_FILENAME} and {EMBEDDER_FILENAME} into {args.models_dir}")
    return 0


def _cmd_enroll(args: argparse.Namespace) -> int:
    pipeline = _build_pipeline(args)
    images = [(path.name, load_image(path)) for path in args.images]
    record = pipeline.enroll(args.person_id, images)
    print(json.dumps({"person_id": record.person_id, "num_samples": len(record.samples)}))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    result = _build_pipeline(args).verify(args.person_id, load_image(args.image))
    print(json.dumps(result.to_dict()))
    if result.status is VerificationStatus.MATCH:
        return EXIT_MATCH
    if result.status is VerificationStatus.NO_MATCH:
        return EXIT_NO_MATCH
    return EXIT_INCONCLUSIVE


def _cmd_evaluate(args: argparse.Namespace) -> int:
    encoder = build_encoder(args.models_dir)
    embeddings: Dict[str, List[np.ndarray]] = {}
    skipped: List[str] = []
    for person_dir in sorted(p for p in args.dataset.iterdir() if p.is_dir()):
        for image_path in list_images(person_dir):
            embedding = encoder.encode(load_image(image_path))
            if embedding is None:
                skipped.append(str(image_path))
            else:
                embeddings.setdefault(person_dir.name, []).append(embedding)

    report = evaluate(embeddings, threshold=args.threshold, target_far=args.target_far).to_dict()
    report["skipped_no_face"] = skipped
    output = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n")
    print(output)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="face-verify", description="Offline 1:1 facial identity verification."
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--models-dir", type=Path, default=DEFAULT_MODELS_DIR)
    scoring = argparse.ArgumentParser(add_help=False)
    scoring.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    gallery = argparse.ArgumentParser(add_help=False)
    gallery.add_argument("--gallery-dir", type=Path, default=DEFAULT_GALLERY_DIR)

    commands = parser.add_subparsers(dest="command", required=True)

    download = commands.add_parser(
        "download-models", parents=[common], help="Install buffalo_l detector + embedder."
    )
    download.add_argument("--zip", type=Path, help="Local buffalo_l.zip (skips download).")
    download.set_defaults(handler=_cmd_download_models)

    enroll = commands.add_parser(
        "enroll", parents=[common, scoring, gallery], help="Enroll images for a person."
    )
    enroll.add_argument("--person-id", required=True)
    enroll.add_argument("--images", type=Path, nargs="+", required=True)
    enroll.set_defaults(handler=_cmd_enroll)

    verify = commands.add_parser(
        "verify",
        parents=[common, scoring, gallery],
        help="Verify an image against a claimed identity (exit 0 match, 1 no match, 2 inconclusive).",
    )
    verify.add_argument("--person-id", required=True)
    verify.add_argument("--image", type=Path, required=True)
    verify.set_defaults(handler=_cmd_verify)

    evaluation = commands.add_parser(
        "evaluate",
        parents=[common, scoring],
        help="All-pairs FAR/FRR/EER on a <dataset>/<person_id>/*.jpg folder.",
    )
    evaluation.add_argument("--dataset", type=Path, required=True)
    evaluation.add_argument("--target-far", type=float, default=DEFAULT_TARGET_FAR)
    evaluation.add_argument("--output", type=Path, help="Also write the JSON report here.")
    evaluation.set_defaults(handler=_cmd_evaluate)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    CLI entry point.

    Args:
        argv: Arguments (defaults to sys.argv[1:]).

    Returns:
        Process exit code.
    """
    args = _build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_INCONCLUSIVE


if __name__ == "__main__":
    raise SystemExit(main())
