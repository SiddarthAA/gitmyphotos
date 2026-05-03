"use client";

import { useState } from "react";
import { Spinner } from "@/components/ui/Spinner";
import { ConnectGitHub } from "@/components/auth/ConnectGitHub";
import { RepoSetup } from "@/components/repo/RepoSetup";
import { RepoHealth } from "@/components/repo/RepoHealth";
import { AppShell } from "@/components/shell/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { useRepo } from "@/hooks/useRepo";

export default function Page() {
  const { loading: authLoading, authed, logout, ...authRest } = useAuth();
  const {
    loading: repoLoading,
    health,
    current,
    repos,
    repoListLoading,
    refetch,
    connect,
    create,
    scaffold,
    disconnect,
    loadRepos,
  } = useRepo(authed);

  const [scaffolding, setScaffolding] = useState(false);

  if (authLoading) return <FullScreenSpinner />;

  if (!authed) {
    return (
      <ConnectGitHub
        onConnect={() => { window.location.href = "/api/auth/login"; }}
      />
    );
  }

  if (repoLoading && !health && !current) return <FullScreenSpinner />;

  if (!current) {
    return (
      <RepoSetup
        repos={repos}
        reposLoading={repoListLoading}
        onLoadRepos={loadRepos}
        onConnect={async (p) => { await connect(p.owner, p.name, p.branch); refetch(); }}
        onCreate={async (p) => { await create(p.name, p.branch, p.private); refetch(); }}
      />
    );
  }

  if (!health?.initialized) {
    return (
      <RepoHealth
        health={health}
        current={current}
        onRefetch={refetch}
        scaffolding={scaffolding}
        onScaffold={async () => {
          setScaffolding(true);
          try { await scaffold(); refetch(); }
          finally { setScaffolding(false); }
        }}
      />
    );
  }

  const authState = {
    loading:    authLoading,
    authed,
    username:   authRest.username,
    name:       authRest.name,
    avatar_url: authRest.avatar_url,
  };

  return (
    <AppShell
      auth={authState}
      current={current}
      health={health}
      onDisconnect={async () => { await disconnect(); refetch(); }}
      onLogout={logout}
    />
  );
}

function FullScreenSpinner() {
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
      <Spinner size={28} color="var(--muted)" />
    </div>
  );
}

