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
  const accentColor = color || "var(--terra)";
  return (
    <div className="relative flex flex-col items-center justify-center py-20 px-4 overflow-hidden">
      {/* Decorative background shapes */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden>
        <svg
          className="absolute -top-10 right-[20%] w-40 h-40 opacity-[0.04]"
          viewBox="0 0 160 160"
        >
          <circle cx="80" cy="80" r="78" fill={accentColor} />
        </svg>
        <svg
          className="absolute -bottom-8 left-[15%] w-28 h-28 opacity-[0.03]"
          viewBox="0 0 112 112"
        >
          <rect
            x="8"
            y="8"
            width="96"
            height="96"
            rx="20"
            fill={accentColor}
            transform="rotate(-12 56 56)"
          />
        </svg>
      </div>

      <div className="relative">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5 mx-auto"
          style={{ backgroundColor: accentColor, opacity: 0.9 }}
        >
          <Icon size={28} className="text-white" />
        </div>
        <h3 className="text-xl font-bold text-ink mb-2 text-center">{title}</h3>
        <p className="text-sm text-ink-secondary text-center max-w-sm mb-6">
          {description}
        </p>
        {children && (
          <div className="flex items-center justify-center gap-3">
            {children}
          </div>
        )}
      </div>
    </div>
  );
}
