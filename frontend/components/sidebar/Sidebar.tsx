"use client";

import { DropZone } from "./DropZone";
import { UploadQueue } from "./UploadQueue";
import { BatchIndicator } from "./BatchIndicator";
import type { UploadQueueItem, RepoHealth } from "@/lib/types";

interface SidebarProps {
  queue:         UploadQueueItem[];
  batchCountdown: number | null;
  batchSize:     number;
  health:        RepoHealth | null;
  onFiles:       (files: FileList | File[]) => void;
  onClearDone:   () => void;
}

export function Sidebar({
  queue,
  batchCountdown,
  batchSize,
  health,
  onFiles,
  onClearDone,
}: SidebarProps) {
  const hasActive = queue.some((i) => i.stage !== "idle");
  const isPushing = queue.some((i) => i.stage === "pushing");
  const isDone    = queue.length > 0 && queue.every((i) => i.stage === "done" || i.stage === "error");

  return (
    <aside
      style={{
        width:        "268px",
        flexShrink:   0,
        background:   "var(--surface)",
        borderRight:  "1px solid var(--border)",
        display:      "flex",
        flexDirection: "column",
        overflow:     "hidden",
      }}
    >
      {/* Batch indicator */}
      {(batchCountdown !== null || isPushing || isDone) && (
        <div style={{ paddingTop: "12px" }}>
          <BatchIndicator
            pushing={isPushing}
            done={isDone}
            count={batchSize}
            countdown={batchCountdown}
          />
        </div>
      )}

      {/* Content */}
      {hasActive ? (
        <UploadQueue queue={queue} onClear={onClearDone} />
      ) : (
        <DropZone
          onFiles={onFiles}
          photoCount={health?.photo_count ?? 0}
          totalSizeMb={health?.total_size_mb ?? 0}
        />
      )}
    </aside>
  );
}
