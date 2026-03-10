import type { HTMLAttributes } from "react";

type Variant = "default" | "positive" | "caution" | "critical" | "brand";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

const styles: Record<Variant, string> = {
  default: "bg-stone-bg text-ink-secondary",
  positive: "bg-sage-bg text-sage",
  caution: "bg-clay-bg text-clay",
  critical: "bg-rust-bg text-rust",
  brand: "bg-terra-bg text-terra",
};

export function Badge({
  variant = "default",
  className = "",
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold",
        styles[variant],
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </span>
  );
}
