# face-verification

Offline facial identity verification: a library plus a Vercel demo deployment, laid out
as a small `apps/` + `packages/` monorepo so the app depends on the library as a real
dependency instead of a nested/copied one.

```
face-verification/
  packages/
    face-verification/   the library + CLI — see packages/face-verification/README.md
  apps/
    web/                  the Vercel demo API (enroll / verify / identify) — see apps/web/README.md
    console/              Next.js operator UI that talks to apps/web — see apps/console/README.md
```

`apps/web` depends on `packages/face-verification` via a local, editable `uv` path
dependency (`[tool.uv.sources] face-verification = { path = "../../packages/face-verification",
editable = true }` in `apps/web/pyproject.toml`) — not a workspace (see
`apps/web/README.md` for why a formal `uv` workspace doesn't work with Vercel's Python
builder), and not a vendored copy.

Start with whichever half you're working on:
- **Library/CLI**: `packages/face-verification/README.md`
- **Web demo API**: `apps/web/README.md`
- **Operator UI (Next.js)**: `apps/console/README.md`
