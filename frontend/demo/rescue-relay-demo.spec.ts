import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

const OUTPUT = process.env.RESCUERELAY_DEMO_VIDEO ?? "/tmp/rescue-relay-demo.webm";
const architecture = readFileSync(new URL("../../docs/architecture.png", import.meta.url)).toString("base64");
const agentSource = readFileSync(new URL("../../src/rescue_relay/agent.py", import.meta.url), "utf8");
const matcherSource = readFileSync(new URL("../../src/rescue_relay/matching.py", import.meta.url), "utf8");

function escapeHtml(value: string) {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

async function slide(page: Page, eyebrow: string, title: string, body: string, visual = "") {
  await page.setContent(`
    <!doctype html><html><head><meta charset="utf-8"><style>
      * { box-sizing: border-box; }
      body { margin: 0; background: #f7f4ec; color: #173f35; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
      main { width: 1600px; height: 900px; padding: 92px 112px; display: grid; grid-template-columns: ${visual ? "0.82fr 1.18fr" : "1fr"}; gap: 72px; align-items: center; border-left: 26px solid #143f34; }
      .copy { max-width: 690px; }
      .eyebrow { color: #d9652d; font-size: 22px; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; }
      h1 { margin: 20px 0 28px; font-family: Georgia, serif; font-size: 66px; line-height: 1.04; letter-spacing: -.035em; }
      p { margin: 0; color: #4b625b; font-size: 28px; line-height: 1.5; }
      .visual { display: flex; align-items: center; justify-content: center; min-width: 0; }
      .visual img { width: 100%; max-height: 720px; object-fit: contain; border-radius: 18px; box-shadow: 0 18px 55px #173f3526; }
      .visual pre { width: 100%; max-height: 700px; overflow: hidden; margin: 0; padding: 34px; border-radius: 18px; background: #143f34; color: #e8f3ee; font: 18px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; box-shadow: 0 18px 55px #173f3530; white-space: pre-wrap; }
      footer { position: fixed; left: 112px; bottom: 56px; color: #73837e; font-size: 18px; letter-spacing: .04em; }
    </style></head><body><main><section class="copy"><div class="eyebrow">${escapeHtml(eyebrow)}</div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(body)}</p></section>${visual}</main><footer>RescueRelay · Agents for Humans</footer></body></html>
  `);
}

async function installCaption(page: Page) {
  await page.evaluate(() => {
    document.querySelector("#demo-caption")?.remove();
    document.querySelector("#demo-caption-style")?.remove();
    const style = document.createElement("style");
    style.id = "demo-caption-style";
    style.textContent = `
      #demo-caption { position: fixed; z-index: 999999; left: 50%; bottom: 28px; transform: translateX(-50%); width: min(1060px, calc(100vw - 80px)); padding: 18px 24px 20px; color: #f8fbf9; background: rgba(20,63,52,.94); border: 1px solid rgba(255,255,255,.14); border-radius: 14px; box-shadow: 0 18px 50px rgba(0,0,0,.25); pointer-events: none; backdrop-filter: blur(10px); }
      #demo-caption small { display: block; margin-bottom: 5px; color: #f5a37b; font: 800 12px/1.2 Inter,ui-sans-serif,system-ui; letter-spacing: .13em; text-transform: uppercase; }
      #demo-caption strong { display: block; font: 700 25px/1.25 Georgia,serif; }
      #demo-caption p { margin: 6px 0 0; color: #d8e5df; font: 500 17px/1.4 Inter,ui-sans-serif,system-ui; }
    `;
    document.head.append(style);
    const caption = document.createElement("aside");
    caption.id = "demo-caption";
    caption.innerHTML = "<small></small><strong></strong><p></p>";
    document.body.append(caption);
  });
}

async function caption(page: Page, eyebrow: string, title: string, body: string, duration = 5_000) {
  if (!(await page.locator("#demo-caption").count())) await installCaption(page);
  await page.locator("#demo-caption small").evaluate((element, text) => { element.textContent = text; }, eyebrow);
  await page.locator("#demo-caption strong").evaluate((element, text) => { element.textContent = text; }, title);
  await page.locator("#demo-caption p").evaluate((element, text) => { element.textContent = text; }, body);
  await page.waitForTimeout(duration);
}

async function smoothScroll(page: Page, selector: string) {
  await page.locator(selector).scrollIntoViewIfNeeded();
  await page.waitForTimeout(1_200);
}

test.afterEach(async ({ page }) => {
  const video = page.video();
  if (!video) return;
  await page.close();
  await video.saveAs(OUTPUT);
});

test("records the complete caption-led hackathon demo", async ({ page }) => {
  await slide(
    page,
    "Agents for Humans · Good Neighbor Agent",
    "RescueRelay turns expiring food offers into accountable handoffs.",
    "A quiet Strands agent for food-rescue coordinators—automating repetitive triage while keeping every real-world commitment human-owned.",
  );
  await page.waitForTimeout(8_000);

  await page.goto("/");
  await expect(page.getByRole("button", { name: "Simulate offer arrival" }).first()).toBeVisible();
  await caption(
    page,
    "The problem",
    "Every expiring offer starts the same coordination scramble.",
    "Interpret the food, verify pantry need and capacity, match pickup windows, draft outreach, and chase approval—before shelf life disappears.",
    8_000,
  );
  await caption(
    page,
    "Who it serves",
    "Small food-rescue teams that cannot afford more inbox busywork.",
    "The workspace is visibly labeled demo data, and the event intake is ready without pretending to be a connected production inbox.",
    7_000,
  );

  await page.getByRole("button", { name: "Simulate offer arrival" }).first().click();
  await expect(page.getByText("event completed", { exact: true })).toBeVisible();
  await caption(
    page,
    "One event · one durable receipt",
    "The real Strands tool loop completes in the background.",
    "A stable source ID is claimed before execution. Exact retries cannot rerun it; changed content under the same ID is rejected.",
    8_000,
  );

  await smoothScroll(page, "#run-trace");
  const steps = page.locator(".timeline-step");
  for (let index = 0; index < 4; index += 1) {
    await steps.nth(index).click();
    await page.waitForTimeout(2_500);
  }
  await caption(
    page,
    "Model-orchestrated · deterministic where correctness matters",
    "Read offers → load constraints → optimize → stage messages.",
    "The model chooses the tool sequence. Tested code owns quantities, capacity, hours, distance, and partial-allocation visibility.",
    8_000,
  );

  await page.locator(".timeline-step").nth(2).click();
  await caption(
    page,
    "Evidence before action",
    "412 lb matched with linked donor and pantry records.",
    "Donor messages remain untrusted data. A default-deny hook allows only four read, plan, and draft tools—and no send tool exists.",
    9_000,
  );

  await smoothScroll(page, "#pickups");
  await caption(
    page,
    "A complete operational plan",
    "Four offers, grounded pickup windows, visible confidence and state.",
    "Outreach is persisted as reversible drafts. Failures are stored as failures rather than dressed up as success.",
    8_000,
  );
  const auditDownload = page.waitForEvent("download");
  await page.getByTitle("Download audit evidence").click();
  const downloadedAudit = await auditDownload;
  const auditPath = `/tmp/rescue-relay-demo-audit-${process.pid}.json`;
  await downloadedAudit.saveAs(auditPath);
  const audit = JSON.parse(readFileSync(auditPath, "utf8"));
  expect(audit.schema_version).toBe("1.0");
  expect(audit.safety_assertions.outbound_send_capability).toBe(false);
  await caption(
    page,
    "Portable evidence",
    "The complete audit record exports with one click.",
    "Run state, evidence links, drafts, approvals, and impact remain inspectable outside the dashboard.",
    6_000,
  );

  await smoothScroll(page, "#decisions");
  await caption(
    page,
    "Human judgment is the product boundary",
    "Only two Harbor Market decisions interrupt the coordinator.",
    "Approving the proposed split is not enough to schedule the pickup; the real-world commitment remains a separate decision.",
    8_000,
  );
  await page.getByRole("button", { name: "Approve" }).first().click();
  await expect(page.getByRole("heading", { name: "1 decisions" })).toBeVisible();
  await page.waitForTimeout(4_000);
  await page.getByRole("button", { name: "Approve" }).first().click();
  await expect(page.getByRole("heading", { name: "All clear" })).toBeVisible();
  await expect(page.locator(".state-badge.scheduled")).toHaveCount(1);
  await caption(
    page,
    "Commitment recorded—not silently inferred",
    "The Harbor pickup changes to scheduled only after both approvals.",
    "Declining either decision follows the alternate atomic path: the dispatch is declined and its sibling decision closes.",
    8_000,
  );

  const eventPayload = `{
  "event_id": "harbor-market-2026-08-28T09:12:00Z",
  "offers": [{
    "donor": "Harbor Market",
    "item": "mixed produce",
    "quantity_lb": 180,
    "pickup_window": "today 14:00-17:00"
  }],
  "partners": [{
    "name": "Northside Community Pantry",
    "need_lb": 120,
    "capacity_lb": 120
  }]
}`;
  await slide(
    page,
    "Real event contract",
    "Replayable for the demo; caller-supplied in the product.",
    "The UI button uses labeled fixtures for a stable recording. The same validated action accepts custom offers and partner constraints, persists the payload before acknowledgement, and rejects conflicting reuse of an event ID.",
    `<section class="visual"><pre>${escapeHtml(eventPayload)}</pre></section>`,
  );
  await page.waitForTimeout(11_000);

  await slide(
    page,
    "Technical implementation",
    "A small, inspectable architecture with a hard commitment boundary.",
    "Validated events reach a Strands agent; a deterministic matcher produces an evidence-linked plan; SQLite records receipts, drafts, decisions, and impact; AgentCore provides the AWS runtime path.",
    `<section class="visual"><img alt="RescueRelay architecture" src="data:image/png;base64,${architecture}"></section>`,
  );
  await page.waitForTimeout(13_000);

  const excerpt = [
    "# Structural guard: unknown tools are denied before execution",
    ...agentSource.split("\n").slice(30, 35),
    ...agentSource.split("\n").slice(37, 42),
    "",
    "# Deterministic allocation remains outside model prose",
    ...matcherSource.split("\n").slice(14, 18),
    ...matcherSource.split("\n").slice(20, 31),
  ].join("\n");
  await slide(
    page,
    "Strands + AgentCore",
    "The agent can swap replay for Amazon Bedrock without moving correctness into a prompt.",
    "The repository includes an AWS-IAM-protected AgentCore entrypoint, explicit account/region targeting, and an audited minimal CodeZip deployment artifact.",
    `<section class="visual"><pre style="font-size:16px;line-height:1.38;padding:28px">${escapeHtml(excerpt)}</pre></section>`,
  );
  await page.waitForTimeout(13_000);

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "All clear" })).toBeVisible();
  await smoothScroll(page, "#decisions");
  await caption(
    page,
    "Transparent impact",
    "412 lb matched · 286 estimated meals · 38 estimated minutes saved.",
    "These are deterministic demo estimates, not field-validated claims or model prose. The pilot plan measures whether real handling time falls without more corrections or missed windows.",
    9_000,
  );

  await slide(
    page,
    "RescueRelay",
    "Turn an inbox into an accountable community handoff.",
    "Let coordinators spend their time on people—not repetitive message triage.",
  );
  await page.waitForTimeout(9_000);
});
