import { expect, test, type Page } from "@playwright/test";

const api = "http://127.0.0.1:8193";

async function ask(page: Page, question = "Do I need a permit before I build a new hog barn?") {
  const box = page.getByRole("textbox", { name: "Compliance question" });
  await box.fill(question);
  await page.getByRole("button", { name: "Ask question" }).click();
}

test.beforeEach(async ({ request }) => {
  await request.post(`${api}/__e2e/reset`);
});

test("U01 producer interface loads with evidence and confidentiality boundaries", async ({ page }) => {
  await page.goto("./");
  await expect(page.getByRole("heading", { name: /Know the rule/ })).toBeVisible();
  await expect(page.getByText("Built to show its work.")).toBeVisible();
  await expect(page.getByText(/Do not enter names, exact addresses, or confidential records/)).toBeVisible();
  expect(await page.content()).not.toContain("OPENAI_API_KEY");
});

test("U02 blank questions keep the ask control disabled", async ({ page }) => {
  await page.goto("./");
  await expect(page.getByRole("button", { name: "Ask question" })).toBeDisabled();
});

test("U03 a producer receives a cited answer from the joined browser and API flow", async ({ page }) => {
  await page.goto("./");
  await ask(page);
  await expect(page.getByText(/Check the Nebraska approval requirement/)).toBeVisible();
  await expect(page.getByText("Authoritative sources found")).toBeVisible();
  await expect(page.getByRole("link", { name: "View source 1" }).first()).toBeVisible();
});

test("U04 farm context changes the returned applicability explanation", async ({ page }) => {
  await page.goto("./");
  await page.locator("details.control-panel").filter({ hasText: "Farm facts" }).locator("summary").click();
  await page.getByLabel("County").fill("Madison");
  await page.getByLabel("Operation").selectOption("confinement");
  await ask(page);
  await expect(page.getByText(/facts for Madison remain necessary/)).toBeVisible();
});

test("U05 topic scope reaches the API and remains visible in cited reasoning", async ({ page }) => {
  await page.goto("./");
  await page.getByText("Search scope").click();
  await page.getByLabel("Topic").selectOption("labor");
  await ask(page, "Can a 15-year-old clean a hog barn?");
  await expect(page.getByText(/retrieved labor source/)).toBeVisible();
});

test("U06 the interface prevents removing the final source tier", async ({ page }) => {
  await page.goto("./");
  await page.getByText("Search scope").click();
  const government = page.getByRole("checkbox", { name: /Government and statutes/ });
  const guidance = page.getByRole("checkbox", { name: /Official and extension guidance/ });
  await guidance.uncheck();
  await expect(government).toBeDisabled();
});

test("U07 helpful feedback is saved and reflected in the interface", async ({ page }) => {
  await page.goto("./");
  await ask(page);
  const helpful = page.getByRole("button", { name: "Mark helpful" });
  await helpful.click();
  await expect(helpful).toHaveClass(/selected/);
});

test("U08 a not-helpful rating accepts an explanatory comment", async ({ page }) => {
  await page.goto("./");
  await ask(page);
  await page.getByRole("button", { name: "Mark not helpful" }).click();
  await page.getByLabel("What was missing or wrong?").fill("The capacity threshold needs a clearer citation.");
  await page.getByRole("button", { name: "Send feedback" }).click();
  await expect(page.getByLabel("What was missing or wrong?")).toHaveCount(0);
});

test("U09 a saved answer survives a browser reload on the same device", async ({ page }) => {
  await page.goto("./");
  await ask(page);
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByRole("button", { name: /Saved on this device/ })).toBeVisible();
  await page.reload();
  await expect(page.getByText(/Check the Nebraska approval requirement/)).toBeVisible();
});

test("U10 a service failure gives a dismissible error and preserves follow-up input", async ({ page }) => {
  await page.goto("./");
  await ask(page, "server failure please");
  await expect(page.locator(".error[role='alert']")).toContainText("temporarily unavailable");
  await page.getByRole("button", { name: "Dismiss" }).click();
  await expect(page.getByRole("textbox", { name: "Follow-up question" })).toBeEnabled();
});

test("A01 malformed JSON is rejected without a stack trace", async ({ request }) => {
  const response = await request.post(`${api}/api/chat`, { headers: { "content-type": "application/json" }, data: "{" });
  expect(response.status()).toBe(422);
  expect(await response.text()).not.toMatch(/Traceback|site-packages/);
});

test("A02 whitespace-only and too-short questions are rejected", async ({ request }) => {
  const response = await request.post(`${api}/api/chat`, { data: { question: "  " } });
  expect(response.status()).toBe(422);
});

test("A03 oversized request bodies are rejected before parsing", async ({ request }) => {
  const response = await request.post(`${api}/api/chat`, { data: { question: "x".repeat(40_000) } });
  expect(response.status()).toBe(413);
  expect((await response.json()).detail).toMatch(/too large/i);
});

test("A04 unsupported compliance topics are rejected", async ({ request }) => {
  const response = await request.post(`${api}/api/chat`, { data: { question: "Is this required?", topics: ["tax_advice"] } });
  expect(response.status()).toBe(422);
});

test("A05 impossible farm capacity is rejected", async ({ request }) => {
  const response = await request.post(`${api}/api/chat`, { data: { question: "Do I need a permit?", farm_context: { animal_unit_capacity: -1 } } });
  expect(response.status()).toBe(422);
});

test("A06 a disallowed browser origin receives no CORS permission", async ({ request }) => {
  const response = await request.fetch(`${api}/api/chat`, { method: "OPTIONS", headers: { origin: "https://attacker.example", "access-control-request-method": "POST" } });
  expect(response.status()).toBe(400);
  expect(response.headers()["access-control-allow-origin"]).toBeUndefined();
});

test("A07 the chat rate limit stops a request flood", async ({ request }) => {
  await request.post(`${api}/__e2e/reset`);
  let response;
  for (let index = 0; index < 21; index += 1) response = await request.post(`${api}/api/chat`, { data: { question: `Permit question ${index}` } });
  expect(response!.status()).toBe(429);
  expect((await response!.json()).detail).toMatch(/Too many questions/);
});

test("A08 conversation history remains behind the admin boundary", async ({ request }) => {
  const response = await request.get(`${api}/api/conversations/33333333-3333-4333-8333-333333333333`);
  expect(response.status()).toBe(401);
  expect((await response.json()).detail).toBe("Invalid admin key");
});

test("A09 active HTML is handled as data and yields no executable output", async ({ request }) => {
  const response = await request.post(`${api}/api/chat`, { data: { question: "<script>window.pwned=true</script> permit evidence" } });
  expect(response.status()).toBe(200);
  const payload = await response.json();
  expect(payload.evidence_status).toBe("insufficient");
  expect(JSON.stringify(payload)).not.toContain("<script>");
});

test("A10 unknown routes and unsupported methods fail closed with security headers", async ({ request }) => {
  const [unknown, method] = await Promise.all([
    request.get(`${api}/api/not-a-route`),
    request.put(`${api}/api/sources`, { data: {} })
  ]);
  expect(unknown.status()).toBe(404);
  expect(method.status()).toBe(405);
  expect(unknown.headers()["x-content-type-options"]).toBe("nosniff");
  expect(method.headers()["x-frame-options"]).toBe("DENY");
  expect(`${await unknown.text()}${await method.text()}`).not.toMatch(/OPENAI_API_KEY|ADMIN_API_KEY|Traceback/);
});
