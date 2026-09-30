export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(url, options) {
  let res;
  try {
    res = await fetch(url, options);
  } catch {
    throw new ApiError("Cannot reach the service. Check your connection and try again.", 0);
  }
  let body = null;
  try { body = await res.json(); } catch { /* non-JSON error page */ }
  return { res, body };
}

export function errorText(res, body) {
  const detail = body && body.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  if (res.status === 413) return "Image is too large.";
  if (res.status >= 500) return "The service had a problem. Please retry shortly.";
  return `Request failed (${res.status}).`;
}

/** Verify/identify answer 404 with a valid decision body for not_enrolled / empty_gallery. */
async function decision(url, form) {
  const { res, body } = await request(url, { method: "POST", body: form });
  if (body && typeof body.status === "string") return body;
  throw new ApiError(errorText(res, body), res.status);
}

export async function getHealth() {
  const { res, body } = await request("/api/health");
  if (!res.ok || !body) throw new ApiError("unhealthy", res.status);
  return body;
}

export async function getGallery() {
  const { res, body } = await request("/api/gallery");
  if (!res.ok) throw new ApiError(errorText(res, body), res.status);
  return body;
}

export async function enroll(personId, blobs) {
  const fd = new FormData();
  fd.append("person_id", personId);
  blobs.forEach((b, i) => fd.append("images", b, `capture-${i + 1}.jpg`));
  const { res, body } = await request("/api/enroll", { method: "POST", body: fd });
  if (!res.ok) throw new ApiError(errorText(res, body), res.status);
  return body;
}

export function verify(personId, blob) {
  const fd = new FormData();
  fd.append("person_id", personId);
  fd.append("image", blob, "probe.jpg");
  return decision("/api/verify", fd);
}

export function identify(blob) {
  const fd = new FormData();
  fd.append("image", blob, "probe.jpg");
  return decision("/api/identify", fd);
}
