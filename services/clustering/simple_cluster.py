"""Lightweight clustering helpers for the local Faceflow demo service."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, Iterable, List, Sequence


@dataclass
class ClusterResult:
    """Represents a cluster of embedding vectors."""

    id: str
    photo_ids: List[str]
    centroid: List[float]


def _normalize(vector: Sequence[float]) -> List[float]:
    norm = sqrt(sum(component * component for component in vector))
    if norm == 0:
        return [0.0 for _ in vector]
    return [component / norm for component in vector]


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _average(vectors: Iterable[Sequence[float]]) -> List[float]:
    vectors = list(vectors)
    if not vectors:
        return []
    length = len(vectors[0])
    totals = [0.0] * length
    for vector in vectors:
        for idx in range(length):
            totals[idx] += vector[idx]
    return [value / len(vectors) for value in totals]


def cluster_embeddings(
    embeddings: Dict[str, Sequence[float]],
    similarity_threshold: float = 0.8,
) -> List[ClusterResult]:
    """Cluster embeddings using a greedy cosine-similarity threshold.

    The algorithm is intentionally simple and deterministic for demo purposes:
    iterate through the embeddings, placing each vector into the first existing
    cluster whose centroid cosine similarity exceeds the threshold. Otherwise, a
    new cluster is created. Clusters are represented with normalized centroids.
    """

    clusters: List[ClusterResult] = []

    for photo_id, vector in embeddings.items():
        normalized_vector = _normalize(vector)
        if not clusters:
            clusters.append(
                ClusterResult(
                    id=f"cluster-{len(clusters) + 1}",
                    photo_ids=[photo_id],
                    centroid=normalized_vector,
                )
            )
            continue

        assigned = False
        for cluster in clusters:
            similarity = _cosine_similarity(cluster.centroid, normalized_vector)
            if similarity >= similarity_threshold:
                cluster.photo_ids.append(photo_id)
                cluster.centroid = _normalize(
                    _average(embeddings[pid] for pid in cluster.photo_ids)
                )
                assigned = True
                break
        if not assigned:
            clusters.append(
                ClusterResult(
                    id=f"cluster-{len(clusters) + 1}",
                    photo_ids=[photo_id],
                    centroid=normalized_vector,
                )
            )

    return clusters
