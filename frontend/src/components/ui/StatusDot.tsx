import type { HealthStatus } from "@/lib/types";

const colorMap: Record<HealthStatus, string> = {
  healthy: "bg-sage",
  unhealthy: "bg-rust",
  unknown: "bg-stone",
};

export function StatusDot({ status }: { status: HealthStatus }) {
  return (
    <span className="relative inline-flex items-center justify-center w-3 h-3">
      <span className={["w-2 h-2 rounded-full", colorMap[status]].join(" ")} />
    </span>
  );
}
