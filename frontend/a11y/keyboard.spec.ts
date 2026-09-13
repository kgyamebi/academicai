import { test, expect } from "@playwright/test";
import { assertAxe, registerStudent } from "./helpers";

test("login form is fully keyboard operable with visible focus", async ({ page }) => {
  await page.goto("/login", { waitUntil: "load" });
  await page.keyboard.press("Tab"); // skip link or first control
  // Walk to email field
  for (let i = 0; i < 8; i++) {
    const focused = page.locator(":focus");
    const id = await focused.getAttribute("id");
    if (id === "email") break;
    await page.keyboard.press("Tab");
  }
  await expect(page.locator("#email")).toBeFocused();
  await page.keyboard.type("keyboard-a11y@example.com");
  await page.keyboard.press("Tab");
  await expect(page.locator("#password")).toBeFocused();
  await page.keyboard.type("WrongPass1!");
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("alert")).toBeVisible({ timeout: 10000 });
  await assertAxe(page, "/login#keyboard");
});

test("settings delete dialog traps Tab focus", async ({ page }) => {
  await registerStudent(page);
  await page.goto("/app/settings", { waitUntil: "load" });
  await page.getByRole("button", { name: "Delete account" }).click();
  const dialog = page.getByRole("alertdialog", { name: "Delete this account?" });
  await expect(dialog).toBeVisible();
  const cancel = page.getByRole("button", { name: "Cancel" });
  const confirm = page.getByRole("button", { name: /Delete permanently|Confirm|Delete/i }).first();
  await expect(cancel).toBeFocused();
  await page.keyboard.press("Tab");
  // Focus stays inside dialog
  const inside = await page.evaluate(() => {
    const dlg = document.querySelector('[role="alertdialog"]');
    return !!(dlg && dlg.contains(document.activeElement));
  });
  expect(inside).toBe(true);
  await page.keyboard.press("Shift+Tab");
  const stillInside = await page.evaluate(() => {
    const dlg = document.querySelector('[role="alertdialog"]');
    return !!(dlg && dlg.contains(document.activeElement));
  });
  expect(stillInside).toBe(true);
  await cancel.focus();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
});

test("billing page keyboard reaches primary actions", async ({ page }) => {
  await registerStudent(page);
  await page.goto("/app/billing", { waitUntil: "load" });
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  let reached = false;
  for (let i = 0; i < 30; i++) {
    await page.keyboard.press("Tab");
    const tag = await page.evaluate(() => document.activeElement?.tagName);
    if (tag === "BUTTON" || tag === "A") {
      reached = true;
      break;
    }
  }
  expect(reached).toBe(true);
  await assertAxe(page, "/app/billing#keyboard");
});
