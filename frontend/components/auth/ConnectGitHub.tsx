"use client";

import { Github } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface ConnectGitHubProps {
  onConnect: () => void;
  loading?:  boolean;
}

export function ConnectGitHub({ onConnect, loading = false }: ConnectGitHubProps) {
  return (
    <div
      style={{
        position:       "fixed",
        inset:          0,
        background:     "var(--bg)",
        display:        "flex",
        alignItems:     "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          display:        "flex",
          flexDirection:  "column",
          alignItems:     "center",
          gap:            "32px",
          padding:        "48px",
          background:     "var(--surface)",
          border:         "1px solid var(--border)",
          borderRadius:   "16px",
          width:          "100%",
          maxWidth:       "400px",
          margin:         "0 16px",
        }}
      >
        {/* Logo */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              width:          "48px",
              height:         "48px",
              background:     "var(--surface-2)",
              borderRadius:   "12px",
              border:         "1px solid var(--border)",
              display:        "flex",
              alignItems:     "center",
              justifyContent: "center",
            }}
          >
            <Github size={24} color="var(--fg)" />
          </div>
          <div style={{ textAlign: "center" }}>
            <h1
              style={{
                fontSize:   "22px",
                fontWeight: 600,
                color:      "var(--fg)",
                fontFamily: "var(--font-geist-sans)",
                margin:     0,
              }}
            >
              GitMyPhotos
            </h1>
            <p
              style={{
                fontSize:   "13px",
                color:      "var(--muted)",
                fontFamily: "var(--font-geist-sans)",
                margin:     "6px 0 0",
              }}
            >
              Your photos stay in your repo.
            </p>
          </div>
        </div>

        {/* Divider */}
        <div style={{ width: "100%", height: "1px", background: "var(--border)" }} />

        {/* CTA */}
        <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: "12px" }}>
          <Button
            variant="primary"
            size="lg"
            fullWidth
            loading={loading}
            onClick={onConnect}
          >
            <Github size={16} />
            Continue with GitHub
          </Button>
          <p
            style={{
              fontSize:   "11px",
              color:      "var(--muted)",
              textAlign:  "center",
              fontFamily: "var(--font-geist-sans)",
              margin:     0,
              lineHeight: 1.5,
            }}
          >
            Authorises read/write access to your repositories.
            <br />
            No data is stored on our servers.
          </p>
        </div>
      </div>
    </div>
  );
}
