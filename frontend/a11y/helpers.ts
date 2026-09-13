import { expect, type APIRequestContext, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

export const ESSAY = `
Globalization has changed trade in developing economies. This essay argues that the effects are mixed: export growth often rises, but inequality can widen unless industrial policy is strong.

Comparison
East Asian industrialisers used trade alongside policy, whereas some commodity exporters liberalised without upgrading (Rodrik, 2011). The difference suggests that openness alone does not determine outcomes.

Evaluation
Therefore globalization should be evaluated by distribution and capability, not only by average GDP.

Conclusion
The question is not whether globalization exists, but which effects dominate in which developing economies.

References
Rodrik, D. (2011). The globalization paradox. W. W. Norton.
`;

export async function assertAxe(page: Page, route: string) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .exclude("nextjs-portal")
    .exclude("[data-next-badge-root]")
    .analyze();
  expect(results.violations, `${route}\n${JSON.stringify(results.violations, null, 2)}`).toEqual([]);
}

export async function registerStudent(page: Page) {
  const email = `a11y-${Date.now()}@example.com`;
  await page.goto("/register");
  await page.getByLabel("Full name").fill("A11y Tester");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel(/^Password/).fill("password12");
  await page.getByRole("button", { name: "Create account" }).click();
  await page.waitForURL(/\/app\/dashboard/);
  return email;
}

async function csrfHeaders(page: Page) {
  const cookies = await page.context().cookies();
  const csrf = cookies.find((c) => c.name === "ac_csrf")?.value || "";
  return csrf ? { "X-CSRF-Token": csrf } : {};
}

export async function apiJson<T>(page: Page, path: string, init?: { method?: string; data?: unknown }): Promise<T> {
  const headers = { ...(await csrfHeaders(page)) };
  const request: APIRequestContext = page.request;
  const response = init?.method && init.method !== "GET"
    ? await request.fetch(path, { method: init.method, data: init.data, headers })
    : await request.get(path, { headers });
  expect(response.ok(), `${path} ${response.status()} ${await response.text()}`).toBeTruthy();
  return response.json() as Promise<T>;
}

export async function seedAssignmentAndReport(page: Page) {
  const assignment = await apiJson<{ id: string }>(page, "/api/assignments", {
    method: "POST",
    data: {
      title: "A11y assignment",
      question: "Compare and evaluate the effects of globalization on developing economies.",
      academic_level: "undergraduate",
      citation_style: "apa7",
    },
  });
  const document = await apiJson<{ id: string }>(page, "/api/documents/paste", {
    method: "POST",
    data: { assignment_id: assignment.id, text: ESSAY, filename: "draft.txt" },
  });
  const created = await apiJson<{ id: string }>(page, "/api/analysis", {
    method: "POST",
    data: { assignment_id: assignment.id, document_id: document.id, analysis_type: "full" },
  });
  for (let i = 0; i < 40; i += 1) {
    const job = await apiJson<{ report_id?: string | null; status?: string }>(page, `/api/analysis/${created.id}`);
    if (job.report_id) return { assignmentId: assignment.id, reportId: job.report_id };
    await page.waitForTimeout(400);
  }
  throw new Error("Analysis did not produce a report for accessibility seeding.");
}
