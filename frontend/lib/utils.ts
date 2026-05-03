import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function formatDate(iso: string): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatMonthYear(iso: string): string {
  if (!iso) return "Unknown";
  return new Date(iso).toLocaleDateString("en-GB", {
    month: "long",
    year: "numeric",
  });
}

export function groupByMonth(
  photos: import("./types").Photo[]
): Record<string, import("./types").Photo[]> {
  const groups: Record<string, import("./types").Photo[]> = {};
  for (const p of photos) {
    const key = formatMonthYear(p.captured_at ?? p.uploaded_at);
    if (!groups[key]) groups[key] = [];
    groups[key].push(p);
  }
  return groups;
}

export function buildThumbUrl(id: string): string {
  return `/api/thumb/${id}`;
}

export function buildPreviewUrl(id: string): string {
  return `/api/preview/${id}`;
}

export function truncateFilename(name: string, max = 26): string {
  if (name.length <= max) return name;
  const ext = name.slice(name.lastIndexOf("."));
  const base = name.slice(0, max - ext.length - 3);
  return `${base}...${ext}`;
}
