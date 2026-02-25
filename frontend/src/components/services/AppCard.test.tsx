import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { AppCard } from "./AppCard";
import type { AppDefinition } from "@/lib/types";

const mockApp: AppDefinition = {
  name: "ha_entity_dashboard",
  service_type: "homeassistant",
  service_name: "homeassistant",
  title: "Entity Dashboard",
  description: "Interactive grid of entities",
  parameters_schema: {},
};

describe("AppCard", () => {
  it("renders title and description", () => {
    render(<AppCard app={mockApp} onPreview={() => {}} />);
    expect(screen.getByText("Entity Dashboard")).toBeInTheDocument();
    expect(
      screen.getByText("Interactive grid of entities"),
    ).toBeInTheDocument();
  });

  it("calls onPreview when preview button is clicked", async () => {
    const user = userEvent.setup();
    const onPreview = vi.fn();
    render(<AppCard app={mockApp} onPreview={onPreview} />);

    await user.click(screen.getByText("Preview"));
    expect(onPreview).toHaveBeenCalledWith(mockApp);
  });

  it("renders preview button", () => {
    render(<AppCard app={mockApp} onPreview={() => {}} />);
    expect(screen.getByText("Preview")).toBeInTheDocument();
  });
});
