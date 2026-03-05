import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { i18n } from "@/i18n/init";
import { TerminalBlock } from "./TerminalBlock";

describe("TerminalBlock", () => {
  const getCopyLabel = () =>
    i18n.t("ui.terminalBlock.copy", { ns: "components" });
  const getCopiedLabel = () =>
    i18n.t("ui.terminalBlock.copied", { ns: "components" });
  const getCopyToClipboardLabel = () =>
    i18n.t("ui.terminalBlock.copyToClipboard", { ns: "components" });

  it("renders code content", () => {
    render(<TerminalBlock code="echo hello" />);
    expect(screen.getByText("echo hello")).toBeDefined();
  });

  it("shows label when provided", () => {
    render(<TerminalBlock code="ls" label="Terminal" />);
    expect(screen.getByText("Terminal")).toBeDefined();
  });

  it("has three traffic light dots", () => {
    const { container } = render(<TerminalBlock code="test" />);
    const dots = container.querySelectorAll("span.w-3.h-3.rounded-full");
    expect(dots.length).toBe(3);
  });

  it("shows copy button", () => {
    render(<TerminalBlock code="test" />);
    expect(
      screen.getByRole("button", { name: getCopyToClipboardLabel() }),
    ).toBeInTheDocument();
    expect(screen.getByText(getCopyLabel())).toBeInTheDocument();
  });

  it("changes to Copied after click", async () => {
    const user = userEvent.setup();
    // Mock clipboard via defineProperty since navigator.clipboard is read-only
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      writable: true,
      configurable: true,
    });

    render(<TerminalBlock code="test" />);
    await user.click(
      screen.getByRole("button", { name: getCopyToClipboardLabel() }),
    );
    expect(screen.getByText(getCopiedLabel())).toBeInTheDocument();
    expect(writeText).toHaveBeenCalledWith("test");
  });
});
