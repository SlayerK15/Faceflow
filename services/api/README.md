# Faceflow API Service

This service provides a FastAPI-powered backend that emulates Faceflow's upload, clustering and sharing flows without relying on AWS services. It is suitable for local development demos and integration tests.

## Running locally

```bash
uvicorn app.main:app --reload
```

The server stores data in-memory for simplicity. Restarting the server clears all albums, photos, clusters and share bundles.

## Key endpoints

- `POST /albums` — create a new album
- `POST /albums/{album_id}/photos` — register uploaded photos and (optional) embeddings
- `POST /albums/{album_id}/cluster` — run lightweight clustering using cosine similarity
- `GET /albums/{album_id}` — retrieve album details with computed clusters
- `POST /share` — create share bundles for selected clusters
- `GET /share/{bundle_id}` — obtain bundle details and download links

Refer to the automatically generated OpenAPI schema at `/docs` for the complete contract.
