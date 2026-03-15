import { FileScan, Globe, Puzzle } from "lucide-react";
import {
  ForgejoLogo,
  HomeAssistantLogo,
  PaperlessLogo,
  ImmichLogo,
  NextcloudLogo,
  UptimeKumaLogo,
  AdGuardLogo,
  NginxProxyManagerLogo,
  PortainerLogo,
  FreshRSSLogo,
  WallabagLogo,
  WikiJsLogo,
  CalibreWebLogo,
  CloudflareLogo,
  TailscaleLogo,
} from "@/components/icons/ServiceLogos";
import { translateText } from "@/i18n/translate";
import type { BuiltinServiceType, ServiceType } from "./types";

type ServiceIconComponent = React.ComponentType<{
  size?: number | string;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
}>;

interface ServiceMeta {
  icon: ServiceIconComponent;
  label: string;
  description: string;
  color: string;
}

function createServiceMeta(
  type: BuiltinServiceType,
  icon: ServiceIconComponent,
  color: string,
  fallbackLabel: string,
  fallbackDescription: string,
): ServiceMeta {
  return {
    icon,
    color,
    get label() {
      return translateText(`serviceMeta:services.${type}.label`, fallbackLabel);
    },
    get description() {
      return translateText(
        `serviceMeta:services.${type}.description`,
        fallbackDescription,
      );
    },
  };
}

export const SERVICE_META: Record<BuiltinServiceType, ServiceMeta> = {
  forgejo: createServiceMeta(
    "forgejo",
    ForgejoLogo,
    "var(--brand-forgejo)",
    "Forgejo",
    "Git hosting & CI/CD",
  ),
  homeassistant: createServiceMeta(
    "homeassistant",
    HomeAssistantLogo,
    "var(--brand-homeassistant)",
    "Home Assistant",
    "Smart home automation",
  ),
  paperless: createServiceMeta(
    "paperless",
    PaperlessLogo,
    "var(--brand-paperless)",
    "Paperless-ngx",
    "Document management",
  ),
  immich: createServiceMeta(
    "immich",
    ImmichLogo,
    "var(--brand-immich)",
    "Immich",
    "Photo & video management",
  ),
  nextcloud: createServiceMeta(
    "nextcloud",
    NextcloudLogo,
    "var(--brand-nextcloud)",
    "Nextcloud",
    "Cloud storage & sync",
  ),
  uptimekuma: createServiceMeta(
    "uptimekuma",
    UptimeKumaLogo,
    "var(--brand-uptimekuma)",
    "Uptime Kuma",
    "Uptime monitoring",
  ),
  adguard: createServiceMeta(
    "adguard",
    AdGuardLogo,
    "var(--brand-adguard)",
    "AdGuard Home",
    "DNS filtering & ad blocking",
  ),
  nginxproxymanager: createServiceMeta(
    "nginxproxymanager",
    NginxProxyManagerLogo,
    "var(--brand-nginxproxymanager)",
    "Nginx Proxy Manager",
    "Reverse proxy & SSL",
  ),
  portainer: createServiceMeta(
    "portainer",
    PortainerLogo,
    "var(--brand-portainer)",
    "Portainer",
    "Container management",
  ),
  freshrss: createServiceMeta(
    "freshrss",
    FreshRSSLogo,
    "var(--brand-freshrss)",
    "FreshRSS",
    "RSS feed reader",
  ),
  wallabag: createServiceMeta(
    "wallabag",
    WallabagLogo,
    "var(--brand-wallabag)",
    "Wallabag",
    "Read-it-later articles",
  ),
  stirlingpdf: createServiceMeta(
    "stirlingpdf",
    FileScan,
    "var(--brand-stirlingpdf)",
    "Stirling PDF",
    "PDF processing tools",
  ),
  wikijs: createServiceMeta(
    "wikijs",
    WikiJsLogo,
    "var(--brand-wikijs)",
    "Wiki.js",
    "Team knowledge base",
  ),
  calibreweb: createServiceMeta(
    "calibreweb",
    CalibreWebLogo,
    "var(--brand-calibreweb)",
    "Calibre-Web",
    "E-book library management",
  ),
  cloudflare: createServiceMeta(
    "cloudflare",
    CloudflareLogo,
    "var(--brand-cloudflare)",
    "Cloudflare",
    "DNS, tunnels, and zero trust management",
  ),
  tailscale: createServiceMeta(
    "tailscale",
    TailscaleLogo,
    "var(--brand-tailscale)",
    "Tailscale",
    "VPN mesh network and device management",
  ),
  generic_rest: createServiceMeta(
    "generic_rest",
    Globe,
    "var(--brand-generic-rest)",
    "Custom API",
    "Connect any REST API",
  ),
};

const _fallbackMeta: ServiceMeta = {
  icon: Puzzle,
  color: "var(--ink-tertiary)",
  get label() {
    return translateText("serviceMeta:fallback.label", "Unknown");
  },
  get description() {
    return translateText(
      "serviceMeta:fallback.description",
      "Unknown service type",
    );
  },
};

export function getServiceMeta(type: ServiceType): ServiceMeta {
  return (SERVICE_META as Record<string, ServiceMeta>)[type] ?? _fallbackMeta;
}

export function ServiceIcon({
  type,
  size = 18,
  className,
}: {
  type: ServiceType;
  size?: number | string;
  className?: string;
}) {
  const meta = getServiceMeta(type);
  const Icon = meta.icon;
  return <Icon size={size} color={meta.color} className={className} />;
}

export function ServiceIconBadge({
  type,
  size = "md",
}: {
  type: ServiceType;
  size?: "sm" | "md" | "lg";
}) {
  const meta = getServiceMeta(type);
  const Icon = meta.icon;
  const sizeMap = {
    sm: { box: "w-7 h-7", icon: 14 },
    md: { box: "w-9 h-9", icon: 18 },
    lg: { box: "w-11 h-11", icon: 22 },
  };
  const s = sizeMap[size];

  return (
    <div
      className={`${s.box} rounded-xl flex items-center justify-center shrink-0`}
      style={{
        backgroundColor: `color-mix(in srgb, ${meta.color} 8%, transparent)`,
      }}
    >
      <Icon size={s.icon} color={meta.color} />
    </div>
  );
}
