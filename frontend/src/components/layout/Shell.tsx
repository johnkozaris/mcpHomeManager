import { type ReactNode, useEffect, useState } from "react";
import { useAppName } from "@/hooks/useAppName";
import { Link, useNavigate } from "@tanstack/react-router";
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
  type LucideIcon,
} from "lucide-react";
import { useTheme } from "@/hooks/useTheme";
import { useCurrentUser } from "@/hooks/useAuth";
import { clearSession } from "@/lib/api";
import logoSrc from "@/assets/logo.png";

const baseNav: {
  to: string;
  label: string;
  icon: LucideIcon;
  exact?: boolean;
}[] = [
  { to: "/", label: "Home", icon: Home, exact: true },
  { to: "/services", label: "Services", icon: Server },
  { to: "/tools", label: "Tools", icon: Wrench },
  { to: "/agents", label: "Agents", icon: Bot },
  { to: "/logs", label: "Logs", icon: ScrollText },
  { to: "/users", label: "Users", icon: Users },
];

const secondaryNav: { to: string; label: string; icon: LucideIcon }[] = [
  { to: "/settings", label: "Settings", icon: Settings },
];

function SidebarLink({
  item,
  collapsed,
}: {
  item: (typeof baseNav)[number];
  collapsed: boolean;
}) {
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
      title={collapsed ? item.label : undefined}
    >
      <Icon size={18} className="shrink-0" />
      {!collapsed && <span>{item.label}</span>}
    </Link>
  );
}

/* Background geometric shapes — Bauhaus style */
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
  const appName = useAppName();
  const { data: currentUserData } = useCurrentUser();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem(COLLAPSED_KEY) === "true",
  );
  const currentUser =
    currentUserData?.username ?? localStorage.getItem("username");
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
    try {
      await fetch("/api/auth/logout", {
        method: "DELETE",
        credentials: "same-origin",
      }).catch(() => {});
    } finally {
      clearSession();
    }
    navigate({ to: "/login" });
  };

  const sidebarWidth = collapsed ? 68 : 220;

  return (
    <div className="flex h-screen overflow-hidden bg-canvas">
      {/* Sidebar */}
      <aside
        className="shrink-0 sidebar flex flex-col transition-all duration-300"
        style={{ width: sidebarWidth }}
      >
        {/* Logo + collapse toggle */}
        <div
          className={`flex items-center border-b border-white/5 ${collapsed ? "flex-col gap-1 px-2 pt-5 pb-3" : "gap-3 px-5 pt-5 pb-4"}`}
        >
          <img
            src={logoSrc}
            alt=""
            width={collapsed ? 36 : 32}
            height={collapsed ? 36 : 32}
            className="shrink-0 drop-shadow-lg transition-all duration-300"
          />
          {!collapsed && (
            <>
              <span className="text-xs font-bold text-white/90 tracking-wide uppercase flex-1">
                {appName}
              </span>
              <button
                onClick={toggleCollapsed}
                className="p-1 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
                aria-label="Collapse sidebar"
                title="Collapse"
              >
                <ChevronLeft size={16} />
              </button>
            </>
          )}
          {collapsed && (
            <button
              onClick={toggleCollapsed}
              className="p-1 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
              aria-label="Expand sidebar"
              title="Expand"
            >
              <ChevronRight size={16} />
            </button>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-4 space-y-1">
          {baseNav.map((item) => (
            <SidebarLink key={item.to} item={item} collapsed={collapsed} />
          ))}
          <div className="my-3 border-t border-white/5" />
          {secondaryNav.map((item) => (
            <SidebarLink key={item.to} item={item} collapsed={collapsed} />
          ))}
        </nav>

        {/* Decorative shapes in sidebar */}
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

        {/* Footer — theme + user */}
        <div className="px-2 py-2 border-t border-white/5 space-y-0.5">
          {/* Theme toggle */}
          <button
            onClick={toggle}
            className={`sidebar-link flex items-center gap-3 text-sm font-medium transition-all duration-200 w-full ${collapsed ? "justify-center" : ""}`}
            aria-label={theme === "light" ? "Dark mode" : "Light mode"}
            title={theme === "light" ? "Dark mode" : "Light mode"}
          >
            {theme === "light" ? (
              <Moon size={18} className="shrink-0" />
            ) : (
              <Sun size={18} className="shrink-0" />
            )}
            {!collapsed && <span>{theme === "light" ? "Dark" : "Light"}</span>}
          </button>

          {/* User row */}
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
                    className="text-2xs text-white/30 hover:text-white/70 transition-colors whitespace-nowrap"
                    title="Sign out"
                  >
                    Sign out
                  </button>
                </>
              )}
              {collapsed && (
                <button
                  onClick={handleLogout}
                  className="p-1 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
                  title="Sign out"
                >
                  <LogOut size={14} />
                </button>
              )}
            </div>
          )}
        </div>
      </aside>

      {/* Main — wider content area with bg shapes */}
      <div className="flex-1 overflow-y-auto relative">
        <BgShapes sidebarWidth={sidebarWidth} />
        <div className="relative z-10 px-14 py-8">{children}</div>
      </div>
    </div>
  );
}
