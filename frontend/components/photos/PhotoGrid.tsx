"use client";

import { MonthGroup } from "./MonthGroup";
import { Spinner } from "@/components/ui/Spinner";
import { groupByMonth } from "@/lib/utils";
import type { Photo } from "@/lib/types";
import { CloudUpload } from "lucide-react";

interface PhotoGridProps {
  photos:   Photo[];
  loading:  boolean;
  error:    string | null;
  onSelect: (photo: Photo) => void;
}

export function PhotoGrid({ photos, loading, error, onSelect }: PhotoGridProps) {
  if (loading) {
    return (
      <div
        style={{
          flex:           1,
          display:        "flex",
          alignItems:     "center",
          justifyContent: "center",
          flexDirection:  "column",
          gap:            "12px",
          color:          "var(--muted)",
        }}
      >
        <Spinner size={24} />
        <span style={{ fontSize: "13px", fontFamily: "var(--font-geist-sans)" }}>Loading photos…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          flex:           1,
          display:        "flex",
          alignItems:     "center",
          justifyContent: "center",
          color:          "var(--danger)",
          fontSize:       "13px",
          fontFamily:     "var(--font-geist-sans)",
        }}
      >
        {error}
      </div>
    );
  }

  if (photos.length === 0) {
    return (
      <div
        style={{
          flex:           1,
          display:        "flex",
          alignItems:     "center",
          justifyContent: "center",
          flexDirection:  "column",
          gap:            "14px",
          color:          "var(--muted)",
        }}
      >
        <CloudUpload size={36} />
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: "14px", fontWeight: 500, color: "var(--fg-2)", margin: "0 0 4px", fontFamily: "var(--font-geist-sans)" }}>
            No photos yet
          </p>
          <p style={{ fontSize: "12px", color: "var(--muted)", margin: 0, fontFamily: "var(--font-geist-sans)" }}>
            Drop images into the sidebar to get started.
          </p>
        </div>
      </div>
    );
  }

  const grouped = groupByMonth(photos);
  const months  = Object.keys(grouped).sort((a, b) => b.localeCompare(a));

  return (
    <div
      style={{
        flex:       1,
        overflow:   "auto",
        padding:    "24px",
      }}
    >
      {months.map((month) => (
        <MonthGroup
          key={month}
          month={month}
          photos={grouped[month]}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
