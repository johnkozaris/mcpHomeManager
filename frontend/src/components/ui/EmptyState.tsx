import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  color?: string;
  children?: React.ReactNode;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  color,
  children,
}: EmptyStateProps) {
  const accentColor = color || "var(--ink-tertiary)";
  return (
    <div className="py-16 px-4 max-w-sm mx-auto text-center">
      <Icon
        size={28}
        style={{ color: accentColor }}
        className="mx-auto mb-4"
      />
      <h3 className="text-base font-semibold text-ink mb-1">{title}</h3>
      <p className="text-sm text-ink-tertiary leading-relaxed mb-5">
        {description}
      </p>
      {children && (
        <div className="flex items-center justify-center gap-3">
          {children}
        </div>
      )}
    </div>
  );
}
