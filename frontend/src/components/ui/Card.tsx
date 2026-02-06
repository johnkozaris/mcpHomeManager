import type { HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
  accent?: string;
}

export function Card({
  hoverable,
  accent,
  className = "",
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={[
        "card p-5",
        accent && "border-l-[3px]",
        hoverable &&
          "hover:border-line-hover hover:shadow-elevated transition-all duration-200 cursor-pointer",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      style={accent ? { borderLeftColor: accent } : undefined}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className = "",
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`flex items-center justify-between mb-4 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  className = "",
  children,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={`text-lg font-bold text-ink ${className}`} {...props}>
      {children}
    </h3>
  );
}
