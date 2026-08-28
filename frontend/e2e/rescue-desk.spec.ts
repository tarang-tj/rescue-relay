import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  const resetResponse = await page.request.post("http://127.0.0.1:8010/api/reset");
  expect(resetResponse.ok()).toBe(true);
  await page.goto("/");
  await expect(page.locator(".empty-desk").getByRole("button", { name: "Run inbox scan" })).toBeVisible();
});

test("runs the agent, preserves dates, rejects safely, and exports evidence", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "Desktop evidence flow");
  const consoleProblems: string[] = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) consoleProblems.push(message.text());
  });

  await expect(page).toHaveTitle(/RescueRelay/);
  await page.locator(".empty-desk").getByRole("button", { name: "Run inbox scan" }).click();

  await expect(page.getByRole("heading", { name: "Today’s proposed pickups" })).toBeVisible();
  await expect(page.getByText("Today 16:30-17:15", { exact: true })).toBeVisible();
  await expect(page.getByText("Tomorrow 09:30-10:15", { exact: true })).toBeVisible();
  await expect(page.getByText("4 drafts", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "2 decisions" })).toBeVisible();
  await page.screenshot({ path: "/tmp/rescue-relay-desktop-pending.png", fullPage: true });

  const downloadReady = page.waitForEvent("download");
  await page.getByTitle("Download audit evidence").click();
  const download = await downloadReady;
  expect(download.suggestedFilename()).toBe("rescue-relay-audit.json");
  await download.saveAs("/tmp/rescue-relay-audit.json");

  await page.getByRole("button", { name: "Decline" }).first().click();
  await expect(page.getByRole("heading", { name: "All clear" })).toBeVisible();
  await expect(page.locator(".decision-card.rejected")).toHaveCount(2);
  await expect(page.locator(".state-badge.declined")).toHaveCount(1);
  expect(consoleProblems).toEqual([]);

  await page.screenshot({ path: `/tmp/rescue-relay-${testInfo.project.name}.png`, fullPage: true });
  await page.getByTitle("Reset demo").click();
  await expect(page.locator(".empty-desk").getByRole("button", { name: "Run inbox scan" })).toBeVisible();
});

test("mobile layout keeps primary controls and decisions usable", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile-chromium", "Mobile evidence flow");
  await page.locator(".empty-desk").getByRole("button", { name: "Run inbox scan" }).click();

  await expect(page.getByRole("button", { name: "Approve" }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Decline" }).first()).toBeVisible();
  const horizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(horizontalOverflow).toBe(false);

  await page.screenshot({ path: `/tmp/rescue-relay-mobile-${testInfo.project.name}.png`, fullPage: true });
});
