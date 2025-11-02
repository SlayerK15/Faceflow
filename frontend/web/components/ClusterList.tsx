"use client";

import { useEffect, useState } from "react";

interface Cluster {
  id: string;
  photo_ids: string[];
}

interface ClusterListProps {
  albumId: string;
  refreshKey: number;
}

type AlbumSummaryResponse = {
  clusters: Cluster[];
};

export function ClusterList({ albumId, refreshKey }: ClusterListProps) {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refreshClusters() {
    const response = await fetch(`/albums/${albumId}`);
    if (!response.ok) {
      setError("Failed to load clusters");
      return;
    }
    const data: AlbumSummaryResponse = await response.json();
    setClusters(data.clusters ?? []);
  }

  async function handleCluster() {
    setError(null);
    const response = await fetch(`/albums/${albumId}/cluster`, { method: "POST" });
    if (!response.ok) {
      setError("No embeddings available. Upload photos first.");
      return;
    }
    await refreshClusters();
  }

  useEffect(() => {
    void refreshClusters();
  }, [refreshKey]);

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Clusters</h2>
        <button
          onClick={handleCluster}
          className="rounded bg-emerald-500 px-3 py-1 text-sm font-semibold text-slate-950 hover:bg-emerald-400"
        >
          Run clustering
        </button>
      </div>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      <ul className="flex flex-col gap-2">
        {clusters.map((cluster) => (
          <li key={cluster.id} className="rounded border border-slate-800 bg-slate-900/40 p-3">
            <h3 className="text-sm font-medium">{cluster.id}</h3>
            <p className="text-xs text-slate-400">Photos: {cluster.photo_ids.join(", ")}</p>
          </li>
        ))}
        {clusters.length === 0 && (
          <li className="rounded border border-dashed border-slate-800 bg-slate-900/30 p-4 text-sm text-slate-400">
            No clusters yet. Upload photos with embeddings and run clustering.
          </li>
        )}
      </ul>
    </section>
  );
}
