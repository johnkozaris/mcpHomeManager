import { render, screen, waitFor } from "@testing-library/react";
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from "@tanstack/react-router";
import { LogEntryDetail } from "./LogEntryDetail";
import type { AuditEntry } from "@/lib/types";
import { i18n } from "@/i18n/init";

const baseEntry: AuditEntry = {
  id: "abc-123",
  service_name: "forgejo",
  tool_name: "list_repos",
  input_summary: '{"page": 1}',
  status: "success",
  duration_ms: 42,
  error_message: null,
  created_at: "2025-01-15T10:00:00Z",
};

function renderWithRouter(ui: React.ReactElement) {
  const rootRoute = createRootRoute({ component: () => ui });
  const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/",
    component: () => ui,
  });
  const router = createRouter({
    routeTree: rootRoute.addChildren([indexRoute]),
    history: createMemoryHistory({ initialEntries: ["/"] }),
  });
  return render(<RouterProvider router={router} />);
}

describe("LogEntryDetail", () => {
  const getErrorLabel = () =>
    i18n.t("logs.logEntryDetail.error", { ns: "components" });
  const getViewServiceLabel = () =>
    i18n.t("logs.logEntryDetail.viewService", { ns: "components" });

  it("renders duration and timestamp", async () => {
    renderWithRouter(<LogEntryDetail entry={baseEntry} />);
    await waitFor(() => {
      expect(screen.getByText("42ms")).toBeInTheDocument();
    });
  });

  it("renders input summary when present", async () => {
    renderWithRouter(<LogEntryDetail entry={baseEntry} />);
    await waitFor(() => {
      expect(screen.getByText('{"page": 1}')).toBeInTheDocument();
    });
  });

  it("renders error message when present", async () => {
    const errorEntry: AuditEntry = {
      ...baseEntry,
      status: "error",
      error_message: "Connection refused",
    };
    renderWithRouter(<LogEntryDetail entry={errorEntry} />);
    await waitFor(() => {
      expect(screen.getByText("Connection refused")).toBeInTheDocument();
    });
  });

  it("does not render error section for success entries", async () => {
    renderWithRouter(<LogEntryDetail entry={baseEntry} />);
    await waitFor(() => {
      expect(screen.queryByText(getErrorLabel())).not.toBeInTheDocument();
    });
  });

  it("renders View Service link when serviceId is provided", async () => {
    renderWithRouter(<LogEntryDetail entry={baseEntry} serviceId="svc-456" />);
    await waitFor(() => {
      const link = screen.getByRole("link", { name: getViewServiceLabel() });
      expect(link).toBeInTheDocument();
      expect(link.closest("a")).toHaveAttribute("href", "/services/svc-456");
    });
  });

  it("does not render View Service link when serviceId is absent", async () => {
    renderWithRouter(<LogEntryDetail entry={baseEntry} />);
    await waitFor(() => {
      expect(
        screen.queryByRole("link", { name: getViewServiceLabel() }),
      ).not.toBeInTheDocument();
    });
  });
});
