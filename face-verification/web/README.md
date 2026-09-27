# face-verification web demo

A public demo deploying the face-verification pipeline to Vercel: enroll, 1:1 verify,
and 1:N identify from a browser. See the parent [README](../README.md) for the pipeline
itself; this directory only adds an HTTP layer and swaps in a smaller model pack.

## Why this isn't just `face-verify` on a server

- **Model pack:** uses InsightFace's `buffalo_sc` (`det_500m.onnx` + `w600k_mbf.onnx`,
  ~16MB total) instead of the CLI's default `buffalo_l` (~190MB). Same detector/embedder
  interfaces, same preprocessing conventions, lower accuracy than the full-size models —
  acceptable for a demo, not for production. The two files are committed directly under
  `api/_models/` (small enough that a network fetch at build time isn't worth the fragility).
- **No OpenCV:** the core library's two OpenCV call sites (`detection.resize_with_cv2`,
  `alignment.warp_affine_with_cv2`) are swappable; this app injects a Pillow-based
  implementation instead (`face_verification.pillow_ops`), since OpenCV's installed
  footprint alone would risk exceeding Vercel's serverless function size budget once
  onnxruntime and numpy are also in the bundle.
- **No local disk:** enrollment has to persist across requests, but a serverless function
  has no writable shared disk. `api/_lib/blob_store.py` implements the same
  `EnrollmentStore` interface the CLI's `FileEnrollmentStore` does, backed by Vercel Blob
  instead of the filesystem.
- **Vendored core library:** `api/_vendor/face_verification/` is a copy of the relevant
  modules from `../src/face_verification/`, added to `sys.path` at runtime rather than
  pip-installed. Vercel's Python builder couldn't resolve a `-e ../` editable install of
  the sibling package for this monorepo layout; see `api/_vendor/README.md` for the
  details and how to keep it in sync.

## Architecture

Single FastAPI app (`api/index.py`) with `vercel.json` rewriting all paths to it, so
FastAPI's own routes do the dispatch:

- `GET /` — the demo page (`api/_lib/templates/index.html`)
- `GET /api/health`, `GET /api/gallery`
- `POST /api/enroll` — multipart form: `person_id`, up to 5 `images`
- `POST /api/verify` — multipart form: `person_id`, `image` (1:1)
- `POST /api/identify` — multipart form: `image` (1:N, searches the whole gallery)
- `GET|POST /api/admin/reset` — wipes the gallery; requires `Authorization: Bearer $CRON_SECRET`

`api/_lib/encoder.py` builds the detector/embedder/pipeline once per warm process and
reuses it across invocations. `api/_lib/blob_store.py` talks to Vercel Blob's REST API
directly (no official Python SDK exists for it) — see its docstring for the exact calls.

## This is a public demo, not a product

Anyone can enroll or search this gallery; there's no auth on the demo endpoints. To bound
cost and abuse:

- Uploads are capped at 6MB each, enrollment at 5 images per call, and the gallery at 50
  enrolled identities.
- A daily cron (`vercel.json` → `/api/admin/reset`, protected by `CRON_SECRET`) wipes the
  whole gallery, so nothing is retained long-term.
- The page tells visitors not to upload real photos of real people.

None of this makes it safe for real biometric data — it's a demo of the pipeline, not an
access-control deployment. See the parent README's license caveat too: `buffalo_sc`, like
`buffalo_l`, is InsightFace's non-commercial-research-licensed weights.

## Deploying

Requires a Vercel project with root directory `face-verification/web`,
**`sourceFilesOutsideRootDirectory` enabled** (the build needs the sibling
`face-verification/` package via `-e ../` in requirements.txt), a Blob store connected to
the project (provides `BLOB_READ_WRITE_TOKEN` automatically), and a `CRON_SECRET` env var
(Vercel sends it automatically as `Authorization: Bearer $CRON_SECRET` to cron-triggered
requests once the var is set).

## Local development

```bash
cd face-verification/web
pip install -r requirements.txt
BLOB_READ_WRITE_TOKEN=... CRON_SECRET=... uvicorn api.index:app --reload
```

Without network access to `blob.vercel-storage.com`, storage-dependent routes fail with a
clean `502` (wrapped by `BlobStoreError`) rather than crashing — enough to verify routing,
image decoding, and validation without a live token.
