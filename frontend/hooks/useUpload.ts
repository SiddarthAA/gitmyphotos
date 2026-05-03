"use client";

import { useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import type { UploadQueueItem, UploadStage } from "@/lib/types";

const BATCH_DELAY = 3000; // 3s window

interface UseUploadReturn {
  queue: UploadQueueItem[];
  addFiles: (files: FileList | File[]) => void;
  clearDone: () => void;
  batchCountdown: number | null;
  batchSize: number;
}

export function useUpload(onCommit?: () => void): UseUploadReturn {
  const [queue, setQueue]               = useState<UploadQueueItem[]>([]);
  const [batchCountdown, setBatchCountdown] = useState<number | null>(null);
  const [batchSize, setBatchSize]       = useState(0);
  const timerRef                        = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownRef                    = useRef<ReturnType<typeof setInterval> | null>(null);

  const updateItem = useCallback(
    (id: string, patch: Partial<UploadQueueItem>) =>
      setQueue((q) => q.map((item) => (item.id === id ? { ...item, ...patch } : item))),
    []
  );

  const startBatchCountdown = useCallback(
    (items: UploadQueueItem[]) => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (countdownRef.current) clearInterval(countdownRef.current);

      const queued = items.filter((i) => i.stage === "queued");
      setBatchSize(queued.length);
      setBatchCountdown(3);

      let remaining = 3;
      countdownRef.current = setInterval(() => {
        remaining -= 1;
        setBatchCountdown(remaining);
        if (remaining <= 0) {
          clearInterval(countdownRef.current!);
          countdownRef.current = null;
        }
      }, 1000);

      timerRef.current = setTimeout(async () => {
        setBatchCountdown(null);
        // All queued items → pushing
        setQueue((q) =>
          q.map((item) =>
            item.stage === "queued" ? { ...item, stage: "pushing" as UploadStage } : item
          )
        );
        // Already uploaded individually — just wait and mark done
        await new Promise((r) => setTimeout(r, 800));
        setQueue((q) =>
          q.map((item) =>
            item.stage === "pushing" ? { ...item, stage: "done" as UploadStage, progress: 100 } : item
          )
        );
        onCommit?.();
      }, BATCH_DELAY);
    },
    [onCommit]
  );

  const processFile = useCallback(
    async (item: UploadQueueItem) => {
      const { id, file } = item;

      // reading
      updateItem(id, { stage: "reading", progress: 5 });
      await new Promise((r) => setTimeout(r, 80));

      // exif
      updateItem(id, { stage: "exif", progress: 20 });
      await new Promise((r) => setTimeout(r, 80));

      // thumb
      updateItem(id, { stage: "thumb", progress: 40 });
      await new Promise((r) => setTimeout(r, 80));

      // meta
      updateItem(id, { stage: "meta", progress: 60 });

      // POST to backend
      try {
        await api.upload.file(file);
        updateItem(id, { stage: "queued", progress: 80 });
        // Trigger batch countdown after this file is queued
        setQueue((q) => {
          const updated = q.map((i) =>
            i.id === id ? { ...i, stage: "queued" as UploadStage, progress: 80 } : i
          );
          startBatchCountdown(updated);
          return updated;
        });
      } catch (e) {
        updateItem(id, {
          stage: "error",
          error: e instanceof Error ? e.message : "Upload failed",
        });
      }
    },
    [updateItem, startBatchCountdown]
  );

  const addFiles = useCallback(
    (files: FileList | File[]) => {
      const arr = Array.from(files);
      const newItems: UploadQueueItem[] = arr.map((file) => ({
        id:         `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        file,
        stage:      "idle",
        progress:   0,
        previewUrl: URL.createObjectURL(file),
      }));

      setQueue((q) => [...q, ...newItems]);

      // Process each file
      for (const item of newItems) {
        processFile(item);
      }
    },
    [processFile]
  );

  const clearDone = useCallback(() => {
    setQueue((q) => q.filter((item) => item.stage !== "done"));
    setBatchSize(0);
  }, []);

  return { queue, addFiles, clearDone, batchCountdown, batchSize };
}
