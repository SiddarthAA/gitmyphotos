"use client";

import { Panel } from "@/components/ui/Panel";
import { Button } from "@/components/ui/Button";
import { buildPreviewUrl, formatBytes, formatDate } from "@/lib/utils";
import type { Photo } from "@/lib/types";
import { Download, Github, MapPin, Camera } from "lucide-react";

interface PhotoDetailProps {
  photo:   Photo | null;
  onClose: () => void;
}

export function PhotoDetail({ photo, onClose }: PhotoDetailProps) {
  if (!photo) return null;

  const exif = photo.exif;
  const gps  = photo.gps;

  return (
    <Panel open={!!photo} onClose={onClose} title={photo.filename} width={380} side="right">
      <div style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "16px" }}>

        {/* Preview */}
        <img
          src={buildPreviewUrl(photo.id)}
          alt={photo.filename}
          style={{
            width:        "100%",
            borderRadius: "8px",
            objectFit:    "cover",
            maxHeight:    "220px",
            border:       "1px solid var(--border)",
          }}
        />

        {/* Core info */}
        <InfoBlock title="File">
          <InfoRow label="Name"     value={photo.filename} />
          <InfoRow label="Date"     value={formatDate(photo.captured_at ?? photo.uploaded_at)} />
          <InfoRow label="Size"     value={formatBytes(photo.file_size)} />
          <InfoRow label="Mime"     value={photo.mime_type} />
          {photo.width && photo.height && (
            <InfoRow label="Dimensions" value={`${photo.width} × ${photo.height}`} />
          )}
        </InfoBlock>

        {/* EXIF */}
        {exif && Object.keys(exif).length > 0 && (
          <InfoBlock title="EXIF" icon={<Camera size={12} />}>
            {exif.make      && <InfoRow label="Camera"   value={`${exif.make} ${exif.model ?? ""}`} />}
            {exif.iso       && <InfoRow label="ISO"      value={String(exif.iso)} />}
            {exif.aperture  && <InfoRow label="Aperture" value={`ƒ/${exif.aperture}`} />}
            {exif.shutter   && <InfoRow label="Shutter"  value={exif.shutter} />}
            {exif.focal_length && <InfoRow label="Focal" value={`${exif.focal_length}mm`} />}
          </InfoBlock>
        )}

        {/* GPS */}
        {gps && gps.lat !== undefined && gps.lng !== undefined && (
          <InfoBlock title="Location" icon={<MapPin size={12} />}>
            <InfoRow label="Lat" value={gps.lat.toFixed(6)} />
            <InfoRow label="Lon" value={gps.lng.toFixed(6)} />
            {gps.altitude !== undefined && <InfoRow label="Alt" value={`${gps.altitude.toFixed(0)}m`} />}
            <a
              href={`https://maps.google.com/?q=${gps.lat},${gps.lng}`}
              target="_blank"
              rel="noreferrer"
              style={{ fontSize: "11px", color: "var(--muted-fg)", fontFamily: "var(--font-geist-sans)", textDecoration: "underline" }}
            >
              Open in Maps
            </a>
          </InfoBlock>
        )}

        {/* Storage path */}
        {photo.original_path && (
          <InfoBlock title="GitHub" icon={<Github size={12} />}>
            <span
              style={{
                fontSize:     "11px",
                fontFamily:   "var(--font-geist-mono)",
                color:        "var(--muted-fg)",
                wordBreak:    "break-all",
              }}
            >
              {photo.original_path}
            </span>
          </InfoBlock>
        )}

        {/* Actions */}
        <Button
          variant="ghost"
          size="md"
          fullWidth
          onClick={() => {
            window.open(`/api/photos/${photo.id}/original`, "_blank");
          }}
        >
          <Download size={14} />
          Download Original
        </Button>
      </div>
    </Panel>
  );
}

function InfoBlock({ title, icon, children }: { title: string; icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: "5px", marginBottom: "8px" }}>
        {icon && <span style={{ color: "var(--muted)" }}>{icon}</span>}
        <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--muted)", fontFamily: "var(--font-geist-sans)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
          {title}
        </span>
      </div>
      <div
        style={{
          background:   "var(--surface-2)",
          border:       "1px solid var(--border)",
          borderRadius: "8px",
          padding:      "10px 12px",
          display:      "flex",
          flexDirection: "column",
          gap:          "6px",
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
      <span style={{ fontSize: "11px", color: "var(--muted)", fontFamily: "var(--font-geist-sans)", flexShrink: 0 }}>{label}</span>
      <span style={{ fontSize: "11px", color: "var(--fg-2)", fontFamily: "var(--font-geist-mono)", textAlign: "right", wordBreak: "break-all" }}>{value}</span>
    </div>
  );
}
