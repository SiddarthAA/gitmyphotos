"use client";

import { forwardRef, ButtonHTMLAttributes } from "react";
import { Spinner } from "./Spinner";

type Variant = "primary" | "ghost" | "danger";
type Size    = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:  Variant;
  size?:     Size;
  loading?:  boolean;
  fullWidth?: boolean;
}

const variantStyles: Record<Variant, React.CSSProperties> = {
  primary: {
    background:  "var(--accent)",
    color:       "var(--accent-fg)",
    border:      "1px solid transparent",
  },
  ghost: {
    background:  "transparent",
    color:       "var(--fg)",
    border:      "1px solid var(--border)",
  },
  danger: {
    background:  "transparent",
    color:       "var(--danger)",
    border:      "1px solid var(--danger)",
  },
};

const sizeStyles: Record<Size, React.CSSProperties> = {
  sm: { padding: "4px 12px",  fontSize: "13px", borderRadius: "6px",  height: "30px" },
  md: { padding: "6px 18px",  fontSize: "14px", borderRadius: "8px",  height: "36px" },
  lg: { padding: "10px 24px", fontSize: "15px", borderRadius: "10px", height: "44px" },
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size    = "md",
      loading = false,
      fullWidth = false,
      disabled,
      children,
      style,
      ...rest
    },
    ref
  ) => {
    const isDisabled = disabled || loading;
    return (
      <button
        ref={ref}
        disabled={isDisabled}
        style={{
          display:        "inline-flex",
          alignItems:     "center",
          justifyContent: "center",
          gap:            "8px",
          fontFamily:     "var(--font-geist-sans)",
          fontWeight:     500,
          cursor:         isDisabled ? "not-allowed" : "pointer",
          opacity:        isDisabled ? 0.5 : 1,
          transition:     "opacity 0.15s, background 0.15s",
          width:          fullWidth ? "100%" : "auto",
          userSelect:     "none",
          whiteSpace:     "nowrap",
          ...variantStyles[variant],
          ...sizeStyles[size],
          ...style,
        }}
        {...rest}
      >
        {loading && <Spinner size={14} />}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
