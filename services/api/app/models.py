"""Pydantic schemas and internal data models for the Faceflow demo API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class AlbumCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class Album(BaseModel):
    id: str
    name: str
    created_at: datetime


class PhotoCreate(BaseModel):
    filename: str = Field(..., min_length=1)
    embedding: List[float] = Field(default_factory=list)
    metadata: Dict[str, str] | None = None


class Photo(BaseModel):
    id: str
    album_id: str
    filename: str
    embedding: List[float]
    metadata: Dict[str, str] | None = None
    uploaded_at: datetime


class Cluster(BaseModel):
    id: str
    album_id: str
    centroid: List[float]
    photo_ids: List[str]
    created_at: datetime


class AlbumSummary(BaseModel):
    album: Album
    photos: List[Photo]
    clusters: List[Cluster]


class ShareBundleCreate(BaseModel):
    album_id: str
    cluster_ids: List[str] = Field(..., min_length=1)
    recipients: List[str] = Field(..., min_length=1)


class ShareBundle(BaseModel):
    id: str
    album_id: str
    cluster_ids: List[str]
    recipients: List[str]
    created_at: datetime
    download_url: HttpUrl


def new_album(name: str) -> Album:
    return Album(id=str(uuid4()), name=name, created_at=utcnow())


def new_photo(album_id: str, payload: PhotoCreate) -> Photo:
    return Photo(
        id=str(uuid4()),
        album_id=album_id,
        filename=payload.filename,
        embedding=payload.embedding,
        metadata=payload.metadata,
        uploaded_at=utcnow(),
    )


def new_cluster(album_id: str, cluster_id: str, photo_ids: List[str], centroid: List[float]) -> Cluster:
    return Cluster(
        id=cluster_id,
        album_id=album_id,
        photo_ids=photo_ids,
        centroid=centroid,
        created_at=utcnow(),
    )


def new_bundle(payload: ShareBundleCreate, download_url: str) -> ShareBundle:
    return ShareBundle(
        id=str(uuid4()),
        album_id=payload.album_id,
        cluster_ids=payload.cluster_ids,
        recipients=payload.recipients,
        created_at=utcnow(),
        download_url=download_url,
    )
