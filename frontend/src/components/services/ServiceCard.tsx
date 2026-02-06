import { Link } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import type { ServiceConnection } from "@/lib/types";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { StatusDot } from "@/components/ui/StatusDot";
import { ServiceIconBadge, getServiceMeta } from "@/lib/service-meta";

export function ServiceCard({ service }: { service: ServiceConnection }) {
  const meta = getServiceMeta(service.service_type);
  const qc = useQueryClient();

  function handlePrefetch() {
    qc.prefetchQuery({
      queryKey: ["services", service.id],
      queryFn: () => api.services.get(service.id),
      staleTime: 30_000,
    });
  }

  return (
    <Link
      to="/services/$id"
      params={{ id: service.id }}
      onMouseEnter={handlePrefetch}
      onFocus={handlePrefetch}
      className="card p-5 flex flex-col gap-3 group transition-all duration-200"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <ServiceIconBadge type={service.service_type} size="lg" />
          <div>
            <p className="text-sm font-semibold text-ink group-hover:text-terra transition-colors">
              {service.display_name}
            </p>
            <p className="text-xs text-ink-tertiary">{meta.description}</p>
          </div>
        </div>
      </div>
      <div className="flex items-center justify-between mt-auto">
        <div className="flex items-center gap-2">
          <StatusDot status={service.health_status} />
          {!service.is_enabled && <Badge variant="caution">paused</Badge>}
        </div>
        <Badge variant="brand">{service.tool_count} tools</Badge>
      </div>
      <p className="text-xs text-ink-faint font-mono truncate">
        {service.base_url}
      </p>
    </Link>
  );
}
