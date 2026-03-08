import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { i18n } from "@/i18n/init";
import type { OpenAPIImportResult } from "@/lib/types";
import { ImportOpenAPIModal } from "./ImportOpenAPIModal";

const importOpenapiMock = vi.hoisted(() => ({
  mutate: vi.fn(),
  isPending: false,
  isError: false,
  error: null as unknown,
}));

vi.mock("@/hooks/useServices", () => ({
  useImportOpenapi: () => importOpenapiMock,
}));

vi.mock("@/components/ui/MonacoEditor", () => ({
  MonacoEditor: ({
    value,
    onChange,
  }: {
    value: string;
    onChange?: (value: string) => void;
  }) => (
    <textarea
      aria-label="OpenAPI specification"
      value={value}
      onChange={(event) => onChange?.(event.target.value)}
    />
  ),
}));

function mockImportResult(result: OpenAPIImportResult) {
  importOpenapiMock.mutate.mockImplementation(
    (
      _variables: { serviceId: string; spec: string },
      options?: { onSuccess?: (result: OpenAPIImportResult) => void },
    ) => {
      options?.onSuccess?.(result);
    },
  );
}

function renderModal(onClose = vi.fn()) {
  render(<ImportOpenAPIModal open onClose={onClose} serviceId="svc-123" />);
  return { onClose };
}

describe("ImportOpenAPIModal", () => {
  const importLabel = () =>
    i18n.t("services.importOpenApiModal.import", { ns: "components" });
  const warningSummary = (count: number) =>
    i18n.t("services.importOpenApiModal.warningsSummary", {
      ns: "components",
      count,
    });
  const partialSummary = (importedCount: number, skippedCount: number) =>
    i18n.t("services.importOpenApiModal.partialSummary", {
      ns: "components",
      importedCount,
      skippedCount,
    });

  beforeEach(() => {
    vi.useFakeTimers();
    importOpenapiMock.mutate.mockReset();
    importOpenapiMock.isPending = false;
    importOpenapiMock.isError = false;
    importOpenapiMock.error = null;
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it("auto-closes after a clean import success", async () => {
    mockImportResult({
      status: "success",
      imported: ["create_user"],
      skipped: [],
      warnings: [],
      tools_count: 1,
    });
    const { onClose } = renderModal();

    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "openapi: 3.0.0" },
    });
    fireEvent.click(screen.getByRole("button", { name: importLabel() }));

    expect(onClose).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1499);
    });
    expect(onClose).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("keeps the modal open when a successful import includes warnings", async () => {
    const warning =
      "Operation GET /extremely/long/path/that/keeps/going/without/a/natural/breakpoint/and/still/needs/to/be/read was imported with fallback parameter handling.";
    mockImportResult({
      status: "success",
      imported: ["create_user"],
      skipped: [],
      warnings: [warning],
      tools_count: 1,
    });
    const { onClose } = renderModal();

    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "openapi: 3.0.0" },
    });
    fireEvent.click(screen.getByRole("button", { name: importLabel() }));

    expect(screen.getByText(warningSummary(1))).toBeInTheDocument();
    expect(screen.getByText(warning)).toBeInTheDocument();

    await vi.advanceTimersByTimeAsync(5000);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("keeps the modal open when some tools are skipped", async () => {
    mockImportResult({
      status: "success",
      imported: ["create_user"],
      skipped: ["delete_user"],
      warnings: [],
      tools_count: 1,
    });
    const { onClose } = renderModal();

    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "openapi: 3.0.0" },
    });
    fireEvent.click(screen.getByRole("button", { name: importLabel() }));

    expect(screen.getByText(partialSummary(1, 1))).toBeInTheDocument();

    await vi.advanceTimersByTimeAsync(5000);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("clears the draft spec when dismissed with Escape", () => {
    const onClose = vi.fn();
    const { rerender } = render(
      <ImportOpenAPIModal open onClose={onClose} serviceId="svc-123" />,
    );

    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "openapi: 3.0.0" },
    });
    fireEvent.keyDown(document, { key: "Escape" });

    expect(onClose).toHaveBeenCalledTimes(1);

    rerender(
      <ImportOpenAPIModal open={false} onClose={onClose} serviceId="svc-123" />,
    );
    rerender(<ImportOpenAPIModal open onClose={onClose} serviceId="svc-123" />);

    expect(screen.getByRole("textbox")).toHaveValue("");
  });
});
