"use client";

type PillVariant = "default" | "success" | "warning" | "error" | "pushing" | "muted";

const pillColors: Record<PillVariant, { bg: string; color: string }> = {
  default:  { bg: "rgba(255,255,255,0.08)", color: "var(--fg-2)" },
  success:  { bg: "rgba( 74,222,128,0.12)", color: "#4ade80"    },
  warning:  { bg: "rgba(251,191, 36,0.12)", color: "#fbbf24"    },
  error:    { bg: "rgba(248,113,113,0.12)", color: "var(--danger)" },
  pushing:  { bg: "rgba(129,140,248,0.12)", color: "#818cf8"    },
  muted:    { bg: "rgba(113,113,122,0.12)", color: "var(--muted)" },
};

interface PillProps {
  label:     string;
  variant?:  PillVariant;
  dot?:      boolean;
}

export function Pill({ label, variant = "default", dot = false }: PillProps) {
  const { bg, color } = pillColors[variant];
  return (
    <span
      style={{
        display:        "inline-flex",
        alignItems:     "center",
        gap:            "5px",
        padding:        "2px 8px",
        borderRadius:   "999px",
        fontSize:       "11px",
        fontWeight:     500,
        fontFamily:     "var(--font-geist-mono)",
        letterSpacing:  "0.02em",
        background:     bg,
        color,
        whiteSpace:     "nowrap",
      }}
    >
      {dot && (
        <span
          style={{
            width:        "5px",
            height:       "5px",
            borderRadius: "50%",
            background:   color,
            flexShrink:   0,
          }}
        />
      )}
      {label}
    </span>
  );
}
