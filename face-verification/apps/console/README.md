# FaceGate console

Operator UI for the face-verification service: 1:1 access checks, 1:N identification,
enrollment (with consent capture), a directory of enrolled people and a local activity log.
Next.js (App Router) + React, no UI framework, deployable to Vercel.

It is a pure front end. `next.config.mjs` rewrites `/api/*` to the FastAPI service in
[`../web`](../web/README.md) (`BACKEND_URL`), so the browser talks to a single origin and
no CORS setup is needed. The two are separate Vercel projects.

## Screens

| Route | Purpose |
|---|---|
| `/` | KPIs (gallery vs. capacity, granted / denied / inconclusive) and recent activity |
| `/verify` | 1:1 check: claimed ID + webcam or upload → granted / denied / inconclusive with score-vs-threshold gauge |
| `/identify` | 1:N search across the gallery |
| `/enroll` | Up to 5 photos, ID validation, explicit consent, duplicate-ID confirmation |
| `/directory` | Searchable list of enrolled people |
| `/activity` | Filterable audit trail with CSV export |
| `/about` | Decision method, operating parameters, pre-production checklist |

Behaviour that matters for a biometric UI: no-face and not-enrolled are shown as
*inconclusive*, never as a mismatch; images are downscaled client-side and never stored;
the activity log keeps outcomes and scores only (in `localStorage`, not tamper-evident).

## Local development

```bash
# terminal 1: the API (see ../web/README.md)
cd ../web && uv sync && BLOB_READ_WRITE_TOKEN=... uv run uvicorn api.index:app --reload
# terminal 2: the console
cd apps/console && cp .env.example .env.local && npm install && npm run dev
npm test        # unit tests (node:test)
```

The camera needs a secure context: `localhost` or HTTPS.

## Deploying to Vercel

Create a second Vercel project with root directory `face-verification/apps/console`
(framework: Next.js) and set `BACKEND_URL` to the deployed `apps/web` URL.
