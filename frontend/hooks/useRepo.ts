"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { RepoHealth, RepoItem, CurrentRepo } from "@/lib/types";

interface UseRepoReturn {
  loading: boolean;
  health: RepoHealth | null;
  current: CurrentRepo | null;
  repos: RepoItem[];
  repoListLoading: boolean;
  refetch: () => Promise<void>;
  connect: (owner: string, name: string, branch: string) => Promise<void>;
  create: (name: string, branch: string, priv: boolean) => Promise<void>;
  scaffold: () => Promise<void>;
  disconnect: () => Promise<void>;
  loadRepos: () => Promise<void>;
}

export function useRepo(enabled = true): UseRepoReturn {
  const [loading, setLoading]             = useState(true);
  const [health, setHealth]               = useState<RepoHealth | null>(null);
  const [current, setCurrent]             = useState<CurrentRepo | null>(null);
  const [repos, setRepos]                 = useState<RepoItem[]>([]);
  const [repoListLoading, setRepoListLoading] = useState(false);

  const fetch = useCallback(async () => {
    if (!enabled) return;
    try {
      // Fetch current connection first — health() 400s when no repo connected
      const c = await api.repo.current();
      const connected = c?.connected;
      setCurrent(connected ? c : null);
      if (connected) {
        const h = await api.repo.health();
        setHealth(h);
      } else {
        setHealth(null);
      }
    } catch {
      setHealth(null);
      setCurrent(null);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (enabled) fetch();
  }, [enabled, fetch]);

  const connect = useCallback(async (owner: string, name: string, branch: string) => {
    await api.repo.connect({ owner, name, branch });
    await fetch();
  }, [fetch]);

  const create = useCallback(async (name: string, branch: string, priv: boolean) => {
    await api.repo.create({ name, branch, private: priv });
    await fetch();
  }, [fetch]);

  const scaffold = useCallback(async () => {
    await api.repo.scaffold();
    await fetch();
  }, [fetch]);

  const disconnect = useCallback(async () => {
    await api.repo.disconnect();
    setHealth(null);
    setCurrent(null);
  }, []);

  const loadRepos = useCallback(async () => {
    setRepoListLoading(true);
    try {
      const list = await api.repo.list();
      setRepos(list);
    } finally {
      setRepoListLoading(false);
    }
  }, []);

  return {
    loading,
    health,
    current,
    repos,
    repoListLoading,
    refetch: fetch,
    connect,
    create,
    scaffold,
    disconnect,
    loadRepos,
  };
}
