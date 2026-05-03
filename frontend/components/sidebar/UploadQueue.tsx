"use client";

import { Pill } from "@/components/ui/Pill";
import { Button } from "@/components/ui/Button";
import type { UploadQueueItem, UploadStage } from "@/lib/types";
import { truncateFilename } from "@/lib/utils";

type PillVariant = "default" | "success" | "warning" | "error" | "pushing" | "muted";

const stageVariant: Record<UploadStage, PillVariant> = {
  idle:    "muted",
  reading: "default",
  exif:    "default",
  thumb:   "default",
  meta:    "default",
  queued:  "warning",
  pushing: "pushing",
  done:    "success",
  error:   "error",
};

const stageLabel: Record<UploadStage, string> = {
  idle:    "idle",
  reading: "reading",
  exif:    "exif",
  thumb:   "thumb",
  meta:    "meta",
  queued:  "queued",
  pushing: "pushing",
  done:    "done",
  error:   "error",
};

interface UploadQueueProps {
  queue:     UploadQueueItem[];
  onClear:   () => void;
}

export function UploadQueue({ queue, onClear }: UploadQueueProps) {
  const hasDone = queue.some((i) => i.stage === "done");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
      {/* Header */}
      <div
        style={{
          display:        "flex",
          alignItems:     "center",
          justifyContent: "space-between",
          padding:        "10px 16px",
          borderBottom:   "1px solid var(--border)",
        }}
      >
        <span style={{ fontSize: "12px", fontWeight: 500, color: "var(--muted-fg)", fontFamily: "var(--font-geist-sans)" }}>
          {queue.length} file{queue.length !== 1 ? "s" : ""}
        </span>
        {hasDone && (
          <Button variant="ghost" size="sm" onClick={onClear} style={{ height: "24px", padding: "2px 8px", fontSize: "11px" }}>
            Clear done
          </Button>
        )}
      </div>

      {/* Items */}
      <div style={{ overflow: "auto", maxHeight: "calc(100vh - 300px)" }}>
        {queue.map((item) => (
          <div
            key={item.id}
            style={{
              display:       "flex",
              alignItems:    "center",
              gap:           "10px",
              padding:       "10px 14px",
              borderBottom:  "1px solid var(--border-soft)",
            }}
          >
            {/* Thumb */}
            {item.previewUrl ? (
              <img
                src={item.previewUrl}
                alt=""
                style={{
                  width:        "36px",
                  height:       "36px",
                  borderRadius: "4px",
                  objectFit:    "cover",
                  flexShrink:   0,
                  border:       "1px solid var(--border)",
                }}
              />
            ) : (
              <div style={{ width: "36px", height: "36px", background: "var(--surface-2)", borderRadius: "4px", flexShrink: 0 }} />
            )}

            {/* Info */}
            <div style={{ flex: 1, overflow: "hidden" }}>
              <div style={{ fontSize: "12px", color: "var(--fg-2)", fontFamily: "var(--font-geist-sans)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {truncateFilename(item.file.name)}
              </div>
              {item.stage !== "idle" && item.stage !== "done" && item.stage !== "error" && (
                <div
                  style={{
                    marginTop:    "4px",
                    height:       "2px",
                    background:   "var(--border)",
                    borderRadius: "2px",
                    overflow:     "hidden",
                  }}
                >
                  <div
                    style={{
                      height:           "100%",
                      width:            `${item.progress}%`,
                      background:       "var(--fg)",
                      transition:       "width 0.3s ease",
                      borderRadius:     "2px",
                    }}
                  />
                </div>
              )}
              {item.error && (
                <div style={{ fontSize: "10px", color: "var(--danger)", marginTop: "2px", fontFamily: "var(--font-geist-sans)" }}>
                  {item.error}
                </div>
              )}
            </div>

            {/* Stage pill */}
            <Pill label={stageLabel[item.stage]} variant={stageVariant[item.stage]} />
          </div>
        ))}
      </div>
    </div>
  );
}
