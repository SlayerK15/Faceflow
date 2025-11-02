# Faceflow Web Frontend

A minimal Next.js 15 app that interacts with the FastAPI demo backend. The UI focuses on the album → upload → cluster flow and proxies all API requests to `http://localhost:8000` via `next.config.mjs` rewrites.

## Getting started

```bash
pnpm install
pnpm dev
```

Ensure the FastAPI service is running on port 8000 before launching the frontend:

```bash
uvicorn services.api.app.main:app --reload
```
