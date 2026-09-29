"""
Demo API for face-verification: enroll, verify (1:1) and identify (1:N).

This is a public, unauthenticated demo. It deliberately runs a smaller model
pack (buffalo_sc) than the CLI's default (buffalo_l) to fit a serverless
function's size budget, and caps upload size and gallery size to bound cost
and abuse. See README.md for the full set of caveats.
"""

import io
import os
from typing import List, Optional

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Header, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from face_verification.pipeline import NoFaceDetectedError
from face_verification.verification import IdentificationStatus, VerificationStatus

from api._lib.blob_store import BlobStoreError
from api._lib.encoder import get_pipeline, get_store

MAX_IMAGE_BYTES = 6 * 1024 * 1024
MAX_IMAGES_PER_ENROLL = 5
MAX_GALLERY_SIZE = 50

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "_lib", "templates", "index.html")

app = FastAPI(title="face-verification demo")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as handle:
        return handle.read()


@app.get("/api/health")
def health() -> dict:
    try:
        gallery_size = len(get_store().list_ids())
    except BlobStoreError:
        gallery_size = None
    return {"status": "ok", "gallery_size": gallery_size}


@app.get("/api/gallery")
def gallery() -> dict:
    ids = get_store().list_ids()
    return {"person_ids": ids, "count": len(ids)}


async def _decode_upload(upload: UploadFile) -> np.ndarray:
    data = await upload.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, f"{upload.filename}: exceeds {MAX_IMAGE_BYTES // (1024 * 1024)}MB limit")
    try:
        from PIL import Image, UnidentifiedImageError

        image = Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(400, f"{upload.filename}: not a readable image ({error})") from error
    return np.asarray(image)[:, :, ::-1]  # RGB -> BGR, the library's convention


@app.post("/api/enroll")
async def enroll(person_id: str = Form(...), images: List[UploadFile] = File(...)) -> dict:
    if not images:
        raise HTTPException(400, "At least one image is required")
    if len(images) > MAX_IMAGES_PER_ENROLL:
        raise HTTPException(400, f"At most {MAX_IMAGES_PER_ENROLL} images per enrollment")

    pipeline = get_pipeline()
    existing_ids = set(get_store().list_ids())
    if person_id not in existing_ids and len(existing_ids) >= MAX_GALLERY_SIZE:
        raise HTTPException(507, f"Demo gallery is full (max {MAX_GALLERY_SIZE} people)")

    decoded = [(upload.filename or "upload.jpg", await _decode_upload(upload)) for upload in images]
    try:
        record = pipeline.enroll(person_id, decoded)
    except NoFaceDetectedError as error:
        raise HTTPException(422, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except BlobStoreError as error:
        raise HTTPException(502, f"Storage error: {error}") from error
    return {"person_id": record.person_id, "num_samples": len(record.samples)}


@app.post("/api/verify")
async def verify(person_id: str = Form(...), image: UploadFile = File(...)) -> dict:
    decoded = await _decode_upload(image)
    try:
        result = get_pipeline().verify(person_id, decoded)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except BlobStoreError as error:
        raise HTTPException(502, f"Storage error: {error}") from error
    body = result.to_dict()
    status_code = 200 if result.status is not VerificationStatus.NOT_ENROLLED else 404
    return JSONResponse(body, status_code=status_code)


@app.post("/api/identify")
async def identify(image: UploadFile = File(...)) -> dict:
    decoded = await _decode_upload(image)
    try:
        result = get_pipeline().identify(decoded)
    except BlobStoreError as error:
        raise HTTPException(502, f"Storage error: {error}") from error
    body = result.to_dict()
    status_code = 200 if result.status is not IdentificationStatus.EMPTY_GALLERY else 404
    return JSONResponse(body, status_code=status_code)


@app.api_route("/api/admin/reset", methods=["GET", "POST"])
def admin_reset(authorization: Optional[str] = Header(None)) -> dict:
    """Wipe the demo gallery. Called daily by Vercel Cron; also usable manually with the same secret."""
    expected = os.environ.get("CRON_SECRET")
    if not expected or authorization != f"Bearer {expected}":
        raise HTTPException(401, "Unauthorized")
    try:
        removed = get_store().delete_all()
    except BlobStoreError as error:
        raise HTTPException(502, f"Storage error: {error}") from error
    return {"removed": removed}
