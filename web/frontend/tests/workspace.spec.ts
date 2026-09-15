import { expect, test, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import catalog from "./fixtures/catalog.json" with { type: "json" };
import result from "./fixtures/result.json" with { type: "json" };
const id = result.job_id;
const path = `/api/v1/design-jobs/${id}`;
const job = (status = "queued") => ({
  job_id: id,
  topology: result.topology,
  status,
  progress: status === "succeeded" ? 100 : 15,
  stage: "topology",
  created_at: "2026-09-14T10:00:00Z",
});
const file = {
  id: "result-json",
  name: "result.json",
  media_type: "application/json",
  size: 100,
  download_url: `${path}/artifacts/result-json`,
  stage: "report",
  schema_version: "1.0",
  sha256: "a".repeat(64),
};
async function setup(page: Page) {
  await page.route("**/api/v1/topologies", (route) =>
    route.fulfill({ json: catalog }),
  );
  await page.route(`**${path}/result`, (route) =>
    route.fulfill({ json: result }),
  );
  await page.route(`**${path}/artifacts`, (route) =>
    route.fulfill({ json: [file] }),
  );
}
async function openBuck(page: Page) {
  await page.goto("/");
  await page
    .getByRole("button")
    .filter({ has: page.getByRole("heading", { name: "DC-DC", exact: true }) })
    .click();
  await page
    .getByRole("button")
    .filter({
      has: page.getByRole("heading", {
        name: "Buck Diode Rectified Unidirectional",
        exact: true,
      }),
    })
    .click();
}
test("submit, poll, render real Buck fixture, navigate tabs and download", async ({
  page,
}, info) => {
  await setup(page);
  let queries = 0;
  let submitted: unknown;
  await page.route("**/api/v1/design-jobs", async (route) => {
    submitted = route.request().postDataJSON();
    await route.fulfill({ status: 202, json: job() });
  });
  await page.route(`**${path}`, (route) =>
    route.fulfill({ json: job(++queries > 1 ? "succeeded" : "running") }),
  );
  await openBuck(page);
  await expect(
    page.getByRole("spinbutton", { name: "Vin min V", exact: true }),
  ).toHaveValue("36");
  await page
    .getByRole("button", { name: "Run Design · 运行设计", exact: true })
    .click();
  await expect(page.getByRole("status")).toHaveText("已完成");
  expect(submitted).toMatchObject({
    request: { vin_min: 36, vin_max: 60, vout: 12, fs_khz: 100 },
  });
  await expect(
    page.getByRole("cell", { name: "candidate.inductance", exact: true }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("cell", { name: "candidate.output_current", exact: true })
      .locator(".."),
  ).toContainText(String(result.summary.candidate.output_current.value));
  await page.screenshot({
    path: info.outputPath("buck-results.png"),
    fullPage: true,
  });
  await page.getByRole("tab", { name: "Waveforms", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "此阶段尚未提供数据" }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Files", exact: true }).click();
  await expect(page.getByText(`SHA-256: ${file.sha256}`)).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "下载", exact: true }).click();
  const downloaded = await download;
  expect(downloaded.suggestedFilename()).toBe("result.json");
  expect(
    JSON.parse(await readFile((await downloaded.path())!, "utf8")),
  ).toEqual(result);
  await page.reload();
  await expect(page.getByRole("status")).toHaveText("已完成");
});

test("unified task shows blocked reason without plotting stale efficiency", async ({ page }) => {
  await setup(page);
  await page.addInitScript(({ id }) => localStorage.setItem("pe-claw-web-v1", JSON.stringify({ jobId: id })), { id });
  await page.route(`**${path}`, route => route.fulfill({ json: job("succeeded") }));
  await page.route(`**${path}/result`, route => route.fulfill({ json: {
    ...result, summary: { ...result.summary, efficiency_sweep: {
      available: true, status: "blocked", blocked_reason: "缺少已选磁件",
      points: [{ load_ratio: 0.1, efficiency: 0.8 }, { load_ratio: 1, efficiency: 0.9 }],
    } },
  } }));
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("已完成");
  await page.getByRole("tab", { name: "Efficiency", exact: true }).click();
  await expect(page.getByRole("heading", { name: "此阶段被阻塞" })).toBeVisible();
  await expect(page.getByText("缺少已选磁件")).toBeVisible();
  await expect(page.getByRole("img", { name: "效率与负载曲线" })).toHaveCount(0);
});

test("waveform and efficiency files belong to unified task and fit mobile", async ({ page }, info) => {
  await setup(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(({ id }) => localStorage.setItem("pe-claw-web-v1", JSON.stringify({ jobId: id })), { id });
  await page.route(`**${path}`, route => route.fulfill({ json: job("succeeded") }));
  await page.route(`**${path}/result`, route => route.fulfill({ json: {
    ...result, summary: { ...result.summary, waveform: { available: true, samples: { time_s: [0, 1], inductor_current_a: [1, 2] } } },
  } }));
  const wave = { ...file, id: "waveform-png", name: "waveform.png", stage: "waveform", media_type: "image/png", download_url: `${path}/artifacts/waveform-png` };
  await page.route(`**${path}/artifacts`, route => route.fulfill({ json: [file, wave] }));
  await page.route(`**${path}/artifacts/waveform-png`, route => route.fulfill({ contentType: "image/png", body: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aRZkAAAAASUVORK5CYII=", "base64") }));
  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("已完成");
  await page.getByRole("tab", { name: "Waveforms", exact: true }).click();
  await expect(page.getByRole("img", { name: "Waveforms · 当前任务计算曲线" })).toHaveAttribute("src", /waveform-png$/);
  await expect(page.getByText("当前报告提供波形统计值，未包含时域采样序列。")).toHaveCount(0);
  await page.getByRole("tab", { name: "Files", exact: true }).click();
  await expect(page.getByText("waveform.png", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath("files-mobile.png"), fullPage: true });
});
test("invalid voltage range stays local and does not submit", async ({
  page,
}) => {
  await setup(page);
  let submissions = 0;
  await page.route("**/api/v1/design-jobs", (route) => {
    submissions++;
    return route.fulfill({ json: job() });
  });
  await openBuck(page);
  await page
    .getByRole("spinbutton", { name: "Vin min V", exact: true })
    .fill("80");
  await page
    .getByRole("button", { name: "Run Design · 运行设计", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText(
    "Vin max 必须大于或等于 Vin min",
  );
  expect(submissions).toBe(0);
});
test("design failure is visible and can be resubmitted", async ({ page }) => {
  await setup(page);
  await page.route("**/api/v1/design-jobs", (route) =>
    route.fulfill({ status: 202, json: job() }),
  );
  await page.route(`**${path}`, (route) =>
    route.fulfill({
      json: {
        ...job("failed"),
        error: { code: "DESIGN_FAILED", message: "Design execution failed" },
      },
    }),
  );
  await openBuck(page);
  await page
    .getByRole("button", { name: "Run Design · 运行设计", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText(
    "Design execution failed",
  );
  await expect(
    page.getByRole("button", { name: "重新运行设计", exact: true }),
  ).toBeEnabled();
});
test("lost status connection can be retried without duplicate jobs", async ({
  page,
}) => {
  await setup(page);
  let online = false;
  await page.addInitScript(
    ({ id }) =>
      localStorage.setItem("pe-claw-web-v1", JSON.stringify({ jobId: id })),
    { id },
  );
  await page.route(`**${path}`, (route) =>
    online ? route.fulfill({ json: job("succeeded") }) : route.abort(),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("无法连接设计服务");
  online = true;
  await page.getByRole("button", { name: "重试查询", exact: true }).click();
  await expect(page.getByRole("status")).toHaveText("已完成");
});
test("catalog connection error is recoverable", async ({ page }) => {
  await page.route("**/api/v1/topologies", (route) => route.abort());
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "设计服务暂不可用" }),
  ).toBeVisible();
  await page.unroute("**/api/v1/topologies");
  await setup(page);
  await page.getByRole("button", { name: "重新连接" }).click();
  await expect(
    page.getByRole("heading", { name: "选择转换器分类" }),
  ).toBeVisible();
});
test("queue errors preserve inputs and keep submit available", async ({
  page,
}) => {
  await setup(page);
  await page.route("**/api/v1/design-jobs", (route) =>
    route.fulfill({
      status: 503,
      json: { detail: "Design queue is unavailable" },
    }),
  );
  await openBuck(page);
  await page
    .getByRole("spinbutton", { name: "Pout W", exact: true })
    .fill("200");
  await page
    .getByRole("button", { name: "Run Design · 运行设计", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText(
    "Design queue is unavailable",
  );
  await expect(
    page.getByRole("spinbutton", { name: "Pout W", exact: true }),
  ).toHaveValue("200");
});
test("mobile layout, draft persistence and unavailable topology", async ({
  page,
}, info) => {
  await setup(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await openBuck(page);
  await page
    .getByRole("spinbutton", { name: "Pout W", exact: true })
    .fill("240");
  await page.getByRole("button", { name: "Topologies", exact: true }).click();
  await expect(
    page
      .getByRole("button")
      .filter({
        has: page.getByRole("heading", {
          name: "Boost Diode Rectified Unidirectional",
          exact: true,
        }),
      }),
  ).toBeDisabled();
  await page
    .getByRole("button")
    .filter({
      has: page.getByRole("heading", {
        name: "Buck Diode Rectified Unidirectional",
        exact: true,
      }),
    })
    .click();
  await expect(
    page.getByRole("spinbutton", { name: "Pout W", exact: true }),
  ).toHaveValue("240");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: info.outputPath("buck-mobile.png"),
    fullPage: true,
  });
});

test("pending task survives reload without resubmitting", async ({ page }) => {
  await setup(page);
  let submissions = 0;
  await page.route("**/api/v1/design-jobs", (route) => {
    submissions++;
    return route.fulfill({ status: 202, json: job() });
  });
  await page.route(`**${path}`, (route) =>
    route.fulfill({ json: job("running") }),
  );
  await openBuck(page);
  await page
    .getByRole("button", { name: "Run Design · 运行设计", exact: true })
    .click();
  await expect(page.getByRole("status")).toHaveText("计算中");
  await page.reload();
  await expect(page.getByRole("status")).toHaveText("计算中");
  await expect(
    page.getByRole("button", { name: "设计运行中…", exact: true }),
  ).toBeDisabled();
  expect(submissions).toBe(1);
});

test("expired or missing result does not display stale numbers", async ({
  page,
}) => {
  await setup(page);
  await page.addInitScript(
    ({ id }) =>
      localStorage.setItem("pe-claw-web-v1", JSON.stringify({ jobId: id })),
    { id },
  );
  await page.route(`**${path}`, (route) =>
    route.fulfill({ status: 404, json: { detail: "Job not found" } }),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("任务或结果不存在");
  await expect(
    page.getByRole("cell", { name: "candidate.inductance", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Run Design · 运行设计", exact: true }),
  ).toBeEnabled();
});
