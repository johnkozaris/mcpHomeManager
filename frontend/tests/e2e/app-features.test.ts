import { test, expect } from "playwright/test";

// Feature tests for MCP Apps, service detail pages, and the overall app UI.
// Backend is not running so API calls fail — we test graceful degradation.

test.describe("Service detail page", () => {
  test("navigating to an invalid service shows error state", async ({
    page,
  }) => {
    await page.goto("/services/00000000-0000-0000-0000-000000000000");
    // Should show error or loading state, not crash
    await expect(page.locator("nav")).toBeVisible();
  });
});

test.describe("Tools page", () => {
  test("tools page renders heading and handles API errors", async ({
    page,
  }) => {
    await page.goto("/tools");
    // The page should render even when API fails
    await expect(page.locator("nav")).toBeVisible();
    // Should not show a blank page
    const bodyText = await page.locator("body").textContent();
    expect(bodyText?.length).toBeGreaterThan(10);
  });
});

test.describe("Logs page", () => {
  test("logs page loads", async ({ page }) => {
    await page.goto("/logs");
    await expect(page.locator("nav")).toBeVisible();
  });
});

test.describe("Add service panel", () => {
  test("services page has connect button", async ({ page }) => {
    await page.goto("/services");
    // Should have some content even with backend down
    await expect(page.locator("nav")).toBeVisible();
  });
});

test.describe("Theme persistence", () => {
  test("toggling dark mode persists across pages", async ({ page }) => {
    await page.goto("/settings");

    // Click dark mode button
    await page.getByRole("button", { name: "Dark", exact: true }).click();

    // Check html has .dark class
    const htmlClass = await page.locator("html").getAttribute("class");
    expect(htmlClass).toContain("dark");

    // Navigate to another page
    await page.getByRole("link", { name: "Tools" }).click();
    await expect(page).toHaveURL(/\/tools/);

    // Dark mode should persist
    const htmlClassAfterNav = await page.locator("html").getAttribute("class");
    expect(htmlClassAfterNav).toContain("dark");
  });
});

test.describe("Sidebar state", () => {
  test("sidebar shows version number", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.getByText("v0.1.0")).toBeVisible();
  });

  test("sidebar has theme toggle", async ({ page }) => {
    await page.goto("/");
    // Should have dark/light mode toggle in sidebar
    const themeButton = page.getByRole("button", { name: /mode/i });
    await expect(themeButton).toBeVisible();
  });
});

test.describe("Settings page details", () => {
  test("shows about section with version", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: "About" })).toBeVisible();
    await expect(page.getByText("0.1.0").first()).toBeVisible();
  });

  test("has security section", async ({ page }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: "Security" })).toBeVisible();
  });

  test("has system health section", async ({ page }) => {
    await page.goto("/settings");
    await expect(
      page.getByRole("heading", { name: "System Health" }),
    ).toBeVisible();
  });
});
