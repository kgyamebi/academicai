import { test, expect } from "@playwright/test";
import { assertAxe, registerStudent, seedAssignmentAndReport } from "./helpers";

const STATIC_ROUTES = ["/app/dashboard", "/app/assignments", "/app/settings", "/app/billing", "/app/coach", "/app/admin"];

for (const route of STATIC_ROUTES) {
  test(`axe-core wcag 2.2 aa on ${route}`, async ({ page }) => {
    await registerStudent(page);
    await page.goto(route, { waitUntil: "load" });
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await assertAxe(page, route);
  });
}

test("axe-core wcag 2.2 aa on assignment workspace, report and versions", async ({ page }) => {
  await registerStudent(page);
  const seeded = await seedAssignmentAndReport(page);
  const routes = [
    `/app/assignments/${seeded.assignmentId}`,
    `/app/assignments/${seeded.assignmentId}/report?report=${seeded.reportId}`,
    `/app/assignments/${seeded.assignmentId}/versions`,
  ];
  for (const route of routes) {
    await page.goto(route, { waitUntil: "load" });
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await assertAxe(page, route);
  }
});

test("admin signed-in overview passes axe", async ({ page }) => {
  await page.goto("/login", { waitUntil: "load" });
  await page.getByLabel("Email").fill("a11y-admin@example.com");
  await page.getByLabel("Password").fill("A11yAdminBootstrap16");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.waitForURL(/\/app\//);
  await page.goto("/app/admin", { waitUntil: "load" });
  await expect(page.getByRole("heading", { name: "Admin" })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await assertAxe(page, "/app/admin#signed-in");
});

test("settings dialog is keyboard reachable and announced", async ({ page }) => {
  await registerStudent(page);
  await page.goto("/app/settings", { waitUntil: "load" });
  await page.getByRole("button", { name: "Delete account" }).click();
  const dialog = page.getByRole("alertdialog", { name: "Delete this account?" });
  await expect(dialog).toBeVisible();
  await expect(page.getByRole("button", { name: "Cancel" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Delete account" })).toBeFocused();
  await assertAxe(page, "/app/settings#dialog");
});

test("report scorecard and findings stay in a table", async ({ page }) => {
  await registerStudent(page);
  const seeded = await seedAssignmentAndReport(page);
  await page.goto(`/app/assignments/${seeded.assignmentId}/report?report=${seeded.reportId}`, {
    waitUntil: "load",
  });
  await expect(page.getByRole("heading", { name: "Academic Performance Overview" })).toBeVisible();
  await expect(page.getByRole("table", { name: /Category scores/ })).toBeVisible();
  await expect(page.getByRole("img", { name: /Diagnostic score/ })).toBeVisible();
  await assertAxe(page, "report-populated");
});
