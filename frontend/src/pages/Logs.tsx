import { useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
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
import { StatCard } from "@/components/ui/StatCard";
import { QueryState } from "@/components/ui/QueryState";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { ServiceIcon } from "@/lib/service-meta";
import { LogEntryDetail } from "@/components/logs/LogEntryDetail";
import { formatRelativeTime } from "@/lib/utils";
import type { ServiceType } from "@/lib/types";

const PAGE_SIZE = 50;

export function Logs() {
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
        <h1 className="page-header">Logs</h1>
        <p className="page-description">
          What AI agents have been doing with your services
        </p>
      </div>

      <div
        className={`grid gap-4 ${totalPages <= 1 ? "grid-cols-4" : "grid-cols-1"}`}
      >
        <StatCard
          label="Total Calls"
          value={total}
          icon={Activity}
          iconColor="var(--terra)"
          iconBg="var(--terra-bg)"
        />
        {totalPages <= 1 && (
          <>
            <StatCard
              label="Success Rate"
              value={
                total > 0
                  ? `${Math.round((successes / Math.max(entries.length, 1)) * 100)}%`
                  : "\u2014"
              }
              icon={CheckCircle2}
              iconColor="var(--sage)"
              iconBg="var(--sage-bg)"
            />
            <StatCard
              label="Errors"
              value={errors_}
              icon={AlertCircle}
              iconColor="var(--rust)"
              iconBg="var(--rust-bg)"
            />
            <StatCard
              label="Avg Latency"
              value={`${avgMs}ms`}
              icon={Timer}
              iconColor="var(--info)"
              iconBg="var(--info-bg)"
            />
          </>
        )}
      </div>

      {chartData.length > 0 && (
        <Card>
          <h2 className="section-label mb-4">Calls over time</h2>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient
                    id="callsGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="5%"
                      stopColor="var(--terra)"
                      stopOpacity={0.2}
                    />
                    <stop
                      offset="95%"
                      stopColor="var(--terra)"
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="hour"
                  tick={{ fontSize: 10, fill: "var(--ink-tertiary)" }}
                  axisLine={{ stroke: "var(--line)" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: "var(--ink-tertiary)" }}
                  axisLine={false}
                  tickLine={false}
                  width={30}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--surface)",
                    border: "1px solid var(--line)",
                    borderRadius: "12px",
                    fontSize: "12px",
                    color: "var(--ink)",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="calls"
                  stroke="var(--terra)"
                  strokeWidth={2}
                  fill="url(#callsGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      <div className="flex items-center gap-3 flex-wrap">
        <div className="w-full sm:w-56">
          <Input
            placeholder="Search tools…"
            value={toolSearch}
            onChange={(e) => updateFilter(() => setToolSearch(e.target.value))}
          />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => updateFilter(() => setFilterService("all"))}
            className={`chip ${filterService === "all" ? "chip-active" : "chip-inactive"}`}
          >
            All services
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
              {status === "all" ? "All status" : status}
            </button>
          ))}
        </div>
      </div>

      <QueryState
        isLoading={isLoading}
        isError={isError}
        error={error instanceof Error ? error : null}
        loadingMessage="Loading logs…"
      >
        {entries.length > 0 ? (
          <>
            <Card className="!p-0 overflow-hidden">
              <div className="overflow-x-auto">
                {/* Table header */}
                <div className="flex items-center py-2.5 px-5 bg-canvas-secondary text-2xs font-semibold uppercase tracking-wider text-ink-tertiary border-b border-line min-w-[640px]">
                  <span className="w-18">Status</span>
                  <span className="flex-1">Tool</span>
                  <span className="w-28">Service</span>
                  <span className="w-20">Client</span>
                  <span className="w-16 text-right">Latency</span>
                  <span className="w-20 text-right">Time</span>
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
                          <span className="w-28 flex items-center gap-1.5 text-2xs text-ink-tertiary truncate">
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
                              <span className="text-2xs text-ink-tertiary">
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

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-tertiary">
                  {total} total entries
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className="p-1.5 rounded-lg text-ink-tertiary hover:text-ink hover:bg-surface-hover transition-all disabled:opacity-30 disabled:pointer-events-none"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span className="text-sm text-ink-secondary tabular-nums">
                    Page {page + 1} of {totalPages}
                  </span>
                  <button
                    onClick={() =>
                      setPage((p) => Math.min(totalPages - 1, p + 1))
                    }
                    disabled={page >= totalPages - 1}
                    className="p-1.5 rounded-lg text-ink-tertiary hover:text-ink hover:bg-surface-hover transition-all disabled:opacity-30 disabled:pointer-events-none"
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
                ? "No matching entries"
                : "No log entries yet"
            }
            description={
              debouncedToolSearch ||
              filterService !== "all" ||
              filterStatus !== "all"
                ? "Try adjusting the filters."
                : "Activity will show up here once AI agents start calling tools through MCP."
            }
          />
        )}
      </QueryState>
    </div>
  );
}
