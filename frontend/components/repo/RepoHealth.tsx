"use client";

import { useEffect } from "react";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import type { RepoHealth as RepoHealthType, CurrentRepo } from "@/lib/types";

interface CheckItem {
  key:   keyof RepoHealthType;
  label: string;
}

const CHECKS: CheckItem[] = [
  { key: "connected",   label: "Repository connected"         },
  { key: "yml",         label: "Workflow YAML present"        },
  { key: "manifest",    label: "Manifest file created"        },
  { key: "folders",     label: "Folder structure ready"       },
  { key: "initialized", label: "Repository fully initialised" },
];

interface RepoHealthProps {
  health:    RepoHealthType | null;
  current:   CurrentRepo   | null;
  onScaffold: () => Promise<void>;
  onRefetch:  () => void;
  scaffolding: boolean;
}

export function RepoHealth({ health, current, onScaffold, onRefetch, scaffolding }: RepoHealthProps) {
  // Poll until initialized
  useEffect(() => {
    if (health?.initialized) return;
    const id = setInterval(onRefetch, 3000);
    return () => clearInterval(id);
  }, [health?.initialized, onRefetch]);

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
          background:   "var(--surface)",
          border:       "1px solid var(--border)",
          borderRadius: "16px",
          padding:      "32px",
          width:        "100%",
          maxWidth:     "440px",
          margin:       "0 16px",
        }}
      >
        <h2 style={{ fontSize: "18px", fontWeight: 600, color: "var(--fg)", margin: "0 0 4px", fontFamily: "var(--font-geist-sans)" }}>
          Setting up your repository
        </h2>
        {current && (
          <p style={{ fontSize: "13px", color: "var(--muted)", margin: "0 0 24px", fontFamily: "var(--font-geist-mono)" }}>
            {current.owner}/{current.name} · {current.branch}
          </p>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "24px" }}>
          {CHECKS.map(({ key, label }) => {
            const done    = Boolean(health?.[key]);
            const current = !done && CHECKS.findIndex((c) => !health?.[c.key]) === CHECKS.findIndex((c) => c.key === key);
            return (
              <div key={key} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                {done ? (
                  <CheckCircle2 size={16} color="var(--success)" />
                ) : current ? (
                  <Loader2 size={16} color="var(--muted)" style={{ animation: "spin 1s linear infinite" }} />
                ) : (
                  <Circle size={16} color="var(--border)" />
                )}
                <span
                  style={{
                    fontSize:   "13px",
                    fontFamily: "var(--font-geist-sans)",
                    color:      done ? "var(--fg)" : "var(--muted)",
                  }}
                >
                  {label}
                </span>
              </div>
            );
          })}
        </div>

        {!health?.initialized && (
          <Button variant="ghost" size="md" fullWidth loading={scaffolding} onClick={onScaffold}>
            Scaffold repository manually
          </Button>
        )}
      </div>
    </div>
  );
}
