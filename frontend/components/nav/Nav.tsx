"use client";

import { Settings } from "lucide-react";
import type { CurrentRepo, AuthState } from "@/lib/types";

interface NavProps {
  auth:          AuthState;
  current:       CurrentRepo | null;
  onSettings:    () => void;
}

export function Nav({ auth, current, onSettings }: NavProps) {
  return (
    <header
      style={{
        height:        "48px",
        background:    "var(--surface)",
        borderBottom:  "1px solid var(--border)",
        display:       "flex",
        alignItems:    "center",
        padding:       "0 16px",
        gap:           "12px",
        flexShrink:    0,
        position:      "relative",
        zIndex:        10,
      }}
    >
      {/* Wordmark */}
      <span
        style={{
          fontSize:   "14px",
          fontWeight: 600,
          color:      "var(--fg)",
          fontFamily: "var(--font-geist-sans)",
          letterSpacing: "-0.01em",
          flex:       "0 0 auto",
        }}
      >
        GitMyPhotos
      </span>

      {/* Repo pill — centred */}
      <div style={{ flex: 1, display: "flex", justifyContent: "center" }}>
        {current && (
          <span
            style={{
              fontSize:     "12px",
              fontFamily:   "var(--font-geist-mono)",
              color:        "var(--muted-fg)",
              background:   "var(--surface-2)",
              border:       "1px solid var(--border)",
              borderRadius: "999px",
              padding:      "3px 12px",
              maxWidth:     "360px",
              overflow:     "hidden",
              textOverflow: "ellipsis",
              whiteSpace:   "nowrap",
            }}
          >
            {current.owner}/{current.name} · {current.branch}
          </span>
        )}
      </div>

      {/* Right side */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: "0 0 auto" }}>
        <button
          onClick={onSettings}
          title="Settings"
          style={{
            background:   "transparent",
            border:       "none",
            cursor:       "pointer",
            color:        "var(--muted)",
            padding:      "6px",
            borderRadius: "6px",
            display:      "flex",
            alignItems:   "center",
          }}
        >
          <Settings size={16} />
        </button>

        {auth.avatar_url && (
          <img
            src={auth.avatar_url}
            alt={auth.username || "avatar"}
            style={{
              width:        "28px",
              height:       "28px",
              borderRadius: "50%",
              border:       "1px solid var(--border)",
            }}
          />
        )}
      </div>
    </header>
  );
}
