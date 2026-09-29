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
- **Local path dependency, not a copy:** `web/pyproject.toml` depends on `face-verification`
  via `[tool.uv.sources] face-verification = { path = "..", editable = true }` — a real,
  editable install of the sibling package, not a vendored copy. Two things were tried
  first and didn't work: a bare `-e ../` in `requirements.txt` (Vercel's `uv` resolved the
  relative path against the wrong root — `Distribution not found at:
  .../face-verification/web/face-verification`), and a formal `uv` **workspace**
  (`{ workspace = true }`), which built fine but crashed at runtime with
  `ModuleNotFoundError: No module named 'fastapi'` — `uv` workspaces always place a single
  shared venv at the workspace *root* (`face-verification/.venv`), outside this function's
  own `rootDirectory`, so Vercel's bundler never saw it. A plain path source keeps the venv
  local to `web/.venv`, which is what actually gets bundled.

## Architecture

Single FastAPI app (`api/index.py`). Vercel auto-detects it (`framework: "fastapi"` in
the project) and routes every path to it directly, preserving the original request
path — so FastAPI's own `@app.get`/`@app.post` routes do the dispatch with no
`vercel.json` rewrite needed. (A manual `/(.*) -> /api/index` rewrite was tried first and
broke every route: it rewrites the *path itself* to the literal string `/api/index`
before the app sees it, so `/api/health` arrives as a request for `/api/index`, which
matches nothing.)

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
**`sourceFilesOutsideRootDirectory` enabled** (the build needs filesystem access to the
sibling `face-verification/` package for the path dependency above), a Blob store
connected to the project (provides `BLOB_READ_WRITE_TOKEN` automatically), and a
`CRON_SECRET` env var (Vercel sends it automatically as `Authorization: Bearer
$CRON_SECRET` to cron-triggered requests once the var is set).

## Local development

```bash
cd face-verification/web
uv sync   # installs face-verification editable from ../, plus fastapi etc. into web/.venv
BLOB_READ_WRITE_TOKEN=... CRON_SECRET=... uv run uvicorn api.index:app --reload
```

Without network access to `blob.vercel-storage.com`, storage-dependent routes fail with a
clean `502` (wrapped by `BlobStoreError`) rather than crashing — enough to verify routing,
image decoding, and validation without a live token.
