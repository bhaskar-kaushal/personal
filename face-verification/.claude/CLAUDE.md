# face-verification — Claude Code guidance

Offline 1:1/1:N facial identity verification (SCRFD detection → 5-point alignment →
ArcFace embedding → cosine threshold), laid out as `packages/face-verification/` (the
library + CLI) and `apps/web/` (the Vercel demo), following the standard `apps/` +
`packages/` monorepo pattern. See `README.md` for the split and why `apps/web` depends on
the package via a plain `uv` path dependency rather than a formal workspace.

Project-specific rules:
- `packages/face-verification/.claude/conventions.md` — library rules (offline execution,
  embedding/scoring conventions, outcome reporting, biometric data handling, test
  doubles). Takes priority over this file for anything under `packages/face-verification/`.
- `apps/web/README.md` — the demo's own architecture, deployment requirements and
  public-demo safeguards.

## Commands

```bash
cd packages/face-verification
pip install -e ".[cv2,dev]"
pytest -q                                   # no models needed
face-verify download-models [--zip PATH]    # installs models/det_10g.onnx, models/w600k_r50.onnx
face-verify enroll   --person-id ID --images A.jpg B.jpg   # 1:1 enrollment
face-verify enroll   --dataset DIR                          # 1:N bulk enrollment (DIR/<person_id>/*.jpg)
face-verify verify   --person-id ID --image P.jpg           # 1:1 verification
face-verify verify   --identify --image P.jpg               # 1:N search across the gallery
face-verify evaluate --dataset DIR --target-far 1e-3

cd ../../apps/web
uv sync && uv run uvicorn api.index:app --reload
```

## Layout

- `packages/face-verification/src/face_verification/`: the library. Interfaces
  (`FaceDetector`, `FaceEmbedder`, `EnrollmentStore`) are ABCs, and concrete
  implementations are injected into `FaceEncoder` and `VerificationPipeline`.
- `packages/face-verification/tests/`: pytest. Test doubles live in `tests/conftest.py`:
  `FakeSession` stands in for onnxruntime, and there are `StubDetector` and `PixelEmbedder`.
- `packages/face-verification/models/` and `data/`: gitignored — model weights and
  biometric data.
- `apps/web/`: Vercel demo deployment (FastAPI + Blob storage + a smaller model pack). Its
  own `pyproject.toml`/`uv.lock`/`vercel.json`, depending on `face-verification` as a local
  editable path dependency (`uv sync` installs it from `../../packages/face-verification`
  into `apps/web/.venv`) rather than a copy.

## OpenCV is optional

`opencv-python-headless` is the `cv2` extra, not a hard dependency: the two places the core
library touches it (`detection.resize_with_cv2`, `alignment.warp_affine_with_cv2`) are
injectable and default to it, but `pillow_ops.py` (the `pillow` extra) is a drop-in swap for
deployments where OpenCV's footprint doesn't fit. Keep both cv2 imports lazy (inside the
function body, not at module top) so a caller that never uses the default doesn't need
OpenCV installed at all.
