# face-verification conventions

These rules extend the repo-wide `.claude/CLAUDE.md` (OOP/SOLID, type hints, Google docstrings).

## Offline execution
- Runtime code never touches the network. `model_download.py` is the only module allowed to.
- Model files are loaded from explicit local paths and are never downloaded implicitly.

## Embeddings and scoring
- Embeddings are always L2-normalised float32. Templates are the re-normalised mean of samples.
- Scores are cosine similarity in [-1, 1]. A claim is accepted when `score >= threshold`.
- Alignment always targets `ARCFACE_TEMPLATE_112`. Any new embedder must accept that crop.

## Outcomes
- Report `NO_FACE` and `NOT_ENROLLED` explicitly. Never turn them into a low score or a `NO_MATCH`.
- Enrollment is all-or-nothing per person: if any image has no face, nothing is stored for
  that person. Bulk (`--dataset`) enrollment applies this per person and continues past a
  failed person rather than aborting the whole batch.
- `identify` (1:N) reports `EMPTY_GALLERY` and `NO_FACE` explicitly, same as `verify` does for
  `NOT_ENROLLED`/`NO_FACE`. It is a linear scan over the gallery, not an indexed search.

## Biometric data
- Never commit images, galleries, embeddings or evaluation reports. Keep them under `data/`.
- Person ids must pass `validate_person_id` because they become file names.
- Store with `np.savez` and load with `allow_pickle=False`.

## Tests
- Unit tests must run without model files. Use `FakeSession`, `StubDetector` and `PixelEmbedder`.
- Real-model checks are manual smoke tests (see README) and are not part of `pytest`.
