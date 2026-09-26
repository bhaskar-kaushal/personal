# Face Verification

Offline **1:1 facial identity verification** for access control: confirm that the person
presenting at a facility is the registered person they claim to be. There is no 1:N search:
every check is against a single claimed identity's enrolled record.

## Pipeline

```
image ─► SCRFD detector ─► largest face ─► 5-point similarity alignment ─► ArcFace (512-d)
          det_10g.onnx      (subject)       → canonical 112×112 crop          w600k_r50.onnx
                                                                                  │ L2-normalised
claimed person_id ─► enrollment store ─► template (mean of samples, re-normalised) │
                                                                                  ▼
                                               cosine similarity ≥ threshold ? MATCH : NO_MATCH
```

| Module | Responsibility |
|---|---|
| `detection.py` | `FaceDetector` ABC; `ScrfdDetector` with its own anchor decoding and NMS on onnxruntime |
| `alignment.py` | Umeyama similarity transform onto the ArcFace 5-point template; `align_face` |
| `embedding.py` | `FaceEmbedder` ABC; `OnnxArcFaceEmbedder` (RGB, `(x-127.5)/127.5`, unit-norm output) |
| `encoder.py` | image → embedding of the largest face (bystanders ignored) |
| `gallery.py` | `EnrollmentStore` ABC; `FileEnrollmentStore` (`<person_id>.npz`, no pickle, atomic writes) |
| `verification.py` | `ThresholdVerifier`, `VerificationResult`, `VerificationStatus` |
| `pipeline.py` | `VerificationPipeline.enroll / verify` (all dependencies injected) |
| `evaluation.py` | FAR/FRR, EER, threshold for a target FAR, TAR@FAR, all-pairs scoring |
| `model_download.py` | the **only** networked code: one-time model install with SHA-256 check |

Every outcome is reported explicitly: `match`, `no_match`, `no_face`, `not_enrolled`.
A missing face or a missing enrollment is never reported as a low-score mismatch.

## Setup

```bash
cd face-verification
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
face-verify download-models                        # online, once
face-verify download-models --zip /path/buffalo_l.zip   # air-gapped alternative
```

After the models are installed, no step uses the network. Everything runs on the CPU through
`onnxruntime`.

## Usage

```bash
face-verify enroll --person-id alice --images alice_1.jpg alice_2.jpg
face-verify verify --person-id alice --image probe.jpg
# {"person_id": "alice", "status": "match", "verified": true, "score": 0.93, "threshold": 0.4}
# exit code: 0 match, 1 no match, 2 inconclusive (no face / not enrolled / bad input)

face-verify evaluate --dataset data/eval --target-far 1e-3 --output data/eval_report.json
```

`evaluate` expects `<dataset>/<person_id>/*.jpg`. It scores every pair of images. It then
reports FAR/FRR at `--threshold`, the EER, and the lowest threshold that meets `--target-far`,
together with the TAR at that threshold.

Defaults: models are read from `models/`, the gallery is kept in `data/gallery/` and the
threshold is `0.40`. Both directories are gitignored because they hold model weights and
biometric data.

## Threshold

`0.40` cosine is a common starting operating point for `w600k_r50`. It is **not calibrated
for your population, cameras or lighting.** Before deployment, collect a labelled in-house
evaluation set and run `evaluate` with the FAR your security policy requires, such as `1e-4`.
Then set `--threshold` to the reported `threshold_at_target_far`. Keep in mind that a FAR
estimate is only meaningful with many more impostor pairs than 1/FAR.

## Smoke-test results

On six faces cropped from InsightFace's sample image `t1.jpg`, each with five variants
(original, flipped, brightened, rotated 12° and blurred):

- genuine variants scored 0.93–0.98
- other people scored about 0.1 or lower
- FAR and FRR were both 0 at 0.40

This data is synthetic and far too small to be a benchmark. It only confirms that
preprocessing, alignment and decoding are correct.

## License caveat

The pretrained InsightFace `buffalo_l` weights are released for **non-commercial research
only**. An organizational or commercial deployment needs either a commercially licensed
ArcFace-class ONNX model or a model trained in-house. Because the embedder sits behind
`FaceEmbedder`, replacing it means supplying a different ONNX file.

## Development

```bash
pytest -q        # unit tests use fakes and need no model files
```

## Roadmap

- Identity drift detection. Each enrollment sample already stores `enrolled_at`. The next
  step is to track verification scores against the template over time and flag people who
  need to re-enroll.
