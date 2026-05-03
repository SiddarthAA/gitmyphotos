// ── Authentication ─────────────────────────────────────────────────────────

export interface AuthState {
  authed: boolean;
  username: string | null;
  avatar_url: string | null;
  name: string | null;
}

// ── Repository ─────────────────────────────────────────────────────────────

export interface RepoHealth {
  connected: boolean;
  yml: boolean;
  manifest: boolean;
  folders: boolean;
  initialized: boolean;
  photo_count: number;
  last_upload: string | null;
  total_size_mb: number | null;
}

export interface RepoItem {
  name: string;
  full_name: string;
  owner: string;
  private: boolean;
  default_branch: string;
}

export interface CurrentRepo {
  connected: boolean;
  owner: string | null;
  name: string | null;
  branch: string | null;
  private: boolean | null;
}

export interface ConnectRepoPayload {
  owner: string;
  name: string;
  branch: string;
}

export interface CreateRepoPayload {
  name: string;
  branch: string;
  private: boolean;
}

// ── Photos ─────────────────────────────────────────────────────────────────

export interface EXIF {
  make?: string;
  model?: string;
  lens?: string;
  focal_length?: string;
  aperture?: string;
  shutter?: string;
  iso?: number;
  flash?: string;
  width?: number;
  height?: number;
}

export interface GPS {
  lat?: number;
  lng?: number;
  altitude?: number;
  city?: string;
  country?: string;
}

export interface PhotoMeta {
  id: string;
  filename: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  width: number | null;
  height: number | null;
  captured_at: string | null;
  uploaded_at: string;
  exif: EXIF | null;
  gps: GPS | null;
  thumb_path: string | null;
  original_path: string | null;
  meta_path: string | null;
}

export interface Photo {
  id: string;
  filename: string;
  original_filename: string;
  captured_at: string | null;
  uploaded_at: string;
  thumb_path: string | null;
  original_path: string | null;
  mime_type: string;
  file_size: number;
  width: number | null;
  height: number | null;
  exif?: EXIF | null;
  gps?: GPS | null;
  thumb_sha?: string | null;
  original_sha?: string | null;
}

export interface Manifest {
  version: number;
  last_updated: string;
  photo_count: number;
  photos: Photo[];
}

// ── Upload ─────────────────────────────────────────────────────────────────

export type UploadStage =
  | "idle"
  | "reading"
  | "exif"
  | "thumb"
  | "meta"
  | "queued"
  | "pushing"
  | "done"
  | "error";

export interface UploadQueueItem {
  id: string;
  file: File;
  stage: UploadStage;
  progress: number;
  previewUrl: string;
  error?: string;
  photoId?: string;
}

// ── Settings ───────────────────────────────────────────────────────────────

export interface AppSettings {
  thumb_width: number;
  preview_width: number;
  cache_max_preview_gb: number;
}
