import { render, screen } from "@testing-library/react";
import { EmptyState } from "./EmptyState";
import { Server } from "lucide-react";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(
      <EmptyState
        icon={Server}
        title="No items"
        description="Add something to get started."
      />,
    );
    expect(screen.getByText("No items")).toBeInTheDocument();
    expect(
      screen.getByText("Add something to get started."),
    ).toBeInTheDocument();
  });

  it("renders an icon", () => {
    const { container } = render(
      <EmptyState icon={Server} title="Test" description="Desc" />,
    );
    expect(container.querySelector("svg")).toBeInTheDocument();
  });

  it("renders children when provided", () => {
    render(
      <EmptyState icon={Server} title="Test" description="Desc">
        <button>Click me</button>
      </EmptyState>,
    );
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("does not render children container when no children", () => {
    const { container } = render(
      <EmptyState icon={Server} title="Test" description="Desc" />,
    );
    // The children wrapper div should not be present
    const buttons = container.querySelectorAll("button");
    expect(buttons).toHaveLength(0);
  });
});
