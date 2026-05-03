"use client";

interface ShimmerProps {
  width?:  string | number;
  height?: string | number;
  radius?: string | number;
  style?:  React.CSSProperties;
}

export function Shimmer({ width = "100%", height = "100%", radius = 6, style }: ShimmerProps) {
  return (
    <div
      className="shimmer"
      style={{
        width:        typeof width  === "number" ? `${width}px`  : width,
        height:       typeof height === "number" ? `${height}px` : height,
        borderRadius: typeof radius === "number" ? `${radius}px` : radius,
        ...style,
      }}
      aria-hidden
    />
  );
}
