import { test, expect } from "playwright/test";

// These smoke tests verify that pages load and render without crashing.
// The backend is not running, so API calls will fail — we test that
// the UI handles errors gracefully and pages render structure.

test.describe("Smoke tests", () => {
  test("dashboard page loads with sidebar", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    // Sidebar logo should render
    await expect(page.getByText("MCP Home Manager")).toBeVisible();
    // Nav links should be present
    await expect(page.getByRole("link", { name: "Home" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Services" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Tools" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Agents" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Settings" })).toBeVisible();
  });

  test("services page loads", async ({ page }) => {
    await page.goto("/services");
    await expect(page.locator("nav")).toBeVisible();
  });

  test("tools page loads", async ({ page }) => {
    await page.goto("/tools");
    await expect(page.locator("nav")).toBeVisible();
  });

  test("settings page loads with sections", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Appearance" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "MCP Endpoint" }),
    ).toBeVisible();
    // Plugins card should be visible
    await expect(
      page.getByRole("heading", { name: "Plugins" }).first(),
    ).toBeVisible();
  });

  test("agents page loads with heading", async ({ page }) => {
    await page.goto("/agents");
    await expect(
      page.getByRole("heading", { name: "Agents", level: 1 }),
    ).toBeVisible();
  });

  test("agents page loads", async ({ page }) => {
    await page.goto("/agents");
    await expect(page.locator("nav")).toBeVisible();
  });

  test("navigation between pages works", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });

    // Navigate to Services
    await page.getByRole("link", { name: "Services" }).click();
    await expect(page).toHaveURL(/\/services/);

    // Navigate to Tools
    await page.getByRole("link", { name: "Tools" }).click();
    await expect(page).toHaveURL(/\/tools/);

    // Navigate to Agents
    await page.getByRole("link", { name: "Agents" }).click();
    await expect(page).toHaveURL(/\/agents/);

    // Navigate to Settings
    await page.getByRole("link", { name: "Settings" }).click();
    await expect(page).toHaveURL(/\/settings/);

    // Navigate back to Home
    await page.getByRole("link", { name: "Home" }).click();
    await expect(page).toHaveURL("http://localhost:3000/");
  });

  test("theme toggle buttons are visible on settings page", async ({
    page,
  }) => {
    await page.goto("/settings");

    // Theme toggle buttons in the Appearance card
    await expect(
      page.getByRole("button", { name: "Dark", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Light", exact: true }),
    ).toBeVisible();
  });
});
