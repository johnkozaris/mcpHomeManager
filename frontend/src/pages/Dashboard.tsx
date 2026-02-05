import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import {
  Server,
  Wrench,
  Activity,
  ArrowRight,
  Plus,
  Bot,
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

/* ─── Hero — compact ───────────────────────────────────────── */
function HeroBanner({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="hero-banner relative overflow-hidden rounded-2xl">
      <div className="absolute inset-0 pointer-events-none" aria-hidden>
        <svg
          className="absolute -top-16 -right-16 w-56 h-56"
          viewBox="0 0 224 224"
        >
          <circle cx="224" cy="0" r="160" fill="white" fillOpacity="0.07" />
        </svg>
      </div>

      <button
        onClick={onDismiss}
        className="absolute top-3 right-3 z-20 w-7 h-7 rounded-lg bg-black/20 backdrop-blur-sm flex items-center justify-center text-white/70 hover:text-white hover:bg-black/30 transition-all"
      >
        <X size={14} />
      </button>

      <div className="relative z-10 px-7 py-6">
        <h1 className="text-xl font-bold text-white tracking-tight">
          Make your services accessible to AI
        </h1>
        <p className="text-sm text-white/60 mt-1.5">
          Turn self-hosted services into tools that AI agents can call
        </p>
        <div className="flex items-center gap-3 mt-4">
          <Link to="/services">
            <Button
              size="sm"
              className="!bg-white !text-[var(--terra-dark)] hover:!bg-white/90 !shadow-lg !font-bold !rounded-xl"
            >
              <Plus size={14} /> Connect a service
            </Button>
          </Link>
          <Link to="/agents">
            <Button
              variant="ghost"
              size="sm"
              className="!text-white/70 hover:!text-white hover:!bg-white/10 !rounded-xl"
            >
              Setup guide
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

/* ─── Compact stat row ─────────────────────────────────────── */
function StatRow({
  services,
  toolCount,
  auditCount,
}: {
  services: ServiceConnection[];
  toolCount: number;
  auditCount: number;
}) {
  const healthy = services.filter((s) => s.health_status === "healthy").length;
  const enabled = services.filter((s) => s.is_enabled).length;

  const stats = [
    {
      icon: Server,
      color: "var(--terra)",
      bg: "var(--terra-bg)",
      label: "Services",
      value: `${services.length}`,
      sub: `${enabled} active`,
    },
    {
      icon: Wrench,
      color: "var(--sage)",
      bg: "var(--sage-bg)",
      label: "Tools",
      value: `${toolCount}`,
      sub: "MCP tools",
    },
    {
      icon: Activity,
      color: healthy === services.length ? "var(--sage)" : "var(--clay)",
      bg: healthy === services.length ? "var(--sage-bg)" : "var(--clay-bg)",
      label: "Health",
      value:
        healthy === services.length ? "OK" : `${healthy}/${services.length}`,
      sub: healthy === services.length ? "all connected" : "need attention",
    },
    {
      icon: Zap,
      color: "var(--info)",
      bg: "var(--info-bg)",
      label: "API Calls",
      value: `${auditCount}`,
      sub: "total",
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-3">
      {stats.map((s) => (
        <div key={s.label} className="card !p-4 flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
            style={{ backgroundColor: s.bg }}
          >
            <s.icon size={16} style={{ color: s.color }} />
          </div>
          <div className="min-w-0">
            <p className="text-lg font-bold text-ink leading-tight">
              {s.value}
            </p>
            <p className="text-2xs text-ink-tertiary">{s.sub}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ─── Service row ─────────────────────────────────────────── */
function ServiceRow({ service }: { service: ServiceConnection }) {
  const meta = getServiceMeta(service.service_type);
  return (
    <Link
      to="/services/$id"
      params={{ id: service.id }}
      className="card flex items-center justify-between p-4 group transition-all duration-200"
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
        <Badge variant="brand">{service.tool_count} tools</Badge>
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
              style={{ backgroundColor: `${meta.color}20` }}
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
        <span className="text-xs font-semibold text-ink-tertiary">More</span>
      </button>
    </div>
  );
}

/* ─── How it works ─────────────────────────────────────────── */
function HowItWorks({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="relative card !p-5">
      <button
        onClick={onDismiss}
        className="absolute top-3 right-3 w-7 h-7 rounded-lg bg-canvas-tertiary flex items-center justify-center text-ink-tertiary hover:text-ink hover:bg-canvas-hover transition-all"
      >
        <X size={14} />
      </button>
      <p className="text-xs font-bold uppercase tracking-wider text-ink-tertiary mb-3">
        How it works
      </p>
      <div className="space-y-3">
        {[
          {
            icon: Server,
            color: "var(--terra)",
            bg: "var(--terra-bg)",
            title: "Connect",
            desc: "Add services with an API token",
          },
          {
            icon: Wrench,
            color: "var(--sage)",
            bg: "var(--sage-bg)",
            title: "Configure",
            desc: "Choose which tools agents can use",
          },
          {
            icon: Bot,
            color: "var(--coral)",
            bg: "var(--coral-bg)",
            title: "Use",
            desc: "Point any MCP client here",
          },
        ].map((step) => (
          <div key={step.title} className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
              style={{ backgroundColor: step.bg }}
            >
              <step.icon size={16} style={{ color: step.color }} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-ink">{step.title}</p>
              <p className="text-xs text-ink-secondary">{step.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Welcome view ─────────────────────────────────────────── */
function WelcomeView() {
  const [heroHidden, setHeroHidden] = useState(isDismissed("hero"));
  const [howHidden, setHowHidden] = useState(isDismissed("howitworks"));

  return (
    <div className="space-y-5">
      <McpEndpointBar />

      {(!heroHidden || !howHidden) && (
        <div
          className={`grid gap-5 ${!heroHidden && !howHidden ? "grid-cols-12" : ""}`}
        >
          {!heroHidden && (
            <div className={howHidden ? "" : "col-span-8"}>
              <HeroBanner
                onDismiss={() => {
                  dismiss("hero");
                  setHeroHidden(true);
                }}
              />
            </div>
          )}
          {!howHidden && (
            <div className={heroHidden ? "" : "col-span-4"}>
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
        <h2 className="section-label mb-3">Supported services</h2>
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
  const [heroHidden, setHeroHidden] = useState(isDismissed("hero"));

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

      <StatRow
        services={services}
        toolCount={toolCount}
        auditCount={audit?.length ?? 0}
      />

      <div className="grid grid-cols-12 gap-5">
        {/* Services list */}
        <div className="col-span-7">
          <h2 className="section-label mb-3">Your services</h2>
          <div className="space-y-2.5">
            {services.map((svc) => (
              <ServiceRow key={svc.id} service={svc} />
            ))}
          </div>
          <Link
            to="/services"
            className="flex items-center gap-1.5 text-sm font-semibold text-terra hover:text-terra-light transition-colors mt-3"
          >
            Manage all <ArrowRight size={14} />
          </Link>
        </div>

        {/* Right column */}
        <div className="col-span-5 space-y-5">
          {/* Activity */}
          {audit && audit.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <h3 className="section-label">Recent activity</h3>
                <Link
                  to="/logs"
                  className="text-xs text-terra hover:text-terra-light transition-colors"
                >
                  View all
                </Link>
              </div>
              <div className="card !p-3.5 space-y-2">
                {audit.slice(0, 5).map((entry) => (
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
                        {entry.status === "success" ? "ok" : "err"}
                      </Badge>
                      <span className="text-xs text-ink font-mono truncate">
                        {entry.tool_name}
                      </span>
                    </div>
                    <span className="text-2xs text-ink-tertiary font-mono shrink-0">
                      {entry.duration_ms}ms
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick actions */}
          <div>
            <h3 className="section-label mb-2.5">Quick actions</h3>
            <div className="space-y-2">
              {[
                {
                  to: "/agents",
                  icon: Bot,
                  color: "var(--terra)",
                  bg: "var(--terra-bg)",
                  label: "Setup AI Agents",
                  desc: "Connection guides",
                },
                {
                  to: "/services",
                  icon: Plus,
                  color: "var(--sage)",
                  bg: "var(--sage-bg)",
                  label: "Connect Service",
                  desc: "Add a new service",
                },
                {
                  to: "/tools",
                  icon: Wrench,
                  color: "var(--info)",
                  bg: "var(--info-bg)",
                  label: "Manage Tools",
                  desc: "Permissions & profiles",
                },
              ].map((a) => (
                <Link
                  key={a.to}
                  to={a.to}
                  className="card flex items-center gap-3 !p-3.5 group transition-all duration-200"
                >
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                    style={{ backgroundColor: a.bg }}
                  >
                    <a.icon size={16} style={{ color: a.color }} />
                  </div>
                  <div className="flex-1">
                    <span className="text-sm font-semibold text-ink group-hover:text-terra transition-colors">
                      {a.label}
                    </span>
                    <span className="block text-2xs text-ink-tertiary">
                      {a.desc}
                    </span>
                  </div>
                  <ArrowRight
                    size={14}
                    className="text-ink-faint opacity-0 group-hover:opacity-100 transition-opacity"
                  />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Main ────────────────────────────────────────────────── */
export function Dashboard() {
  const { data: services, isLoading, isError, error } = useServices();
  const { data: tools } = useTools();
  useHealth();
  const { data: auditData } = useAuditLog();

  return (
    <QueryState
      isLoading={isLoading}
      isError={isError}
      error={error instanceof Error ? error : null}
      loadingMessage="Connecting\u2026"
      errorMessage="Cannot reach the backend."
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
