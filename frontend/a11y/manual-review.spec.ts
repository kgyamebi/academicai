import { test, expect } from "@playwright/test";
import { registerStudent, seedAssignmentAndReport } from "./helpers";

test("keyboard skip link works on the authenticated shell", async ({ page }) => {
  await registerStudent(page);
  await page.goto("/app/dashboard");
  await page.keyboard.press("Tab");
  await expect(page.locator('a[href="#main-content"]')).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();
});

test("200% and 400% zoom keep the dashboard heading in view without a trapped page", async ({ page }) => {
  await registerStudent(page);
  await page.goto("/app/dashboard");
  for (const zoom of [2, 4]) {
    await page.evaluate((value) => {
      document.documentElement.style.zoom = String(value);
    }, zoom);
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    const overflow = await page.evaluate(() => {
      const main = document.querySelector("#main-content");
      if (!(main instanceof HTMLElement)) return true;
      return main.scrollWidth > main.clientWidth + 80;
    });
    expect(overflow, `main overflow at zoom ${zoom}`).toBeFalsy();
  }
});

test("320px reflow keeps plan usage and settings usable", async ({ page }) => {
  await registerStudent(page);
  await page.setViewportSize({ width: 320, height: 640 });
  await page.goto("/app/billing");
  await expect(page.getByRole("heading", { name: "Plan usage" })).toBeVisible();
  await page.goto("/app/settings");
  await expect(page.getByRole("button", { name: "Delete account" })).toBeVisible();
});

test("reduced-motion preference does not hide report content", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await registerStudent(page);
  const seeded = await seedAssignmentAndReport(page);
  await page.goto(`/app/assignments/${seeded.assignmentId}/report?report=${seeded.reportId}`, {
    waitUntil: "networkidle",
  });
  await expect(page.getByRole("heading", { name: "Academic Performance Overview" })).toBeVisible();
  await expect(page.getByRole("table").first()).toBeVisible();
});

test("touch targets on app nav meet 44px", async ({ page }) => {
  await registerStudent(page);
  await page.goto("/app/dashboard");
  const sizes = await page.locator("nav[aria-label='App'] a, nav[aria-label='App'] button").evaluateAll((nodes) =>
    nodes.map((node) => {
      const box = node.getBoundingClientRect();
      return { w: box.width, h: box.height, text: node.textContent?.trim() };
    }),
  );
  for (const size of sizes) {
    expect(size.h, size.text).toBeGreaterThanOrEqual(44);
  }
});
