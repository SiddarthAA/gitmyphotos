"use client";

import { PhotoCard } from "./PhotoCard";
import type { Photo } from "@/lib/types";

interface MonthGroupProps {
  month:    string;
  photos:   Photo[];
  onSelect: (photo: Photo) => void;
}

export function MonthGroup({ month, photos, onSelect }: MonthGroupProps) {
  return (
    <section style={{ marginBottom: "32px" }}>
      {/* Month header */}
      <div
        style={{
          display:       "flex",
          alignItems:    "baseline",
          gap:           "8px",
          marginBottom:  "12px",
        }}
      >
        <h2
          style={{
            fontSize:   "13px",
            fontWeight: 600,
            color:      "var(--fg)",
            fontFamily: "var(--font-geist-sans)",
            margin:     0,
          }}
        >
          {month}
        </h2>
        <span
          style={{
            fontSize:   "11px",
            color:      "var(--muted)",
            fontFamily: "var(--font-geist-sans)",
          }}
        >
          {photos.length} photo{photos.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Grid */}
      <div
        style={{
          display:               "grid",
          gridTemplateColumns:   "repeat(auto-fill, minmax(160px, 1fr))",
          gap:                   "6px",
        }}
      >
        {photos.map((photo) => (
          <PhotoCard key={photo.id} photo={photo} onSelect={onSelect} />
        ))}
      </div>
    </section>
  );
}
