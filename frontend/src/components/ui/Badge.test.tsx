import { render, screen } from "@testing-library/react";
import { Badge } from "./Badge";

describe("Badge", () => {
  it("renders children text", () => {
    render(<Badge>healthy</Badge>);
    expect(screen.getByText("healthy")).toBeInTheDocument();
  });

  it("applies default variant styles", () => {
    render(<Badge>test</Badge>);
    const badge = screen.getByText("test");
    expect(badge).toHaveClass("bg-stone-bg");
  });

  it("applies positive variant", () => {
    render(<Badge variant="positive">ok</Badge>);
    expect(screen.getByText("ok")).toHaveClass("bg-sage-bg", "text-sage");
  });

  it("applies critical variant", () => {
    render(<Badge variant="critical">error</Badge>);
    expect(screen.getByText("error")).toHaveClass("bg-rust-bg", "text-rust");
  });

  it("applies brand variant", () => {
    render(<Badge variant="brand">mcp</Badge>);
    expect(screen.getByText("mcp")).toHaveClass("bg-terra-bg", "text-terra");
  });

  it("passes through additional className", () => {
    render(<Badge className="ml-2">test</Badge>);
    expect(screen.getByText("test")).toHaveClass("ml-2");
  });
});
