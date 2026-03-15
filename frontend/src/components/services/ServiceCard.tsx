import { Link } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import type { ServiceConnection } from "@/lib/types";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import { Badge } from "@/components/ui/Badge";
import { StatusDot } from "@/components/ui/StatusDot";
import { ServiceIconBadge, getServiceMeta } from "@/lib/service-meta";
import { useTranslation } from "react-i18next";

export function ServiceCard({ service }: { service: ServiceConnection }) {
  const { t } = useTranslation("components", {
    keyPrefix: "services.serviceCard",
  });
  const meta = getServiceMeta(service.service_type);
  const qc = useQueryClient();

  function handlePrefetch() {
    qc.prefetchQuery({
      queryKey: queryKeys.service(service.id),
      queryFn: () => api.services.get(service.id),
      staleTime: 30_000,
    });
  }

  const isUnhealthy = service.health_status === "unhealthy";

  return (
    <Link
      to="/services/$id"
      params={{ id: service.id }}
      onMouseEnter={handlePrefetch}
      onFocus={handlePrefetch}
      className={[
        "card card-interactive p-5 flex flex-col gap-3 group transition-all duration-200",
        isUnhealthy && "border-l-[3px] border-l-rust",
      ]
        .filter(Boolean)
        .join(" ")}
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
          {!service.is_enabled && <Badge variant="caution">{t("paused")}</Badge>}
        </div>
        <Badge variant="brand">{t("toolsCount", { count: service.tool_count })}</Badge>
      </div>
    </Link>
  );
}
