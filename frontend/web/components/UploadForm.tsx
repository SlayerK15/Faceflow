"use client";

import { useState } from "react";
import type { FormEvent } from "react";

interface UploadFormProps {
  albumId: string;
  onPhotoUploaded(): void;
}

export function UploadForm({ albumId, onPhotoUploaded }: UploadFormProps) {
  const [filename, setFilename] = useState("");
  const [embedding, setEmbedding] = useState("0.9, 0.1, 0.2");
  const [status, setStatus] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("Uploading...");

    const numericEmbedding = embedding
      .split(",")
      .map((value) => Number.parseFloat(value.trim()))
      .filter((value) => Number.isFinite(value));

    const response = await fetch(`/albums/${albumId}/photos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename, embedding: numericEmbedding })
    });

    if (!response.ok) {
      setStatus("Upload failed");
      return;
    }

    setFilename("");
    onPhotoUploaded();
    setStatus("Uploaded");
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <div>
        <label className="mb-1 block text-sm font-medium">Filename</label>
        <input
          className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          value={filename}
          onChange={(event) => setFilename(event.target.value)}
          placeholder="photo.jpg"
          required
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">Embedding (comma separated vector)</label>
        <input
          className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          value={embedding}
          onChange={(event) => setEmbedding(event.target.value)}
        />
      </div>
      <div className="flex items-center gap-3">
        <button
          type="submit"
          className="rounded bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-sky-400"
        >
          Upload photo
        </button>
        {status && <span className="text-xs text-slate-400">{status}</span>}
      </div>
    </form>
  );
}
