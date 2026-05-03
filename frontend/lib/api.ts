import type {
  AuthState,
  RepoHealth,
  RepoItem,
  CurrentRepo,
  ConnectRepoPayload,
  CreateRepoPayload,
  Manifest,
  PhotoMeta,
  AppSettings,
} from "./types";

const BASE = "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`[${res.status}] ${path}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Auth ───────────────────────────────────────────────────────────────────

export const api = {
  auth: {
    state: (): Promise<AuthState> => req("/auth"),
    login: () => { window.location.href = `${BASE}/auth/login`; },
    logout: (): Promise<{ status: string }> =>
      req("/logout", { method: "POST" }),
  },

  // ── Repo ─────────────────────────────────────────────────────────────────
  repo: {
    current: (): Promise<CurrentRepo> => req("/repo/current"),
    health: (): Promise<RepoHealth> => req("/repo/health"),
    list: (): Promise<RepoItem[]> =>
      req<{ repos: RepoItem[] }>("/repo/list").then((r) => r.repos),
    connect: (data: ConnectRepoPayload): Promise<{ status: string }> =>
      req("/repo/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),
    create: (data: CreateRepoPayload): Promise<{ status: string }> =>
      req("/repo/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),
    scaffold: (): Promise<{ status: string }> =>
      req("/repo/scaffold", { method: "POST" }),
    disconnect: (): Promise<{ status: string }> =>
      req("/repo/disconnect", { method: "POST" }),
  },

  // ── Photos ────────────────────────────────────────────────────────────────
  photos: {
    manifest: (): Promise<Manifest> => req("/manifest"),
    meta: (id: string): Promise<PhotoMeta> => req(`/photo/${id}/meta`),
    thumbUrl: (id: string) => `${BASE}/thumb/${id}`,
    previewUrl: (id: string) => `${BASE}/preview/${id}`,
    originalUrl: (id: string) => `${BASE}/original/${id}`,
  },

  // ── Upload ────────────────────────────────────────────────────────────────
  upload: {
    file: (file: File): Promise<{ id: string; status: string }> => {
      const form = new FormData();
      form.append("file", file);
      return req("/upload", { method: "POST", body: form });
    },
  },

  // ── Settings ──────────────────────────────────────────────────────────────
  settings: {
    get: (): Promise<AppSettings> => req("/settings"),
    update: (patch: Partial<AppSettings>): Promise<AppSettings> =>
      req("/settings", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      }),
    cacheStats: (): Promise<{
      thumb_count: number;
      thumb_size_mb: number;
      preview_count: number;
      preview_size_mb: number;
    }> => req("/cache/stats"),
  },
};
