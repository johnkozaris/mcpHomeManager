import { useState } from "react";
import {
  useTools,
  useServices,
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

type StatusFilter = "all" | "enabled" | "disabled";

export function Tools() {
  const { data: tools, isLoading, isError, error } = useTools();
  const { data: services } = useServices();
  const updateToolPermission = useUpdateToolPermission();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 200);
  const [filterType, setFilterType] = useState<ServiceType | "all">("all");
  const [filterStatus, setFilterStatus] = useState<StatusFilter>("all");

  const filtered = tools?.filter((t) => {
    if (filterType !== "all" && t.service_type !== filterType) return false;
    if (filterStatus === "enabled" && !t.is_enabled) return false;
    if (filterStatus === "disabled" && t.is_enabled) return false;
    if (!debouncedSearch) return true;
    const q = debouncedSearch.toLowerCase();
    return (
      t.name.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q)
    );
  });

  const serviceTypes = [...new Set(tools?.map((t) => t.service_type) ?? [])];
  const enabledCount = tools?.filter((t) => t.is_enabled).length ?? 0;
  const disabledCount = (tools?.length ?? 0) - enabledCount;

  const serviceIdByType = (() => {
    const map = new Map<ServiceType, string>();
    services?.forEach((s) => {
      if (!map.has(s.service_type)) map.set(s.service_type, s.id);
    });
    return map;
  })();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-header">Tools</h1>
        <p className="page-description">
          {tools && tools.length > 0
            ? `${tools.length} tools across ${serviceTypes.length} service${serviceTypes.length !== 1 ? "s" : ""} · ${enabledCount} enabled for agents`
            : "MCP tools that AI agents can call on your behalf"}
        </p>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="w-full sm:w-72">
          <Input
            placeholder="Search tools…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1.5">
          {(["all", "enabled", "disabled"] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`chip ${filterStatus === status ? "chip-active" : "chip-inactive"}`}
            >
              {status === "all"
                ? `All (${tools?.length ?? 0})`
                : status === "enabled"
                  ? `Enabled (${enabledCount})`
                  : `Disabled (${disabledCount})`}
            </button>
          ))}
          <div className="w-px h-5 bg-line-strong mx-1" />
          <button
            onClick={() => setFilterType("all")}
            className={`chip ${filterType === "all" ? "chip-active" : "chip-inactive"}`}
          >
            All services
          </button>
          {serviceTypes.map((type) => {
            const meta = getServiceMeta(type);
            return (
              <button
                key={type}
                onClick={() => setFilterType(type)}
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
        loadingMessage="Loading tools…"
      >
        {filtered && filtered.length > 0 ? (
          <ToolList
            tools={filtered}
            showService
            onToggle={(toolName, enabled) => {
              const tool = filtered.find((t) => t.name === toolName);
              const serviceId = tool
                ? serviceIdByType.get(tool.service_type)
                : undefined;
              if (serviceId) {
                updateToolPermission.mutate({
                  serviceId,
                  toolName,
                  isEnabled: enabled,
                  descriptionOverride: tool?.description_override,
                  parametersSchemaOverride: tool?.parameters_schema_override,
                  httpMethodOverride: tool?.http_method_override,
                  pathTemplateOverride: tool?.path_template_override,
                });
              }
            }}
            onSaveOverrides={(toolName, descOverride, schemaOverride, methodOverride, pathOverride) => {
              const tool = filtered.find((t) => t.name === toolName);
              const serviceId = tool
                ? serviceIdByType.get(tool.service_type)
                : undefined;
              if (serviceId) {
                updateToolPermission.mutate({
                  serviceId,
                  toolName,
                  isEnabled: tool?.is_enabled ?? true,
                  descriptionOverride: descOverride,
                  parametersSchemaOverride: schemaOverride,
                  httpMethodOverride: methodOverride,
                  pathTemplateOverride: pathOverride,
                });
              }
            }}
          />
        ) : (
          <EmptyState
            icon={Wrench}
            title={search ? "No tools match" : "No tools registered yet"}
            description={
              search
                ? "Try a different search term."
                : "Connect a service first — each one comes with AI-callable tools."
            }
          />
        )}
      </QueryState>
    </div>
  );
}
