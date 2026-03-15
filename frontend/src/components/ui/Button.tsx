import { type ButtonHTMLAttributes, type Ref } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "inverse";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  ref?: Ref<HTMLButtonElement>;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-terra text-white hover:bg-terra-light active:bg-terra-dark shadow-subtle",
  secondary:
    "bg-surface text-ink border border-line-strong hover:border-line-hover hover:bg-surface-hover",
  ghost: "text-ink-secondary hover:text-ink hover:bg-canvas-tertiary",
  danger:
    "bg-rust-bg text-rust border border-rust hover:bg-rust hover:text-white",
  inverse:
    "bg-white text-[var(--terra-dark)] hover:bg-white/90 shadow-lg font-bold",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-sm gap-1.5",
  md: "h-9 px-4 text-sm gap-2",
  lg: "h-11 px-6 text-base gap-2",
};

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  ref,
  ...props
}: ButtonProps) {
  return (
    <button
      ref={ref}
      className={[
        "inline-flex items-center justify-center font-semibold rounded-lg",
        "transition-all duration-150 active:scale-[0.97]",
        "focus-visible:outline-none focus-visible:shadow-focus",
        "disabled:opacity-40 disabled:pointer-events-none",
        variants[variant],
        sizes[size],
        className,
      ].join(" ")}
      {...props}
    />
  );
}
