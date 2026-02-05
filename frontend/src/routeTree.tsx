import {
  createRootRoute,
  createRoute,
  createRouter,
  lazyRouteComponent,
  Outlet,
  redirect,
} from "@tanstack/react-router";
import { Shell } from "@/components/layout/Shell";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { RouteErrorFallback } from "@/components/RouteErrorFallback";
import { Dashboard } from "@/pages/Dashboard";
import { Login } from "@/pages/Login";
import { Setup } from "@/pages/Setup";
import { api, hasSessionToken } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

/* ─── Auth helper ─────────────────────────────────────────── */

async function requireAuth() {
  try {
    const config = await queryClient.ensureQueryData({
      queryKey: ["config"],
      queryFn: api.health.config,
      staleTime: 30_000,
    });
    if (config.setup_required) {
      throw redirect({ to: "/setup" });
    }
  } catch (err) {
    // If it's already a redirect, re-throw it
    if (err && typeof err === "object" && "to" in err) throw err;
    // Network error — let them through, they'll get errors on the pages
  }
  if (!hasSessionToken()) {
    throw redirect({ to: "/login" });
  }
}

/* ─── Root layout ─────────────────────────────────────────── */
const rootRoute = createRootRoute({
  component: () => (
    <ErrorBoundary>
      <Outlet />
    </ErrorBoundary>
  ),
});

/* ─── Setup route (no Shell) ─────────────────────────────── */
const setupRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/setup",
  component: Setup,
  beforeLoad: async () => {
    try {
      const config = await queryClient.ensureQueryData({
        queryKey: ["config"],
        queryFn: api.health.config,
        staleTime: 30_000,
      });
      if (!config.setup_required) {
        throw redirect({ to: "/" });
      }
    } catch (err) {
      if (err && typeof err === "object" && "to" in err) throw err;
    }
  },
});

/* ─── Login route (no Shell) ──────────────────────────────── */
const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: Login,
});

/* ─── Forgot password route (no Shell) ───────────────────── */
const forgotPasswordRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/forgot-password",
  component: lazyRouteComponent(
    () => import("@/pages/ForgotPassword"),
    "ForgotPassword",
  ),
});

/* ─── Reset password route (no Shell) ────────────────────── */
const resetPasswordRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/reset-password",
  validateSearch: (search: Record<string, unknown>) => ({
    token: typeof search.token === "string" ? search.token : "",
  }),
  component: lazyRouteComponent(
    () => import("@/pages/ResetPassword"),
    "ResetPassword",
  ),
});

/* ─── App layout (with Shell) ─────────────────────────────── */
const appLayout = createRoute({
  getParentRoute: () => rootRoute,
  id: "app",
  component: () => (
    <Shell>
      <Outlet />
    </Shell>
  ),
  beforeLoad: requireAuth,
});

/* ─── Routes ──────────────────────────────────────────────── */
const indexRoute = createRoute({
  getParentRoute: () => appLayout,
  path: "/",
  component: Dashboard,
});

const servicesRoute = createRoute({
  getParentRoute: () => appLayout,
  path: "/services",
  errorComponent: RouteErrorFallback,
  component: lazyRouteComponent(() => import("@/pages/Services"), "Services"),
});

const serviceDetailRoute = createRoute({
  getParentRoute: () => appLayout,
  path: "/services/$id",
  errorComponent: RouteErrorFallback,
  component: lazyRouteComponent(
    () => import("@/pages/ServiceDetail"),
    "ServiceDetail",
  ),
});

const toolsRoute = createRoute({
  getParentRoute: () => appLayout,
  path: "/tools",
  errorComponent: RouteErrorFallback,
  component: lazyRouteComponent(() => import("@/pages/Tools"), "Tools"),
});

const agentsRoute = createRoute({
  getParentRoute: () => appLayout,
  path: "/agents",
  errorComponent: RouteErrorFallback,
  component: lazyRouteComponent(() => import("@/pages/Agents"), "Agents"),
});

const logsRoute = createRoute({
  getParentRoute: () => appLayout,
  path: "/logs",
  errorComponent: RouteErrorFallback,
  component: lazyRouteComponent(() => import("@/pages/Logs"), "Logs"),
});

const usersRoute = createRoute({
  getParentRoute: () => appLayout,
  path: "/users",
  errorComponent: RouteErrorFallback,
  component: lazyRouteComponent(() => import("@/pages/Users"), "Users"),
});

const settingsRoute = createRoute({
  getParentRoute: () => appLayout,
  path: "/settings",
  errorComponent: RouteErrorFallback,
  component: lazyRouteComponent(() => import("@/pages/Settings"), "Settings"),
});

const notFoundRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "*",
  component: lazyRouteComponent(() => import("@/pages/NotFound"), "NotFound"),
});

/* ─── Route tree + router ─────────────────────────────────── */
const routeTree = rootRoute.addChildren([
  setupRoute,
  loginRoute,
  forgotPasswordRoute,
  resetPasswordRoute,
  appLayout.addChildren([
    indexRoute,
    servicesRoute,
    serviceDetailRoute,
    toolsRoute,
    agentsRoute,
    logsRoute,
    usersRoute,
    settingsRoute,
  ]),
  notFoundRoute,
]);

export const router = createRouter({
  routeTree,
  defaultPreload: "intent",
});

/* ─── Type registration ───────────────────────────────────── */
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
