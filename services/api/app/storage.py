"""Thread-safe in-memory storage for the Faceflow demo API."""

from __future__ import annotations

from threading import RLock
from typing import Dict, List

from .models import (
    Album,
    AlbumSummary,
    Cluster,
    Photo,
    ShareBundle,
)


class InMemoryRepository:
    """Stores albums, photos, clusters and bundles in process memory."""

    def __init__(self) -> None:
        self._albums: Dict[str, Album] = {}
        self._photos: Dict[str, List[Photo]] = {}
        self._clusters: Dict[str, List[Cluster]] = {}
        self._bundles: Dict[str, ShareBundle] = {}
        self._lock = RLock()

    def create_album(self, album: Album) -> Album:
        with self._lock:
            self._albums[album.id] = album
            self._photos.setdefault(album.id, [])
            self._clusters.setdefault(album.id, [])
        return album

    def get_album(self, album_id: str) -> Album | None:
        with self._lock:
            return self._albums.get(album_id)

    def list_albums(self) -> List[Album]:
        with self._lock:
            return list(self._albums.values())

    def add_photo(self, photo: Photo) -> Photo:
        with self._lock:
            if photo.album_id not in self._albums:
                raise KeyError("Album does not exist")
            self._photos.setdefault(photo.album_id, []).append(photo)
        return photo

    def list_photos(self, album_id: str) -> List[Photo]:
        with self._lock:
            return list(self._photos.get(album_id, []))

    def save_clusters(self, album_id: str, clusters: List[Cluster]) -> List[Cluster]:
        with self._lock:
            if album_id not in self._albums:
                raise KeyError("Album does not exist")
            self._clusters[album_id] = clusters
        return clusters

    def list_clusters(self, album_id: str) -> List[Cluster]:
        with self._lock:
            return list(self._clusters.get(album_id, []))

    def create_bundle(self, bundle: ShareBundle) -> ShareBundle:
        with self._lock:
            self._bundles[bundle.id] = bundle
        return bundle

    def get_bundle(self, bundle_id: str) -> ShareBundle | None:
        with self._lock:
            return self._bundles.get(bundle_id)

    def get_album_summary(self, album_id: str) -> AlbumSummary | None:
        with self._lock:
            album = self._albums.get(album_id)
            if not album:
                return None
            return AlbumSummary(
                album=album,
                photos=list(self._photos.get(album_id, [])),
                clusters=list(self._clusters.get(album_id, [])),
            )


repository = InMemoryRepository()
