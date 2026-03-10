import { type ReactNode, useEffect, useRef, useState } from "react";
import { useAppName } from "@/hooks/useAppName";
import { Link, useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import {
  Home,
  Server,
  Wrench,
  ScrollText,
  Settings,
  Sun,
  Moon,
  Bot,
  Users,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Globe,
  type LucideIcon,
} from "lucide-react";
import { useTheme } from "@/hooks/useTheme";
import { useCurrentUser } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import logoSrc from "@/assets/logo.png";
import {
  SUPPORTED_LOCALES,
  LOCALE_DISPLAY_NAMES,
  type SupportedLocale,
} from "@/i18n/config";

interface NavItem {
  to: string;
  labelKey: string;
  icon: LucideIcon;
  exact?: boolean;
}

const baseNav: NavItem[] = [
  { to: "/", labelKey: "home", icon: Home, exact: true },
  { to: "/services", labelKey: "services", icon: Server },
  { to: "/tools", labelKey: "tools", icon: Wrench },
  { to: "/agents", labelKey: "agents", icon: Bot },
  { to: "/logs", labelKey: "logs", icon: ScrollText },
  { to: "/users", labelKey: "users", icon: Users },
];

const secondaryNav: NavItem[] = [
  { to: "/settings", labelKey: "settings", icon: Settings },
];

function SidebarLink({
  item,
  collapsed,
}: {
  item: NavItem;
  collapsed: boolean;
}) {
  const { t } = useTranslation("nav");
  const label = t(`items.${item.labelKey}`);
  const Icon = item.icon;
  return (
    <Link
      to={item.to}
      activeOptions={{ exact: item.exact }}
      className="flex items-center gap-3 text-sm transition-all duration-200 sidebar-link font-medium"
      activeProps={{
        className:
          "flex items-center gap-3 text-sm transition-all duration-200 sidebar-link-active font-semibold",
      }}
      title={collapsed ? label : undefined}
    >
      <Icon size={18} className="shrink-0" />
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}

function BgShapes({ sidebarWidth }: { sidebarWidth: number }) {
  return (
    <div
      className="fixed inset-0 pointer-events-none overflow-hidden"
      style={{ left: sidebarWidth }}
      aria-hidden
    >
      <svg
        className="absolute -top-32 -right-32 w-[500px] h-[500px]"
        viewBox="0 0 500 500"
      >
        <circle
          cx="500"
          cy="0"
          r="380"
          fill="var(--terra)"
          fillOpacity="0.03"
        />
      </svg>
      <svg
        className="absolute bottom-16 left-10 w-36 h-36"
        viewBox="0 0 144 144"
      >
        <circle cx="72" cy="72" r="68" fill="var(--coral)" fillOpacity="0.04" />
      </svg>
      <svg
        className="absolute top-[40%] -right-24 w-60 h-60"
        viewBox="0 0 240 240"
      >
        <circle
          cx="120"
          cy="120"
          r="110"
          stroke="var(--terra)"
          strokeOpacity="0.04"
          strokeWidth="2"
          fill="none"
        />
      </svg>
      <svg
        className="absolute bottom-[20%] right-[30%] w-16 h-16"
        viewBox="0 0 64 64"
      >
        <rect
          x="8"
          y="8"
          width="48"
          height="48"
          rx="10"
          fill="var(--sage)"
          fillOpacity="0.04"
          transform="rotate(15 32 32)"
        />
      </svg>
    </div>
  );
}

const COLLAPSED_KEY = "sidebar_collapsed";

export function Shell({ children }: { children: ReactNode }) {
  const { t, i18n } = useTranslation(["common", "nav"]);
  const appName = useAppName();
  const { data: currentUserData } = useCurrentUser();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem(COLLAPSED_KEY) === "true",
  );
  const currentUser = currentUserData?.username ?? null;
  useEffect(() => {
    document.title = appName;
  }, [appName]);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(COLLAPSED_KEY, String(next));
      return next;
    });
  };

  const handleLogout = async () => {
    await api.auth.logout().catch(() => {});
    queryClient.clear();
    navigate({ to: "/login" });
  };

  const [langOpen, setLangOpen] = useState(false);
  const langRef = useRef<HTMLDivElement>(null);
  const currentLocale = (i18n.language ?? "en") as SupportedLocale;

  useEffect(() => {
    if (!langOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (langRef.current && !langRef.current.contains(e.target as Node)) {
        setLangOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [langOpen]);

  const sidebarWidth = collapsed ? 68 : 220;
  const isLightMode = theme === "light";
  const themeToggleLabel = isLightMode
    ? t("actions.switchToDarkMode", { ns: "nav" })
    : t("actions.switchToLightMode", { ns: "nav" });
  const themeLabel = isLightMode
    ? t("theme.dark", { ns: "nav" })
    : t("theme.light", { ns: "nav" });
  const signOutLabel = t("actions.signOut", { ns: "common" });

  return (
    <div className="flex h-screen overflow-hidden bg-canvas">
      <aside
        className="shrink-0 sidebar flex flex-col transition-all duration-300"
        style={{ width: sidebarWidth }}
      >
        <div
          className={`flex items-center border-b border-white/5 ${collapsed ? "flex-col gap-1 px-2 pt-5 pb-3" : "gap-3 px-5 pt-5 pb-4"}`}
        >
          <img
            src={logoSrc}
            alt=""
            className={`shrink-0 drop-shadow-lg transition-all duration-300 w-auto ${collapsed ? "h-9" : "h-8"}`}
          />
          {!collapsed && (
            <>
              <span className="text-xs font-bold text-white/90 tracking-wide uppercase flex-1">
                {appName}
              </span>
              <button
                onClick={toggleCollapsed}
                className="p-1 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
                aria-label={t("actions.collapseSidebar", { ns: "nav" })}
                title={t("actions.collapse", { ns: "nav" })}
              >
                <ChevronLeft size={16} />
              </button>
            </>
          )}
          {collapsed && (
            <button
              onClick={toggleCollapsed}
              className="p-1 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
              aria-label={t("actions.expandSidebar", { ns: "nav" })}
              title={t("actions.expand", { ns: "nav" })}
            >
              <ChevronRight size={16} />
            </button>
          )}
        </div>

        <nav className="flex-1 px-2 py-4 space-y-1">
          {baseNav.map((item) => (
            <SidebarLink key={item.to} item={item} collapsed={collapsed} />
          ))}
          <div className="my-3 border-t border-white/5" />
          {secondaryNav.map((item) => (
            <SidebarLink key={item.to} item={item} collapsed={collapsed} />
          ))}
        </nav>

        {!collapsed && (
          <div className="px-5 pb-2" aria-hidden>
            <svg
              width="100%"
              height="36"
              viewBox="0 0 180 36"
              fill="none"
              className="opacity-[0.07]"
            >
              <circle cx="18" cy="18" r="16" fill="var(--terra)" />
              <circle cx="50" cy="22" r="10" fill="var(--coral)" />
              <rect
                x="72"
                y="6"
                width="22"
                height="22"
                rx="5"
                fill="var(--sage)"
                transform="rotate(12 83 17)"
              />
            </svg>
          </div>
        )}

        <div className="px-2 py-2 border-t border-white/5 space-y-0.5">
          <button
            onClick={toggle}
            className={`sidebar-link flex items-center gap-3 text-sm font-medium transition-all duration-200 w-full ${collapsed ? "justify-center" : ""}`}
            aria-label={themeToggleLabel}
            title={themeToggleLabel}
          >
            {isLightMode ? (
              <Moon size={18} className="shrink-0" />
            ) : (
              <Sun size={18} className="shrink-0" />
            )}
            {!collapsed && <span>{themeLabel}</span>}
          </button>

          <div className="relative" ref={langRef}>
            <button
              onClick={() => setLangOpen((v) => !v)}
              className={`sidebar-link flex items-center gap-3 text-sm font-medium transition-all duration-200 w-full ${collapsed ? "justify-center" : ""}`}
              title={LOCALE_DISPLAY_NAMES[currentLocale]}
            >
              <Globe size={18} className="shrink-0" />
              {!collapsed && (
                <span>{LOCALE_DISPLAY_NAMES[currentLocale]}</span>
              )}
            </button>
            {langOpen && (
              <div className="absolute bottom-full left-0 mb-1 w-48 max-h-64 overflow-y-auto rounded-xl border border-line bg-surface shadow-lg z-50">
                {SUPPORTED_LOCALES.map((locale) => (
                  <button
                    key={locale}
                    onClick={() => {
                      i18n.changeLanguage(locale);
                      setLangOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                      currentLocale === locale
                        ? "text-terra font-semibold bg-terra-bg"
                        : "text-ink hover:bg-surface-hover"
                    }`}
                  >
                    {LOCALE_DISPLAY_NAMES[locale]}
                  </button>
                ))}
              </div>
            )}
          </div>

          {currentUser && (
            <div
              className={`flex items-center ${collapsed ? "flex-col gap-1 justify-center" : "gap-2.5 px-1.5"} py-1`}
            >
              <div className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center shrink-0">
                <span className="text-xs font-bold text-white/80">
                  {currentUser[0]?.toUpperCase()}
                </span>
              </div>
              {!collapsed && (
                <>
                  <span className="text-sm text-white/70 truncate flex-1">
                    {currentUser}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="text-xs text-white/30 hover:text-white/70 transition-colors whitespace-nowrap"
                    title={signOutLabel}
                  >
                    {signOutLabel}
                  </button>
                </>
              )}
              {collapsed && (
                <button
                  onClick={handleLogout}
                  className="p-1 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
                  title={signOutLabel}
                >
                  <LogOut size={14} />
                </button>
              )}
            </div>
          )}
        </div>
      </aside>

      <div className="flex-1 overflow-y-auto relative">
        <BgShapes sidebarWidth={sidebarWidth} />
        <div className="relative z-10 px-14 py-8">{children}</div>
      </div>
    </div>
  );
}
