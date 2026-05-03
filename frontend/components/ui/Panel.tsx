"use client";

import { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";

interface PanelProps {
  open:       boolean;
  onClose:    () => void;
  title?:     string;
  width?:     number | string;
  children:   React.ReactNode;
  side?:      "left" | "right";
}

export function Panel({
  open,
  onClose,
  title,
  width   = 400,
  children,
  side    = "right",
}: PanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // ESC to close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (open) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            style={{
              position:   "fixed",
              inset:      0,
              background: "rgba(0,0,0,0.5)",
              zIndex:     50,
            }}
          />

          {/* Panel */}
          <motion.div
            key="panel"
            ref={panelRef}
            initial={{ x: side === "right" ? "100%" : "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: side === "right" ? "100%" : "-100%" }}
            transition={{ type: "spring", stiffness: 320, damping: 34 }}
            style={{
              position:   "fixed",
              top:        0,
              [side]:     0,
              bottom:     0,
              width:      typeof width === "number" ? `${width}px` : width,
              background: "var(--surface)",
              borderLeft: side === "right" ? "1px solid var(--border)" : "none",
              borderRight: side === "left" ? "1px solid var(--border)" : "none",
              zIndex:     51,
              display:    "flex",
              flexDirection: "column",
              overflow:   "hidden",
            }}
          >
            {/* Header */}
            {title && (
              <div
                style={{
                  display:       "flex",
                  alignItems:    "center",
                  justifyContent:"space-between",
                  padding:        "16px 20px",
                  borderBottom:   "1px solid var(--border)",
                  flexShrink:     0,
                }}
              >
                <span
                  style={{
                    fontSize:   "14px",
                    fontWeight: 600,
                    color:      "var(--fg)",
                    fontFamily: "var(--font-geist-sans)",
                  }}
                >
                  {title}
                </span>
                <button
                  onClick={onClose}
                  style={{
                    background: "transparent",
                    border:     "none",
                    cursor:     "pointer",
                    color:      "var(--muted)",
                    padding:    "4px",
                    display:    "flex",
                    alignItems: "center",
                    borderRadius: "4px",
                  }}
                  aria-label="Close panel"
                >
                  <X size={16} />
                </button>
              </div>
            )}

            {/* Body */}
            <div style={{ flex: 1, overflow: "auto" }}>{children}</div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
