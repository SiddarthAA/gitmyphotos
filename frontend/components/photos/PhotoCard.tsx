"use client";

import { useState } from "react";
import { Shimmer } from "@/components/ui/Shimmer";
import { buildThumbUrl, truncateFilename } from "@/lib/utils";
import type { Photo } from "@/lib/types";

interface PhotoCardProps {
  photo:    Photo;
  onSelect: (photo: Photo) => void;
}

export function PhotoCard({ photo, onSelect }: PhotoCardProps) {
  const [loaded,  setLoaded]  = useState(false);
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onClick={() => onSelect(photo)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position:     "relative",
        aspectRatio:  "4/3",
        overflow:     "hidden",
        borderRadius: "6px",
        cursor:       "pointer",
        background:   "var(--surface-2)",
        border:       "1px solid var(--border)",
      }}
    >
      {/* Shimmer while loading */}
      {!loaded && (
        <div style={{ position: "absolute", inset: 0 }}>
          <Shimmer width="100%" height="100%" radius={0} />
        </div>
      )}

      {/* Thumbnail */}
      <img
        src={buildThumbUrl(photo.id)}
        alt={photo.filename}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        style={{
          width:      "100%",
          height:     "100%",
          objectFit:  "cover",
          display:    "block",
          opacity:    loaded ? 1 : 0,
          transition: "opacity 0.2s",
        }}
      />

      {/* Hover overlay */}
      <div
        style={{
          position:   "absolute",
          inset:      0,
          background: "linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 50%)",
          opacity:    hovered ? 1 : 0,
          transition: "opacity 0.15s",
          display:    "flex",
          alignItems: "flex-end",
          padding:    "8px",
        }}
      >
        <span
          style={{
            fontSize:     "10px",
            color:        "#fff",
            fontFamily:   "var(--font-geist-sans)",
            overflow:     "hidden",
            textOverflow: "ellipsis",
            whiteSpace:   "nowrap",
            maxWidth:     "100%",
          }}
        >
          {truncateFilename(photo.filename)}
        </span>
      </div>
    </div>
  );
}
