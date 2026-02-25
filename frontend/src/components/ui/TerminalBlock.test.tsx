import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { TerminalBlock } from "./TerminalBlock";

describe("TerminalBlock", () => {
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
    expect(screen.getByText("Copy")).toBeDefined();
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
    await user.click(screen.getByText("Copy"));
    expect(screen.getByText("Copied")).toBeDefined();
    expect(writeText).toHaveBeenCalledWith("test");
  });
});
