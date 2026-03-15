import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { MiniAreaChart } from "@/components/ui/MiniAreaChart";
import {
  ScrollText,
  Activity,
  CheckCircle2,
  AlertCircle,
  Timer,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useAuditLog, useServices } from "@/hooks/useServices";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { Card } from "@/components/ui/Card";
import { QueryState } from "@/components/ui/QueryState";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { ServiceIcon } from "@/lib/service-meta";
import { LogEntryDetail } from "@/components/logs/LogEntryDetail";
import { formatRelativeTime } from "@/lib/utils";
import type { ServiceType } from "@/lib/types";
import { useTranslation } from "react-i18next";

const PAGE_SIZE = 50;

function LogsSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-[52px]" />
      <Skeleton className="h-[300px]" />
    </div>
  );
}

export function Logs() {
  const { t } = useTranslation("logs", { keyPrefix: "page" });
  const { data: services } = useServices();
  const [filterService, setFilterService] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [toolSearch, setToolSearch] = useState("");
  const debouncedToolSearch = useDebouncedValue(toolSearch, 300);
  const [page, setPage] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const serviceNames = services?.map((s) => s.name) ?? [];

  const {
    data: auditData,
    isLoading,
    isError,
    error,
  } = useAuditLog({
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
    serviceName: filterService !== "all" ? filterService : undefined,
    toolName: debouncedToolSearch || undefined,
    status: filterStatus !== "all" ? filterStatus : undefined,
  });

  const entries = auditData?.items ?? [];
  const total = auditData?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  // Stats computed from the current page (best we can do without a separate stats endpoint)
  const successes = entries.filter((a) => a.status === "success").length;
  const errors_ = entries.filter((a) => a.status === "error").length;
  const avgMs =
    entries.length > 0
      ? Math.round(
          entries.reduce((s, a) => s + a.duration_ms, 0) / entries.length,
        )
      : 0;

  const chartData = (() => {
    if (entries.length === 0) return [];
    const buckets: Record<string, { hour: string; calls: number }> = {};
    entries.forEach((a) => {
      if (!a.created_at) return;
      const d = new Date(a.created_at);
      const key = `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:00`;
      if (!buckets[key]) buckets[key] = { hour: key, calls: 0 };
      buckets[key].calls++;
    });
    return Object.values(buckets).slice(-24);
  })();

  function getServiceType(name: string): ServiceType | null {
    const svc = services?.find((s) => s.name === name);
    return svc?.service_type ?? null;
  }

  function getServiceId(name: string): string | undefined {
    return services?.find((s) => s.name === name)?.id;
  }

  function updateFilter(updater: () => void) {
    updater();
    setPage(0);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-header">{t("title")}</h1>
        <p className="page-description">{t("description")}</p>
      </div>

      <div className="card !p-0 flex flex-col sm:flex-row sm:divide-x divide-y sm:divide-y-0 divide-line overflow-hidden">
        <div className="flex-1 flex items-center gap-2.5 px-5 py-3.5">
          <Activity size={15} className="shrink-0" style={{ color: "var(--terra)" }} />
          <span className="text-base font-bold text-ink">{total}</span>
          <span className="text-xs text-ink-tertiary">{t("stats.totalCalls")}</span>
        </div>
        {totalPages <= 1 && (
          <>
            <div className="flex-1 flex items-center gap-2.5 px-5 py-3.5">
              <CheckCircle2 size={15} className="shrink-0" style={{ color: "var(--sage)" }} />
              <span className="text-base font-bold text-ink">
                {total > 0
                  ? `${Math.round((successes / Math.max(entries.length, 1)) * 100)}%`
                  : "\u2014"}
              </span>
              <span className="text-xs text-ink-tertiary">{t("stats.successRate")}</span>
            </div>
            <div className="flex-1 flex items-center gap-2.5 px-5 py-3.5">
              <AlertCircle size={15} className="shrink-0" style={{ color: "var(--rust)" }} />
              <span className="text-base font-bold text-ink">{errors_}</span>
              <span className="text-xs text-ink-tertiary">{t("stats.errors")}</span>
            </div>
            <div className="flex-1 flex items-center gap-2.5 px-5 py-3.5">
              <Timer size={15} className="shrink-0" style={{ color: "var(--info)" }} />
              <span className="text-base font-bold text-ink">{avgMs}ms</span>
              <span className="text-xs text-ink-tertiary">{t("stats.avgLatency")}</span>
            </div>
          </>
        )}
      </div>

      {chartData.length > 0 && (
        <Card>
          <h2 className="section-label mb-4">{t("chart.callsOverTime")}</h2>
          <MiniAreaChart
            data={chartData.map((d) => ({ label: d.hour, value: d.calls }))}
          />
        </Card>
      )}

      <div className="flex items-center gap-3 flex-wrap">
        <div className="w-full sm:w-56">
          <Input
            placeholder={t("filters.searchPlaceholder")}
            value={toolSearch}
            onChange={(e) => updateFilter(() => setToolSearch(e.target.value))}
          />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => updateFilter(() => setFilterService("all"))}
            className={`chip ${filterService === "all" ? "chip-active" : "chip-inactive"}`}
          >
            {t("filters.allServices")}
          </button>
          {serviceNames.map((name) => (
            <button
              key={name}
              onClick={() => updateFilter(() => setFilterService(name))}
              className={`chip ${filterService === name ? "chip-active" : "chip-inactive"}`}
            >
              {name}
            </button>
          ))}
        </div>
        <div className="w-px h-4 bg-line" />
        <div className="flex items-center gap-1.5">
          {["all", "success", "error"].map((status) => (
            <button
              key={status}
              onClick={() => updateFilter(() => setFilterStatus(status))}
              className={`chip ${filterStatus === status ? "chip-active" : "chip-inactive"}`}
            >
              {status === "all"
                ? t("filters.status.all")
                : status === "success"
                  ? t("filters.status.success")
                  : t("filters.status.error")}
            </button>
          ))}
        </div>
      </div>

      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error instanceof Error ? error : null}
        loadingMessage={t("query.loading")}
        skeleton={<LogsSkeleton />}
      >
        {entries.length > 0 ? (
          <>
            <Card className="!p-0 overflow-hidden">
              <div className="overflow-x-auto">
                <div className="flex items-center py-2.5 px-5 bg-canvas-secondary text-xs font-semibold uppercase tracking-wider text-ink-tertiary border-b border-line min-w-[640px]">
                  <span className="w-18">{t("table.headers.status")}</span>
                  <span className="flex-1">{t("table.headers.tool")}</span>
                  <span className="w-28">{t("table.headers.service")}</span>
                  <span className="w-20">{t("table.headers.client")}</span>
                  <span className="w-16 text-right">{t("table.headers.latency")}</span>
                  <span className="w-20 text-right">{t("table.headers.time")}</span>
                  <span className="w-6" />
                </div>
                <div className="divide-y divide-line">
                  {entries.map((entry) => {
                    const svcType = getServiceType(entry.service_name);
                    const svcId = getServiceId(entry.service_name);
                    const isExpanded = expandedId === entry.id;

                    return (
                      <div key={entry.id}>
                        <button
                          type="button"
                          onClick={() =>
                            setExpandedId(isExpanded ? null : entry.id)
                          }
                          className="flex items-center w-full min-w-[640px] text-left py-3 px-5 hover:bg-surface-hover transition-colors cursor-pointer"
                        >
                          <span className="w-18">
                            <Badge
                              variant={
                                entry.status === "success"
                                  ? "positive"
                                  : "critical"
                              }
                            >
                              {entry.status}
                            </Badge>
                          </span>
                          <code className="flex-1 text-xs font-mono text-ink truncate">
                            {entry.tool_name}
                          </code>
                          <span className="w-28 flex items-center gap-1.5 text-xs text-ink-tertiary truncate">
                            {svcType && (
                              <ServiceIcon type={svcType} size={12} />
                            )}
                            {svcId ? (
                              <Link
                                to="/services/$id"
                                params={{ id: svcId }}
                                className="hover:text-terra transition-colors"
                                onClick={(e) => e.stopPropagation()}
                              >
                                {entry.service_name}
                              </Link>
                            ) : (
                              entry.service_name
                            )}
                          </span>
                          <span className="w-20">
                            {entry.client_name && (
                              <Badge>{entry.client_name}</Badge>
                            )}
                          </span>
                          <span className="w-16 text-right text-xs font-mono text-ink-secondary">
                            {entry.duration_ms}ms
                          </span>
                          <span className="w-20 text-right">
                            {entry.created_at && (
                              <span className="text-xs text-ink-tertiary">
                                {formatRelativeTime(new Date(entry.created_at))}
                              </span>
                            )}
                          </span>
                          <span className="w-6 flex justify-end">
                            <ChevronDown
                              size={14}
                              className={[
                                "text-ink-tertiary transition-transform duration-200",
                                isExpanded ? "rotate-180" : "",
                              ].join(" ")}
                            />
                          </span>
                        </button>

                        {isExpanded && (
                          <LogEntryDetail entry={entry} serviceId={svcId} />
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </Card>

            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-tertiary">
                  {t("pagination.totalEntries", { count: total })}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className="p-2 rounded-lg text-ink-tertiary hover:text-ink hover:bg-surface-hover transition-all disabled:opacity-30 disabled:pointer-events-none"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span className="text-sm text-ink-secondary tabular-nums">
                    {t("pagination.page", { current: page + 1, total: totalPages })}
                  </span>
                  <button
                    onClick={() =>
                      setPage((p) => Math.min(totalPages - 1, p + 1))
                    }
                    disabled={page >= totalPages - 1}
                    className="p-2 rounded-lg text-ink-tertiary hover:text-ink hover:bg-surface-hover transition-all disabled:opacity-30 disabled:pointer-events-none"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <EmptyState
            icon={ScrollText}
            title={
              debouncedToolSearch ||
              filterService !== "all" ||
              filterStatus !== "all"
                ? t("empty.filteredTitle")
                : t("empty.defaultTitle")
            }
            description={
              debouncedToolSearch ||
              filterService !== "all" ||
              filterStatus !== "all"
                ? t("empty.filteredDescription")
                : t("empty.defaultDescription")
            }
          />
        )}
      </QueryState>
    </div>
  );
}
