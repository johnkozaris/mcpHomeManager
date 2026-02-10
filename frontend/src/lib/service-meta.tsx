import {
  GitBranch,
  Home,
  FileText,
  Camera,
  Cloud,
  CloudCog,
  Activity,
  Shield,
  Network,
  Container,
  Rss,
  Bookmark,
  FileScan,
  BookOpen,
  Library,
  Globe,
  Waypoints,
  Puzzle,
  type LucideIcon,
} from "lucide-react";
import type { BuiltinServiceType, ServiceType } from "./types";

interface ServiceMeta {
  icon: LucideIcon;
  label: string;
  description: string;
  color: string;
}

export const SERVICE_META: Record<BuiltinServiceType, ServiceMeta> = {
  forgejo: {
    icon: GitBranch,
    label: "Forgejo",
    description: "Git hosting & CI/CD",
    color: "var(--brand-forgejo)",
  },
  homeassistant: {
    icon: Home,
    label: "Home Assistant",
    description: "Smart home automation",
    color: "var(--brand-homeassistant)",
  },
  paperless: {
    icon: FileText,
    label: "Paperless-ngx",
    description: "Document management",
    color: "var(--brand-paperless)",
  },
  immich: {
    icon: Camera,
    label: "Immich",
    description: "Photo & video management",
    color: "var(--brand-immich)",
  },
  nextcloud: {
    icon: Cloud,
    label: "Nextcloud",
    description: "Cloud storage & sync",
    color: "var(--brand-nextcloud)",
  },
  uptimekuma: {
    icon: Activity,
    label: "Uptime Kuma",
    description: "Uptime monitoring",
    color: "var(--brand-uptimekuma)",
  },
  adguard: {
    icon: Shield,
    label: "AdGuard Home",
    description: "DNS filtering & ad blocking",
    color: "var(--brand-adguard)",
  },
  nginxproxymanager: {
    icon: Network,
    label: "Nginx Proxy Manager",
    description: "Reverse proxy & SSL",
    color: "var(--brand-nginxproxymanager)",
  },
  portainer: {
    icon: Container,
    label: "Portainer",
    description: "Container management",
    color: "var(--brand-portainer)",
  },
  freshrss: {
    icon: Rss,
    label: "FreshRSS",
    description: "RSS feed reader",
    color: "var(--brand-freshrss)",
  },
  wallabag: {
    icon: Bookmark,
    label: "Wallabag",
    description: "Read-it-later articles",
    color: "var(--brand-wallabag)",
  },
  stirlingpdf: {
    icon: FileScan,
    label: "Stirling PDF",
    description: "PDF processing tools",
    color: "var(--brand-stirlingpdf)",
  },
  wikijs: {
    icon: BookOpen,
    label: "Wiki.js",
    description: "Team knowledge base",
    color: "var(--brand-wikijs)",
  },
  calibreweb: {
    icon: Library,
    label: "Calibre-Web",
    description: "E-book library management",
    color: "var(--brand-calibreweb)",
  },
  cloudflare: {
    icon: CloudCog,
    label: "Cloudflare",
    description: "DNS, tunnels, and zero trust management",
    color: "var(--brand-cloudflare)",
  },
  tailscale: {
    icon: Waypoints,
    label: "Tailscale",
    description: "VPN mesh network and device management",
    color: "var(--brand-tailscale)",
  },
  generic_rest: {
    icon: Globe,
    label: "Generic REST",
    description: "Custom REST API service",
    color: "var(--brand-generic-rest)",
  },
};

const _fallbackMeta: ServiceMeta = {
  icon: Puzzle,
  label: "Unknown",
  description: "Unknown service type",
  color: "var(--ink-tertiary)",
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
  size?: number;
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
