import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  Server,
  Wrench,
  Activity,
  ArrowRight,
  Plus,
  Zap,
  X,
} from "lucide-react";
import {
  useServices,
  useTools,
  useHealth,
  useAuditLog,
} from "@/hooks/useServices";
import { QueryState } from "@/components/ui/QueryState";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { McpEndpointBar } from "@/components/ui/McpEndpointBar";
import { ServiceIconBadge, getServiceMeta } from "@/lib/service-meta";
import type { ServiceType } from "@/lib/types";
import { StatusDot } from "@/components/ui/StatusDot";
import { isDismissed, dismiss } from "@/lib/utils";
import type { ServiceConnection } from "@/lib/types";
import { Skeleton } from "@/components/ui/Skeleton";
import { useTranslation } from "react-i18next";

/* ─── Hero — compact ───────────────────────────────────────── */
function HeroBanner({ onDismiss }: { onDismiss: () => void }) {
  const { t } = useTranslation("dashboard", { keyPrefix: "heroBanner" });

  return (
    <div className="hero-banner relative overflow-hidden rounded-2xl">
      <button
        onClick={onDismiss}
        className="absolute top-1.5 right-1.5 z-10 w-9 h-9 rounded-lg bg-white/15 flex items-center justify-center text-white/70 hover:text-white hover:bg-white/25 transition-all"
        aria-label={t("dismiss")}
      >
        <X size={14} />
      </button>

      <div className="px-7 py-6">
        <h1 className="text-xl font-bold text-white tracking-tight">
          {t("title")}
        </h1>
        <p className="text-sm text-white/60 mt-1.5">{t("description")}</p>
        <div className="flex items-center gap-3 mt-4">
          <Link to="/services">
            <Button variant="inverse" size="sm" className="!rounded-xl">
              <Plus size={14} /> {t("actions.connectService")}
            </Button>
          </Link>
          <Link to="/agents">
            <Button
              variant="ghost"
              size="sm"
              className="!text-white/70 hover:!text-white hover:!bg-white/10 !rounded-xl"
            >
              {t("actions.setupGuide")}
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

/* ─── Inline stat bar ─────────────────────────────────────── */
function StatBar({
  services,
  toolCount,
  auditCount,
}: {
  services: ServiceConnection[];
  toolCount: number;
  auditCount: number;
}) {
  const { t } = useTranslation("dashboard", { keyPrefix: "stats" });
  const healthy = services.filter((s) => s.health_status === "healthy").length;
  const enabled = services.filter((s) => s.is_enabled).length;

  const stats = [
    {
      id: "services",
      icon: Server,
      color: "var(--terra)",
      value: `${services.length}`,
      label: t("services.sub", { count: enabled }),
    },
    {
      id: "tools",
      icon: Wrench,
      color: "var(--sage)",
      value: `${toolCount}`,
      label: t("tools.sub"),
    },
    {
      id: "health",
      icon: Activity,
      color: healthy === services.length ? "var(--sage)" : "var(--clay)",
      value:
        healthy === services.length
          ? t("health.ok")
          : `${healthy}/${services.length}`,
      label:
        healthy === services.length
          ? t("health.allConnected")
          : t("health.needsAttention"),
    },
    {
      id: "apiCalls",
      icon: Zap,
      color: "var(--info)",
      value: `${auditCount}`,
      label: t("apiCalls.sub"),
    },
  ];

  return (
    <div className="card !p-0 flex flex-col sm:flex-row sm:divide-x divide-y sm:divide-y-0 divide-line overflow-hidden">
      {stats.map((s) => (
        <div key={s.id} className="flex-1 flex items-center gap-2.5 px-5 py-3.5">
          <s.icon size={15} style={{ color: s.color }} className="shrink-0" />
          <span className="text-base font-bold text-ink">{s.value}</span>
          <span className="text-xs text-ink-tertiary truncate">{s.label}</span>
        </div>
      ))}
    </div>
  );
}

/* ─── Service row ─────────────────────────────────────────── */
function ServiceRow({ service }: { service: ServiceConnection }) {
  const { t } = useTranslation("dashboard", { keyPrefix: "serviceRow" });
  const meta = getServiceMeta(service.service_type);
  const isUnhealthy = service.health_status === "unhealthy";
  return (
    <Link
      to="/services/$id"
      params={{ id: service.id }}
      className={[
        "card card-interactive flex items-center justify-between p-4 group transition-all duration-200",
        isUnhealthy && "border-l-[3px] border-l-rust",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="flex items-center gap-3">
        <ServiceIconBadge type={service.service_type} size="sm" />
        <div>
          <p className="text-sm font-semibold text-ink group-hover:text-terra transition-colors">
            {service.display_name}
          </p>
          <p className="text-xs text-ink-tertiary">{meta.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <Badge variant="brand">{t("toolsCount", { count: service.tool_count })}</Badge>
        <StatusDot status={service.health_status} />
        <ArrowRight
          size={15}
          className="text-ink-faint group-hover:text-terra transition-colors"
        />
      </div>
    </Link>
  );
}

/* ─── Service grid (welcome state) ─────────────────────────── */
const GRID_SERVICES: ServiceType[] = [
  "forgejo",
  "homeassistant",
  "paperless",
  "immich",
  "nextcloud",
  "uptimekuma",
  "adguard",
];

function ServiceGrid() {
  const { t } = useTranslation("dashboard", { keyPrefix: "serviceGrid" });
  const navigate = useNavigate();
  return (
    <div className="flex flex-wrap gap-2">
      {GRID_SERVICES.map((type) => {
        const meta = getServiceMeta(type);
        return (
          <button
            key={type}
            onClick={() => navigate({ to: "/services" })}
            className="group flex items-center gap-2.5 px-3 py-2 rounded-xl bg-surface shadow-card hover:shadow-elevated transition-all cursor-pointer"
          >
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
              style={{ backgroundColor: `color-mix(in srgb, ${meta.color} 12%, transparent)` }}
            >
              <meta.icon size={14} style={{ color: meta.color }} />
            </div>
            <div className="text-left">
              <p className="text-sm font-semibold text-ink group-hover:text-terra transition-colors leading-tight">
                {meta.label}
              </p>
            </div>
          </button>
        );
      })}
      <button
        onClick={() => navigate({ to: "/services" })}
        className="flex items-center gap-2 px-3 py-2 rounded-xl border-2 border-dashed border-line-strong hover:border-terra transition-all cursor-pointer"
      >
        <Plus size={14} className="text-ink-tertiary" />
        <span className="text-xs font-semibold text-ink-tertiary">
          {t("more")}
        </span>
      </button>
    </div>
  );
}

/* ─── How it works ─────────────────────────────────────────── */
function HowItWorks({ onDismiss }: { onDismiss: () => void }) {
  const { t } = useTranslation("dashboard", { keyPrefix: "howItWorks" });

  return (
    <div className="relative card !p-5">
      <button
        onClick={onDismiss}
        className="absolute top-1.5 right-1.5 w-9 h-9 rounded-lg bg-canvas-tertiary flex items-center justify-center text-ink-tertiary hover:text-ink hover:bg-canvas-hover transition-all"
        aria-label={t("dismiss")}
      >
        <X size={14} />
      </button>
      <p className="text-xs font-bold uppercase tracking-wider text-ink-tertiary mb-3">
        {t("title")}
      </p>
      <ol className="space-y-2.5 text-sm text-ink-secondary">
        <li className="flex gap-2">
          <span className="text-xs font-bold text-ink-tertiary mt-0.5 shrink-0">1.</span>
          <span>
            <strong className="text-ink">{t("steps.connect.title")}</strong>
            {" \u2014 "}{t("steps.connect.description")}
          </span>
        </li>
        <li className="flex gap-2">
          <span className="text-xs font-bold text-ink-tertiary mt-0.5 shrink-0">2.</span>
          <span>
            <strong className="text-ink">{t("steps.configure.title")}</strong>
            {" \u2014 "}{t("steps.configure.description")}
          </span>
        </li>
        <li className="flex gap-2">
          <span className="text-xs font-bold text-ink-tertiary mt-0.5 shrink-0">3.</span>
          <span>
            <strong className="text-ink">{t("steps.use.title")}</strong>
            {" \u2014 "}{t("steps.use.description")}
          </span>
        </li>
      </ol>
    </div>
  );
}

/* ─── Welcome view ─────────────────────────────────────────── */
function WelcomeView() {
  const { t } = useTranslation("dashboard", { keyPrefix: "welcomeView" });
  const [heroHidden, setHeroHidden] = useState(isDismissed("hero"));
  const [howHidden, setHowHidden] = useState(isDismissed("howitworks"));

  return (
    <div className="space-y-5">
      <McpEndpointBar />

      {(!heroHidden || !howHidden) && (
        <div
          className={`grid gap-5 ${!heroHidden && !howHidden ? "grid-cols-1 lg:grid-cols-12" : ""}`}
        >
          {!heroHidden && (
            <div className={howHidden ? "" : "lg:col-span-8"}>
              <HeroBanner
                onDismiss={() => {
                  dismiss("hero");
                  setHeroHidden(true);
                }}
              />
            </div>
          )}
          {!howHidden && (
            <div className={heroHidden ? "" : "lg:col-span-4"}>
              <HowItWorks
                onDismiss={() => {
                  dismiss("howitworks");
                  setHowHidden(true);
                }}
              />
            </div>
          )}
        </div>
      )}

      <div>
        <h2 className="section-label mb-3">{t("supportedServices")}</h2>
        <ServiceGrid />
      </div>
    </div>
  );
}

/* ─── Dashboard view ──────────────────────────────────────── */
function DashboardView({
  services,
  toolCount,
  audit,
}: {
  services: ServiceConnection[];
  toolCount: number;
  audit:
    | {
        id: string;
        tool_name: string;
        service_name: string;
        status: string;
        duration_ms: number;
        created_at: string | null;
      }[]
    | undefined;
}) {
  const { t } = useTranslation("dashboard", { keyPrefix: "dashboardView" });
  const [heroHidden, setHeroHidden] = useState(isDismissed("hero"));
  const hasActivity = audit && audit.length > 0;

  return (
    <div className="space-y-5">
      <McpEndpointBar />

      {!heroHidden && (
        <HeroBanner
          onDismiss={() => {
            dismiss("hero");
            setHeroHidden(true);
          }}
        />
      )}

      <StatBar
        services={services}
        toolCount={toolCount}
        auditCount={audit?.length ?? 0}
      />

      {hasActivity ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-8">
            <h2 className="section-label mb-3">{t("yourServices")}</h2>
            <div className="space-y-2.5">
              {services.map((svc) => (
                <ServiceRow key={svc.id} service={svc} />
              ))}
            </div>
            <Link
              to="/services"
              className="flex items-center gap-1.5 text-sm font-semibold text-terra hover:text-terra-light transition-colors mt-3"
            >
              {t("manageAll")} <ArrowRight size={14} />
            </Link>
          </div>

          <div className="lg:col-span-4">
            <div className="flex items-center justify-between mb-2.5">
              <h3 className="section-label">{t("recentActivity.title")}</h3>
              <Link
                to="/logs"
                className="text-xs text-terra hover:text-terra-light transition-colors"
              >
                {t("recentActivity.viewAll")}
              </Link>
            </div>
            <div className="card !p-3.5 space-y-2">
              {audit.slice(0, 6).map((entry) => (
                <div
                  key={entry.id}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Badge
                      variant={
                        entry.status === "success" ? "positive" : "critical"
                      }
                    >
                      {entry.status === "success"
                        ? t("recentActivity.statusOk")
                        : t("recentActivity.statusError")}
                    </Badge>
                    <span className="text-xs text-ink font-mono truncate">
                      {entry.tool_name}
                    </span>
                  </div>
                  <span className="text-xs text-ink-tertiary font-mono shrink-0">
                    {entry.duration_ms}ms
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div>
          <h2 className="section-label mb-3">{t("yourServices")}</h2>
          <div className="space-y-2.5">
            {services.map((svc) => (
              <ServiceRow key={svc.id} service={svc} />
            ))}
          </div>
          <Link
            to="/services"
            className="flex items-center gap-1.5 text-sm font-semibold text-terra hover:text-terra-light transition-colors mt-3"
          >
            {t("manageAll")} <ArrowRight size={14} />
          </Link>
        </div>
      )}
    </div>
  );
}

/* ─── Skeleton ────────────────────────────────────────────── */
function DashboardSkeleton() {
  return (
    <div className="space-y-5">
      <Skeleton className="h-10 w-full max-w-md" />
      <Skeleton className="h-[52px]" />
      <div className="space-y-2.5">
        {Array.from({ length: 3 }, (_, i) => (
          <Skeleton key={i} className="h-[68px]" />
        ))}
      </div>
    </div>
  );
}

/* ─── Main ────────────────────────────────────────────────── */
export function Dashboard() {
  const { t } = useTranslation("dashboard", { keyPrefix: "query" });
  const { data: services, isLoading, isError, error } = useServices();
  const { data: tools } = useTools();
  useHealth();
  const { data: auditData } = useAuditLog();

  return (
    <QueryState
      isLoading={isLoading}
      isError={isError}
      error={error instanceof Error ? error : null}
      loadingMessage={t("loading")}
      errorMessage={t("error")}
      skeleton={<DashboardSkeleton />}
    >
      {services && services.length > 0 ? (
        <DashboardView
          services={services}
          toolCount={tools?.length ?? 0}
          audit={auditData?.items}
        />
      ) : (
        <WelcomeView />
      )}
    </QueryState>
  );
}
