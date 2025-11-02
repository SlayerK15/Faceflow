"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { ClusterList } from "../components/ClusterList";
import { UploadForm } from "../components/UploadForm";

interface Album {
  id: string;
  name: string;
}

export default function Home() {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [activeAlbum, setActiveAlbum] = useState<string | null>(null);
  const [albumName, setAlbumName] = useState("Demo Album");
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  async function refreshAlbums() {
    const response = await fetch("/albums");
    if (!response.ok) {
      setError("Failed to load albums");
      return;
    }
    const data: Album[] = await response.json();
    setAlbums(data);
    if (data.length > 0 && !activeAlbum) {
      setActiveAlbum(data[0].id);
    }
  }

  async function handleCreateAlbum(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const response = await fetch("/albums", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: albumName })
    });
    if (!response.ok) {
      setError("Failed to create album");
      return;
    }
    const created: Album = await response.json();
    setAlbumName("");
    setActiveAlbum(created.id);
    await refreshAlbums();
  }

  useEffect(() => {
    void refreshAlbums();
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Faceflow Demo</h1>
        <p className="text-sm text-slate-400">
          Create albums, upload embeddings and cluster faces using the accompanying FastAPI backend.
        </p>
      </header>

      <section className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
        <form className="flex items-center gap-3" onSubmit={handleCreateAlbum}>
          <input
            className="flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
            placeholder="Album name"
            value={albumName}
            onChange={(event) => setAlbumName(event.target.value)}
          />
          <button className="rounded bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-sky-400">
            Create album
          </button>
        </form>
        {error && <p className="mt-2 text-sm text-rose-400">{error}</p>}
      </section>

      <section className="grid gap-4 md:grid-cols-[240px_1fr]">
        <aside className="rounded-lg border border-slate-800 bg-slate-900/30 p-3">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">Albums</h2>
          <ul className="flex flex-col gap-2">
            {albums.map((album) => (
              <li key={album.id}>
                <button
                  onClick={() => setActiveAlbum(album.id)}
                  className={`w-full rounded px-3 py-2 text-left text-sm ${
                    activeAlbum === album.id
                      ? "bg-sky-500 text-slate-950"
                      : "bg-slate-950 text-slate-200 hover:bg-slate-800"
                  }`}
                >
                  {album.name}
                </button>
              </li>
            ))}
            {albums.length === 0 && <li className="text-sm text-slate-500">No albums yet.</li>}
          </ul>
        </aside>

        <div className="flex flex-col gap-4">
          {activeAlbum ? (
            <>
              <UploadForm
                albumId={activeAlbum}
                onPhotoUploaded={() => setRefreshKey((value) => value + 1)}
              />
              <ClusterList albumId={activeAlbum} refreshKey={refreshKey} />
            </>
          ) : (
            <div className="rounded border border-dashed border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-400">
              Select or create an album to get started.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
