import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon?: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  featured?: boolean;
}

export function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  iconColor,
  iconBg,
  featured,
}: StatCardProps) {
  if (featured) {
    return (
      <div
        className="relative overflow-hidden rounded-2xl p-5 text-white shadow-card"
        style={{
          background: `linear-gradient(135deg, ${iconColor || "var(--terra)"}, color-mix(in srgb, ${iconColor || "var(--terra)"} 70%, var(--ink)))`,
        }}
      >
        {/* Bold decorative circle */}
        <div
          className="absolute -top-8 -right-8 w-28 h-28 rounded-full"
          style={{ backgroundColor: "rgba(255,255,255,0.15)" }}
          aria-hidden
        />
        <div
          className="absolute -bottom-4 -right-4 w-16 h-16 rounded-full"
          style={{ backgroundColor: "rgba(255,255,255,0.08)" }}
          aria-hidden
        />
        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-wider text-white/70 mb-2">
            {label}
          </p>
          <p className="text-3xl font-bold tracking-tight">{value}</p>
          {sub && <p className="text-sm text-white/60 mt-1">{sub}</p>}
        </div>
        {Icon && (
          <div className="absolute top-5 right-5">
            <Icon size={22} className="text-white/40" />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="card relative overflow-hidden p-5">
      {/* Decorative half-circle — visible, Bauhaus-style */}
      {iconColor && (
        <div
          className="absolute -top-10 -right-10 w-24 h-24 rounded-full pointer-events-none"
          style={{
            backgroundColor: iconColor
              ? `color-mix(in srgb, ${iconColor} 8%, transparent)`
              : undefined,
          }}
          aria-hidden
        />
      )}
      <div className="relative flex items-start justify-between">
        <div>
          <p className="section-label mb-2">{label}</p>
          <p className="text-2xl font-bold tracking-tight text-ink">{value}</p>
          {sub && <p className="text-xs text-ink-secondary mt-1">{sub}</p>}
        </div>
        {Icon && (
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
            style={{
              backgroundColor:
                iconBg ??
                (iconColor
                  ? `color-mix(in srgb, ${iconColor} 12%, transparent)`
                  : "var(--canvas-tertiary)"),
            }}
          >
            <Icon
              size={20}
              style={{ color: iconColor ?? "var(--ink-tertiary)" }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
