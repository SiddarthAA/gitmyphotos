"use client";

import { useCallback, useRef, useState } from "react";
import { CloudUpload } from "lucide-react";

interface DropZoneProps {
  onFiles: (files: FileList | File[]) => void;
  photoCount?: number;
  totalSizeMb?: number;
}

export function DropZone({ onFiles, photoCount = 0, totalSizeMb = 0 }: DropZoneProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef                = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (e.dataTransfer.files.length > 0) {
        onFiles(e.dataTransfer.files);
      }
    },
    [onFiles]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        onFiles(e.target.files);
        e.target.value = "";
      }
    },
    [onFiles]
  );

  return (
    <div style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        style={{
          border:         `2px dashed ${dragging ? "var(--accent)" : "var(--border)"}`,
          borderRadius:   "10px",
          padding:        "28px 16px",
          display:        "flex",
          flexDirection:  "column",
          alignItems:     "center",
          gap:            "10px",
          cursor:         "pointer",
          background:     dragging ? "rgba(255,255,255,0.04)" : "transparent",
          transition:     "border-color 0.15s, background 0.15s",
        }}
      >
        <CloudUpload size={24} color={dragging ? "var(--fg)" : "var(--muted)"} />
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: "13px", fontWeight: 500, color: "var(--fg-2)", margin: "0 0 2px", fontFamily: "var(--font-geist-sans)" }}>
            Drop photos here
          </p>
          <p style={{ fontSize: "11px", color: "var(--muted)", margin: 0, fontFamily: "var(--font-geist-sans)" }}>
            JPEG, PNG, HEIC, WEBP
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleChange}
          style={{ display: "none" }}
        />
      </div>

      {/* Stats */}
      {(photoCount > 0 || totalSizeMb > 0) && (
        <div
          style={{
            display:       "flex",
            gap:           "12px",
            padding:       "10px 12px",
            background:    "var(--surface-2)",
            borderRadius:  "8px",
            border:        "1px solid var(--border)",
          }}
        >
          <Stat label="Photos" value={String(photoCount)} />
          <div style={{ width: "1px", background: "var(--border)" }} />
          <Stat label="Total" value={`${totalSizeMb.toFixed(1)} MB`} />
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ flex: 1, textAlign: "center" }}>
      <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--fg)", fontFamily: "var(--font-geist-mono)" }}>{value}</div>
      <div style={{ fontSize: "10px", color: "var(--muted)", fontFamily: "var(--font-geist-sans)", marginTop: "1px" }}>{label}</div>
    </div>
  );
}
