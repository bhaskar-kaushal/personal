"""
`EnrollmentStore` backed by Vercel Blob.

A serverless function has no writable, shared local disk, so the file-based
`FileEnrollmentStore` the CLI uses doesn't work here. This stores each person
as one JSON blob at `gallery/<person_id>.json`, upserted in place (Blob's
random-suffix behaviour is disabled so the pathname stays stable), via raw
calls to Blob's REST API (no official Python SDK exists for it).
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from typing import List, Optional, Sequence

import numpy as np

from face_verification.gallery import (
    EnrollmentRecord,
    EnrollmentSample,
    EnrollmentStore,
    validate_person_id,
)

BLOB_API_BASE = "https://blob.vercel-storage.com"
API_VERSION = "7"
GALLERY_PREFIX = "gallery/"
REQUEST_TIMEOUT_SECONDS = 15


class BlobStoreError(RuntimeError):
    """A Vercel Blob API call failed; the message includes the response body."""


class BlobEnrollmentStore(EnrollmentStore):
    """One JSON blob per person, addressed by a deterministic pathname."""

    def __init__(self, token: Optional[str] = None):
        """
        Args:
            token: Blob read/write token; defaults to the BLOB_READ_WRITE_TOKEN
                env var Vercel injects once a Blob store is connected to the project.
        """
        self._token = token or os.environ["BLOB_READ_WRITE_TOKEN"]

    def get(self, person_id: str) -> Optional[EnrollmentRecord]:
        """See EnrollmentStore.get."""
        pathname = self._pathname(person_id)
        listing = self._list(prefix=pathname)
        matches = [blob for blob in listing if blob["pathname"] == pathname]
        if not matches:
            return None
        payload = json.loads(self._get(matches[0]["url"]))
        samples = [
            EnrollmentSample(
                embedding=np.array(sample["embedding"], dtype=np.float32),
                enrolled_at=datetime.fromisoformat(sample["enrolled_at"]),
                source=sample["source"],
            )
            for sample in payload["samples"]
        ]
        return EnrollmentRecord(person_id=person_id, samples=samples)

    def add_samples(self, person_id: str, samples: Sequence[EnrollmentSample]) -> EnrollmentRecord:
        """See EnrollmentStore.add_samples."""
        if not samples:
            raise ValueError("No samples to enroll")
        record = self.get(person_id) or EnrollmentRecord(person_id=validate_person_id(person_id))
        record.samples.extend(samples)
        body = json.dumps(
            {
                "samples": [
                    {
                        "embedding": sample.embedding.tolist(),
                        "enrolled_at": sample.enrolled_at.isoformat(),
                        "source": sample.source,
                    }
                    for sample in record.samples
                ]
            }
        ).encode("utf-8")
        self._put(self._pathname(person_id), body)
        return record

    def list_ids(self) -> List[str]:
        """See EnrollmentStore.list_ids."""
        ids = [
            blob["pathname"][len(GALLERY_PREFIX) : -len(".json")] for blob in self._list(GALLERY_PREFIX)
        ]
        return sorted(ids)

    def delete_all(self) -> int:
        """Admin operation: delete every enrolled record. Returns the number removed."""
        urls = [blob["url"] for blob in self._list(GALLERY_PREFIX)]
        if urls:
            self._request(
                "POST",
                f"{BLOB_API_BASE}/delete",
                data=json.dumps({"urls": urls}).encode("utf-8"),
                headers={"content-type": "application/json"},
            )
        return len(urls)

    def _pathname(self, person_id: str) -> str:
        return f"{GALLERY_PREFIX}{validate_person_id(person_id)}.json"

    def _list(self, prefix: str) -> List[dict]:
        return json.loads(self._request("GET", f"{BLOB_API_BASE}?prefix={prefix}")).get("blobs", [])

    def _get(self, url: str) -> bytes:
        return self._request("GET", url)

    def _put(self, pathname: str, body: bytes) -> None:
        self._request(
            "PUT",
            f"{BLOB_API_BASE}/{pathname}",
            data=body,
            headers={"x-content-type": "application/json", "x-add-random-suffix": "0"},
        )

    def _request(
        self, method: str, url: str, *, data: Optional[bytes] = None, headers: Optional[dict] = None
    ) -> bytes:
        request_headers = {"authorization": f"Bearer {self._token}", "x-api-version": API_VERSION}
        request_headers.update(headers or {})
        request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise BlobStoreError(f"{method} {url} -> {error.code}: {body}") from error
        except urllib.error.URLError as error:
            raise BlobStoreError(f"{method} {url} -> {error.reason}") from error
