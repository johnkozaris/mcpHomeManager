import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { i18n } from "@/i18n/init";
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
  const getPreviewLabel = () =>
    i18n.t("services.appCard.preview", { ns: "components" });

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

    await user.click(
      screen.getByRole("button", { name: getPreviewLabel() }),
    );
    expect(onPreview).toHaveBeenCalledWith(mockApp);
  });

  it("renders preview button", () => {
    render(<AppCard app={mockApp} onPreview={() => {}} />);
    expect(
      screen.getByRole("button", { name: getPreviewLabel() }),
    ).toBeInTheDocument();
  });
});
