"""FastAPI application that simulates the Faceflow pipeline."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware

from services.clustering import cluster_embeddings

from .models import (
    Album,
    AlbumCreate,
    AlbumSummary,
    Cluster,
    Photo,
    PhotoCreate,
    ShareBundle,
    ShareBundleCreate,
    new_album,
    new_bundle,
    new_cluster,
    new_photo,
)
from .storage import InMemoryRepository, repository

app = FastAPI(title="Faceflow Demo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_repository() -> InMemoryRepository:
    return repository


@app.get("/albums", response_model=list[Album])
def list_albums(store: InMemoryRepository = Depends(get_repository)) -> list[Album]:
    return store.list_albums()


@app.post("/albums", response_model=Album, status_code=201)
def create_album(payload: AlbumCreate, store: InMemoryRepository = Depends(get_repository)) -> Album:
    album = new_album(payload.name)
    return store.create_album(album)


@app.get("/albums/{album_id}", response_model=AlbumSummary)
def get_album_summary(
    album_id: str = Path(..., description="Album identifier"),
    store: InMemoryRepository = Depends(get_repository),
) -> AlbumSummary:
    summary = store.get_album_summary(album_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Album not found")
    return summary


@app.post("/albums/{album_id}/photos", response_model=Photo, status_code=201)
def add_photo(
    payload: PhotoCreate,
    album_id: str = Path(..., description="Album identifier"),
    store: InMemoryRepository = Depends(get_repository),
) -> Photo:
    if not store.get_album(album_id):
        raise HTTPException(status_code=404, detail="Album not found")
    photo = new_photo(album_id, payload)
    try:
        return store.add_photo(photo)
    except KeyError as exc:  # pragma: no cover - defensive, should not occur
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/albums/{album_id}/cluster", response_model=list[Cluster])
def run_clustering(
    album_id: str = Path(..., description="Album identifier"),
    store: InMemoryRepository = Depends(get_repository),
) -> list[Cluster]:
    album = store.get_album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    photos = store.list_photos(album_id)
    embeddings = {photo.id: photo.embedding for photo in photos if photo.embedding}
    if not embeddings:
        raise HTTPException(status_code=400, detail="No embeddings available for clustering")

    cluster_results = cluster_embeddings(embeddings)
    clusters = [
        new_cluster(album_id, result.id, result.photo_ids, result.centroid)
        for result in cluster_results
    ]
    store.save_clusters(album_id, clusters)
    return clusters


@app.post("/share", response_model=ShareBundle, status_code=201)
def create_share_bundle(
    payload: ShareBundleCreate,
    store: InMemoryRepository = Depends(get_repository),
) -> ShareBundle:
    summary = store.get_album_summary(payload.album_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Album not found")

    existing_cluster_ids = {cluster.id for cluster in summary.clusters}
    missing = [cluster_id for cluster_id in payload.cluster_ids if cluster_id not in existing_cluster_ids]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={"message": "Unknown clusters", "cluster_ids": missing},
        )

    download_url = f"https://share.faceflow.local/{payload.album_id}/bundle"
    bundle = new_bundle(payload, download_url)
    return store.create_bundle(bundle)


@app.get("/share/{bundle_id}", response_model=ShareBundle)
def get_share_bundle(
    bundle_id: str = Path(..., description="Share bundle identifier"),
    store: InMemoryRepository = Depends(get_repository),
) -> ShareBundle:
    bundle = store.get_bundle(bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Share bundle not found")
    return bundle
