"use client";

import { Panel } from "@/components/ui/Panel";
import { Button } from "@/components/ui/Button";
import type { CurrentRepo, AuthState } from "@/lib/types";
import { formatBytes } from "@/lib/utils";

interface SettingsProps {
  open:         boolean;
  onClose:      () => void;
  auth:         AuthState;
  current:      CurrentRepo | null;
  onDisconnect: () => Promise<void>;
  onLogout:     () => void;
}

export function Settings({ open, onClose, auth, current, onDisconnect, onLogout }: SettingsProps) {
  return (
    <Panel open={open} onClose={onClose} title="Settings" width={360} side="right">
      <div style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "20px" }}>

        {/* Account */}
        <Section title="Account">
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
            {auth.avatar_url && (
              <img
                src={auth.avatar_url}
                alt=""
                style={{ width: "36px", height: "36px", borderRadius: "50%", border: "1px solid var(--border)" }}
              />
            )}
            <div>
              <div style={{ fontSize: "13px", fontWeight: 500, color: "var(--fg)", fontFamily: "var(--font-geist-sans)" }}>
                {auth.name || auth.username}
              </div>
              {auth.username && (
                <div style={{ fontSize: "11px", color: "var(--muted)", fontFamily: "var(--font-geist-mono)" }}>
                  @{auth.username}
                </div>
              )}
            </div>
          </div>
          <Button variant="danger" size="sm" onClick={onLogout} fullWidth>
            Sign out
          </Button>
        </Section>

        {/* Repository */}
        <Section title="Repository">
          {current ? (
            <>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "12px" }}>
                <InfoRow label="Repo"   value={`${current.owner}/${current.name}`} />
                <InfoRow label="Branch" value={current.branch ?? ""} />
              </div>
              <Button variant="danger" size="sm" fullWidth onClick={onDisconnect}>
                Disconnect
              </Button>
            </>
          ) : (
            <p style={{ fontSize: "12px", color: "var(--muted)", fontFamily: "var(--font-geist-sans)", margin: 0 }}>
              No repository connected.
            </p>
          )}
        </Section>

      </div>
    </Panel>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3
        style={{
          fontSize:      "10px",
          fontWeight:    600,
          color:         "var(--muted)",
          fontFamily:    "var(--font-geist-sans)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          margin:        "0 0 10px",
        }}
      >
        {title}
      </h3>
      <div
        style={{
          background:   "var(--surface-2)",
          border:       "1px solid var(--border)",
          borderRadius: "10px",
          padding:      "14px",
        }}
      >
        {children}
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
      <span style={{ fontSize: "11px", color: "var(--muted)", fontFamily: "var(--font-geist-sans)" }}>{label}</span>
      <span style={{ fontSize: "11px", color: "var(--fg-2)", fontFamily: "var(--font-geist-mono)", wordBreak: "break-all", textAlign: "right" }}>{value}</span>
    </div>
  );
}
