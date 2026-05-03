"use client";

import { useState } from "react";
import { Nav } from "@/components/nav/Nav";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { PhotoGrid } from "@/components/photos/PhotoGrid";
import { PhotoDetail } from "@/components/photos/PhotoDetail";
import { Settings } from "@/components/ui/Settings";
import { useManifest } from "@/hooks/useManifest";
import { useUpload } from "@/hooks/useUpload";
import type { AuthState, CurrentRepo, RepoHealth, Photo } from "@/lib/types";

interface AppShellProps {
  auth:         AuthState;
  current:      CurrentRepo;
  health:       RepoHealth;
  onDisconnect: () => Promise<void>;
  onLogout:     () => void;
}

export function AppShell({ auth, current, health, onDisconnect, onLogout }: AppShellProps) {
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);
  const [settingsOpen,  setSettingsOpen]  = useState(false);

  const { photos, loading: manifestLoading, error: manifestError, refetch } = useManifest(true);

  const { queue, addFiles, clearDone, batchCountdown, batchSize } = useUpload(refetch);

  return (
    <div
      style={{
        display:        "flex",
        flexDirection:  "column",
        height:         "100vh",
        background:     "var(--bg)",
        overflow:       "hidden",
      }}
    >
      {/* Top nav */}
      <Nav
        auth={auth}
        current={current}
        onSettings={() => setSettingsOpen(true)}
      />

      {/* Body */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Sidebar */}
        <Sidebar
          queue={queue}
          batchCountdown={batchCountdown}
          batchSize={batchSize}
          health={health}
          onFiles={addFiles}
          onClearDone={clearDone}
        />

        {/* Photo grid */}
        <PhotoGrid
          photos={photos}
          loading={manifestLoading}
          error={manifestError}
          onSelect={setSelectedPhoto}
        />
      </div>

      {/* Photo detail panel */}
      <PhotoDetail
        photo={selectedPhoto}
        onClose={() => setSelectedPhoto(null)}
      />

      {/* Settings panel */}
      <Settings
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        auth={auth}
        current={current}
        onDisconnect={onDisconnect}
        onLogout={onLogout}
      />
    </div>
  );
}
