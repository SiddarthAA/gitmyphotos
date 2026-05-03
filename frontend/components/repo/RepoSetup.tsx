"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import type { RepoItem, ConnectRepoPayload, CreateRepoPayload } from "@/lib/types";

type Tab = "existing" | "create";

interface RepoSetupProps {
  repos:       RepoItem[];
  reposLoading: boolean;
  onLoadRepos: () => void;
  onConnect:   (p: ConnectRepoPayload) => Promise<void>;
  onCreate:    (p: CreateRepoPayload)  => Promise<void>;
}

export function RepoSetup({
  repos,
  reposLoading,
  onLoadRepos,
  onConnect,
  onCreate,
}: RepoSetupProps) {
  const [tab, setTab]           = useState<Tab>("existing");
  const [selectedRepo, setSelectedRepo] = useState("");
  const [branch, setBranch]     = useState("main");
  const [repoName, setRepoName] = useState("");
  const [isPrivate, setIsPrivate] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError]       = useState<string | null>(null);

  useEffect(() => { onLoadRepos(); }, [onLoadRepos]);

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      if (tab === "existing") {
        if (!selectedRepo) { setError("Select a repository."); return; }
        const [owner, ...rest] = selectedRepo.split("/");
        await onConnect({ owner, name: rest.join("/"), branch });
      } else {
        if (!repoName.trim()) { setError("Enter a repository name."); return; }
        await onCreate({ name: repoName.trim(), private: isPrivate, branch });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width:        "100%",
    background:   "var(--surface-2)",
    border:       "1px solid var(--border)",
    borderRadius: "8px",
    padding:      "8px 12px",
    fontSize:     "13px",
    color:        "var(--fg)",
    fontFamily:   "var(--font-geist-sans)",
    outline:      "none",
    boxSizing:    "border-box",
  };

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
          Choose a repository
        </h2>
        <p style={{ fontSize: "13px", color: "var(--muted)", margin: "0 0 24px", fontFamily: "var(--font-geist-sans)" }}>
          GitMyPhotos will store your photos here.
        </p>

        {/* Tabs */}
        <div style={{ display: "flex", gap: "4px", marginBottom: "20px", background: "var(--surface-2)", borderRadius: "8px", padding: "3px" }}>
          {(["existing", "create"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                flex:         1,
                padding:      "6px",
                fontSize:     "13px",
                fontWeight:   500,
                borderRadius: "6px",
                border:       "none",
                cursor:       "pointer",
                fontFamily:   "var(--font-geist-sans)",
                background:   tab === t ? "var(--surface)" : "transparent",
                color:        tab === t ? "var(--fg)" : "var(--muted)",
                transition:   "background 0.15s, color 0.15s",
              }}
            >
              {t === "existing" ? "Use existing" : "Create new"}
            </button>
          ))}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {tab === "existing" ? (
            <>
              <div>
                <label style={{ fontSize: "12px", color: "var(--muted-fg)", fontFamily: "var(--font-geist-sans)", display: "block", marginBottom: "6px" }}>Repository</label>
                {reposLoading ? (
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 0", color: "var(--muted)", fontSize: "13px", fontFamily: "var(--font-geist-sans)" }}>
                    <Spinner size={14} /> Loading repositories…
                  </div>
                ) : (
                  <select value={selectedRepo} onChange={(e) => setSelectedRepo(e.target.value)} style={inputStyle}>
                    <option value="">Select a repository</option>
                    {repos.map((r) => (
                      <option key={r.full_name} value={r.full_name}>{r.full_name}</option>
                    ))}
                  </select>
                )}
              </div>
              <div>
                <label style={{ fontSize: "12px", color: "var(--muted-fg)", fontFamily: "var(--font-geist-sans)", display: "block", marginBottom: "6px" }}>Branch</label>
                <input value={branch} onChange={(e) => setBranch(e.target.value)} style={inputStyle} placeholder="main" />
              </div>
            </>
          ) : (
            <>
              <div>
                <label style={{ fontSize: "12px", color: "var(--muted-fg)", fontFamily: "var(--font-geist-sans)", display: "block", marginBottom: "6px" }}>Repository name</label>
                <input value={repoName} onChange={(e) => setRepoName(e.target.value)} style={inputStyle} placeholder="my-photos" />
              </div>
              <div>
                <label style={{ fontSize: "12px", color: "var(--muted-fg)", fontFamily: "var(--font-geist-sans)", display: "block", marginBottom: "6px" }}>Branch</label>
                <input value={branch} onChange={(e) => setBranch(e.target.value)} style={inputStyle} placeholder="main" />
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <input type="checkbox" id="private" checked={isPrivate} onChange={(e) => setIsPrivate(e.target.checked)} />
                <label htmlFor="private" style={{ fontSize: "13px", color: "var(--fg-2)", fontFamily: "var(--font-geist-sans)", cursor: "pointer" }}>
                  Private repository
                </label>
              </div>
            </>
          )}

          {error && (
            <p style={{ fontSize: "12px", color: "var(--danger)", margin: 0, fontFamily: "var(--font-geist-sans)" }}>{error}</p>
          )}

          <Button variant="primary" size="md" fullWidth loading={submitting} onClick={handleSubmit}>
            {tab === "existing" ? "Connect repository" : "Create & connect"}
          </Button>
        </div>
      </div>
    </div>
  );
}
