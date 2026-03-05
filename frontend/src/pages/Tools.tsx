import { useState } from "react";
import {
  useTools,
  useUpdateToolPermission,
} from "@/hooks/useServices";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { QueryState } from "@/components/ui/QueryState";
import { Input } from "@/components/ui/Input";
import { EmptyState } from "@/components/ui/EmptyState";
import { ToolList } from "@/components/services/ToolList";
import { getServiceMeta } from "@/lib/service-meta";
import { Wrench } from "lucide-react";
import type { ServiceType } from "@/lib/types";
import { useTranslation } from "react-i18next";

type StatusFilter = "all" | "enabled" | "disabled";

export function Tools() {
  const { t } = useTranslation("tools", { keyPrefix: "page" });
  const { data: tools, isLoading, isError, error } = useTools();
  const updateToolPermission = useUpdateToolPermission();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 200);
  const [filterType, setFilterType] = useState<ServiceType | "all">("all");
  const [filterStatus, setFilterStatus] = useState<StatusFilter>("all");
  const [actionError, setActionError] = useState<string | null>(null);

  const requireServiceId = (toolName: string, serviceId: string | null): string | null => {
    if (serviceId) {
      setActionError(null);
      return serviceId;
    }
    setActionError(
      t("errors.missingService", { toolName }),
    );
    return null;
  };

  const filtered = tools?.filter((tool) => {
    if (filterType !== "all" && tool.service_type !== filterType) return false;
    if (filterStatus === "enabled" && !tool.is_enabled) return false;
    if (filterStatus === "disabled" && tool.is_enabled) return false;
    if (!debouncedSearch) return true;
    const q = debouncedSearch.toLowerCase();
    return (
      tool.name.toLowerCase().includes(q) ||
      tool.description.toLowerCase().includes(q)
    );
  });

  const serviceTypes = [
    ...new Set(tools?.map((tool) => tool.service_type) ?? []),
  ];
  const enabledCount = tools?.filter((tool) => tool.is_enabled).length ?? 0;
  const disabledCount = (tools?.length ?? 0) - enabledCount;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-header">{t("title")}</h1>
        <p className="page-description">
          {tools && tools.length > 0
            ? t("description.withCounts", {
                toolsCount: tools.length,
                serviceCount: serviceTypes.length,
                enabledCount,
              })
            : t("description.empty")}
        </p>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="w-full sm:w-72">
          <Input
            placeholder={t("filters.searchPlaceholder")}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setActionError(null);
            }}
          />
        </div>
        <div className="flex items-center gap-1.5">
          {(["all", "enabled", "disabled"] as const).map((status) => (
            <button
              key={status}
              onClick={() => {
                setFilterStatus(status);
                setActionError(null);
              }}
              className={`chip ${filterStatus === status ? "chip-active" : "chip-inactive"}`}
            >
              {status === "all"
                ? t("filters.status.all", { count: tools?.length ?? 0 })
                : status === "enabled"
                  ? t("filters.status.enabled", { count: enabledCount })
                  : t("filters.status.disabled", { count: disabledCount })}
            </button>
          ))}
          <div className="w-px h-5 bg-line-strong mx-1" />
          <button
            onClick={() => {
              setFilterType("all");
              setActionError(null);
            }}
            className={`chip ${filterType === "all" ? "chip-active" : "chip-inactive"}`}
          >
            {t("filters.allServices")}
          </button>
          {serviceTypes.map((type) => {
            const meta = getServiceMeta(type);
            return (
                <button
                  key={type}
                  onClick={() => {
                    setFilterType(type);
                    setActionError(null);
                  }}
                  className={`chip ${filterType === type ? "chip-active" : "chip-inactive"}`}
                >
                {meta.label}
              </button>
            );
          })}
        </div>
      </div>

      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error instanceof Error ? error : null}
        loadingMessage={t("query.loading")}
      >
        {actionError && (
          <div className="mb-3 flex items-center gap-2 py-2 px-3 rounded-lg bg-rust-bg border border-rust">
            <div className="w-1.5 h-1.5 rounded-full bg-rust shrink-0" />
            <p className="text-sm text-rust">{actionError}</p>
          </div>
        )}
        {filtered && filtered.length > 0 ? (
            <ToolList
              tools={filtered}
              showService
              onToggle={(tool, enabled) => {
                const serviceId = requireServiceId(tool.name, tool.service_id);
                if (!serviceId) return;
                updateToolPermission.mutate({
                  serviceId,
                  toolName: tool.name,
                  isEnabled: enabled,
                  descriptionOverride: tool.description_override,
                  parametersSchemaOverride: tool.parameters_schema_override,
                  httpMethodOverride: tool.http_method_override,
                  pathTemplateOverride: tool.path_template_override,
                });
              }}
              onSaveOverrides={(tool, descOverride, schemaOverride, methodOverride, pathOverride) => {
                const serviceId = requireServiceId(tool.name, tool.service_id);
                if (!serviceId) return;
                updateToolPermission.mutate({
                  serviceId,
                  toolName: tool.name,
                  isEnabled: tool.is_enabled,
                  descriptionOverride: descOverride,
                  parametersSchemaOverride: schemaOverride,
                  httpMethodOverride: methodOverride,
                pathTemplateOverride: pathOverride,
              });
            }}
          />
        ) : (
          <EmptyState
            icon={Wrench}
            title={
              search ? t("empty.searchTitle") : t("empty.noToolsTitle")
            }
            description={
              search
                ? t("empty.searchDescription")
                : t("empty.noToolsDescription")
            }
          />
        )}
      </QueryState>
    </div>
  );
}
