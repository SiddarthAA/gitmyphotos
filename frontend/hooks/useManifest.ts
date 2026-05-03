"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import type { Photo, Manifest } from "@/lib/types";

const CACHE_TTL = 5 * 60 * 1000; // 5 min

interface UseManifestReturn {
  photos: Photo[];
  total: number;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useManifest(enabled = true): UseManifestReturn {
  const [photos, setPhotos]   = useState<Photo[]>([]);
  const [total, setTotal]     = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);
  const cachedAt              = useRef<number>(0);

  const fetch = useCallback(async (force = false) => {
    if (!enabled) return;
    const age = Date.now() - cachedAt.current;
    if (!force && age < CACHE_TTL && photos.length > 0) return;
    setLoading(true);
    setError(null);
    try {
      const manifest: Manifest = await api.photos.manifest();
      const sorted = [...manifest.photos].sort((a, b) => {
        const ta = new Date(a.captured_at ?? a.uploaded_at).getTime();
        const tb = new Date(b.captured_at ?? b.uploaded_at).getTime();
        return tb - ta;
      });
      setPhotos(sorted);
      setTotal(manifest.photo_count);
      cachedAt.current = Date.now();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load photos");
    } finally {
      setLoading(false);
    }
  }, [enabled]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (enabled) fetch();
  }, [enabled, fetch]);

  return {
    photos,
    total,
    loading,
    error,
    refetch: () => fetch(true),
  };
}
