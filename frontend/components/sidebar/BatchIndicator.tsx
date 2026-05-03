"use client";

import { CheckCircle2, Clock } from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";

interface BatchIndicatorProps {
  pushing:   boolean;
  done:      boolean;
  count:     number;
  countdown: number | null;
  sha?:      string;
}

export function BatchIndicator({ pushing, done, count, countdown, sha }: BatchIndicatorProps) {
  if (done) {
    return (
      <div
        style={{
          display:       "flex",
          alignItems:    "center",
          gap:           "8px",
          padding:       "10px 14px",
          background:    "rgba(74,222,128,0.06)",
          border:        "1px solid rgba(74,222,128,0.2)",
          borderRadius:  "8px",
          margin:        "0 16px 12px",
        }}
      >
        <CheckCircle2 size={14} color="var(--success)" />
        <div style={{ flex: 1 }}>
          <span style={{ fontSize: "12px", color: "var(--success)", fontFamily: "var(--font-geist-sans)", fontWeight: 500 }}>
            {count} photo{count !== 1 ? "s" : ""} committed
          </span>
          {sha && (
            <span style={{ fontSize: "11px", color: "var(--muted)", fontFamily: "var(--font-geist-mono)", marginLeft: "6px" }}>
              {sha.slice(0, 7)}
            </span>
          )}
        </div>
      </div>
    );
  }

  if (pushing) {
    return (
      <div
        style={{
          display:      "flex",
          alignItems:   "center",
          gap:          "8px",
          padding:      "10px 14px",
          background:   "rgba(129,140,248,0.06)",
          border:       "1px solid rgba(129,140,248,0.2)",
          borderRadius: "8px",
          margin:       "0 16px 12px",
        }}
      >
        <Spinner size={13} color="#818cf8" />
        <span style={{ fontSize: "12px", color: "#818cf8", fontFamily: "var(--font-geist-sans)", fontWeight: 500 }}>
          Pushing {count} photo{count !== 1 ? "s" : ""}…
        </span>
      </div>
    );
  }

  if (countdown !== null && countdown > 0) {
    return (
      <div
        style={{
          display:      "flex",
          alignItems:   "center",
          gap:          "8px",
          padding:      "10px 14px",
          background:   "rgba(251,191,36,0.06)",
          border:       "1px solid rgba(251,191,36,0.2)",
          borderRadius: "8px",
          margin:       "0 16px 12px",
        }}
      >
        <Clock size={13} color="var(--warning)" />
        <span style={{ fontSize: "12px", color: "var(--warning)", fontFamily: "var(--font-geist-sans)", fontWeight: 500 }}>
          {count} photo{count !== 1 ? "s" : ""} → 1 commit in {countdown}s
        </span>
      </div>
    );
  }

  return null;
}
