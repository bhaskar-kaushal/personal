# Vendored `face_verification`

A copy of the relevant modules from `../../../src/face_verification/` (the CLI-only
modules — `cli.py`, `image_io.py`, `model_download.py`, `evaluation.py`, `__main__.py` —
are omitted; the web app doesn't use them).

## Why a copy instead of a proper install

Vercel's Python builder (`uv`) failed to resolve `-e ../` as an editable install of the
sibling `face-verification` package: it treated the relative path as rooted somewhere
other than `web/`, producing `Distribution not found at:
.../face-verification/web/face-verification`. Rather than fight that path resolution
(and risk the module also not surviving into the runtime bundle, since files outside a
Python function's own directory aren't guaranteed to be included even when the build
step can see them), this vendors the source directly under `api/`, which is definitely
part of the function's bundle, and adds it to `sys.path` at runtime
(`api/index.py`, top of the file) instead of installing it as a package. This mirrors
the `sys.path`-based cross-project import already used elsewhere in this monorepo (see
root `CLAUDE.md`'s note on how `conversational-rag` reuses `basic-rag`).

## Keeping it in sync

This is a manual copy, not a build step, so it can drift from the source of truth. When
you change `alignment.py`, `detection.py`, `embedding.py`, `encoder.py`, `gallery.py`,
`pillow_ops.py`, `pipeline.py`, `similarity.py`, `verification.py`, or `__init__.py` in
`face-verification/src/face_verification/`, re-copy the same files here:

```bash
cp face-verification/src/face_verification/{__init__,alignment,detection,embedding,encoder,gallery,pillow_ops,pipeline,similarity,verification}.py \
   face-verification/web/api/_vendor/face_verification/
```
