# face-verification — Claude Code guidance

Offline 1:1 facial identity verification (SCRFD detection → 5-point alignment → ArcFace
embedding → cosine threshold). See `README.md` for the architecture and CLI.
Project rules are in `conventions.md` and take priority over the repo-wide `.claude/CLAUDE.md`.

## Commands (run from `face-verification/`)

```bash
pip install -e ".[dev]"
pytest -q                                   # no models needed
face-verify download-models [--zip PATH]    # installs models/det_10g.onnx, models/w600k_r50.onnx
face-verify enroll   --person-id ID --images A.jpg B.jpg   # 1:1 enrollment
face-verify enroll   --dataset DIR                          # 1:N bulk enrollment (DIR/<person_id>/*.jpg)
face-verify verify   --person-id ID --image P.jpg           # 1:1 verification
face-verify verify   --identify --image P.jpg               # 1:N search across the gallery
face-verify evaluate --dataset DIR --target-far 1e-3
```

## Layout

- `src/face_verification/`: the library. Interfaces (`FaceDetector`, `FaceEmbedder`,
  `EnrollmentStore`) are ABCs, and concrete implementations are injected into
  `FaceEncoder` and `VerificationPipeline`.
- `tests/`: pytest. Test doubles live in `tests/conftest.py`: `FakeSession` stands in for
  onnxruntime, and there are `StubDetector` and `PixelEmbedder`.
- `models/` and `data/`: gitignored because they hold model weights and biometric data.
