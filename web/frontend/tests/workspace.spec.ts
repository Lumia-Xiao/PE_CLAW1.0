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
async function authenticate(page: Page) {
  await page.addInitScript(() => sessionStorage.setItem("pe-claw-session-v1", "test-session-token"));
  await page.route("**/api/v1/auth/session", (route) =>
    route.fulfill({ json: { schema_version: "1.0", expires_at: "2026-12-01T00:00:00Z", user: { user_id: "test-user", username: "student", role: "user" } } }),
  );
}
async function setup(page: Page) {
  await authenticate(page);
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
async function review(page: Page) {
  await page
    .getByRole("button", { name: "检查并确认设计", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "确认完整设计", exact: true }),
  ).toBeVisible();
}
async function reviewAndConfirm(page: Page) {
  await review(page);
  await page
    .getByRole("button", { name: "确认并运行完整设计", exact: true })
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
  await expect(page.getByRole("combobox", { name: "Main switch category" }))
    .toHaveValue("Any active switch");
  await page.getByRole("combobox", { name: "Main switch category" })
    .selectOption("Discrete SiC MOSFET");
  await page.getByRole("combobox", { name: "Rectifier diode category" })
    .selectOption("Discrete SiC SBD");
  await page.getByRole("combobox", { name: "Semiconductor manufacturer" })
    .selectOption("Wolfspeed");
  await page.getByRole("spinbutton", { name: "Ambient temperature °C" }).fill("40");
  await page.getByRole("spinbutton", { name: "Target junction temperature °C" }).fill("125");
  await review(page);
  await expect(page.getByText("36 V", { exact: true })).toBeVisible();
  await expect(page.getByText("48 V", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("list", { name: "完整设计阶段" }).getByRole("listitem"),
  ).toHaveCount(11);
  expect(submitted).toBeUndefined();
  await page
    .getByRole("button", { name: "确认并运行完整设计", exact: true })
    .click();
  await expect(page.getByRole("status")).toHaveText("已完成");
  expect(submitted).toMatchObject({
    request: {
      topology: "buck_diode_rectified_unidirectional",
      raw_input: {
        vin_min: 36,
        vin_max: 60,
        vout: 12,
        fs_khz: 100,
        main_switch_category: "Discrete SiC MOSFET",
        rectifier_diode_category: "Discrete SiC SBD",
        semiconductor_manufacturer: "Wolfspeed",
        ambient_temp_c: 40,
        target_junction_temp_c: 125,
      },
    },
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
  await page.getByRole("button", { name: "下载", exact: true }).click();
  const downloaded = await download;
  expect(downloaded.suggestedFilename()).toBe("result.json");
  expect(
    JSON.parse(await readFile((await downloaded.path())!, "utf8")),
  ).toEqual(result);
  await page.reload();
  await expect(page.getByRole("status")).toHaveText("已完成");
});

test("renders and submits a non-Buck topology with numeric, text and choice fields", async ({ page }) => {
  await authenticate(page);
  const inverterId = "single_phase_full_bridge_inverter";
  const multiCatalog = {
    ...catalog,
    topologies: catalog.topologies.map((entry) => entry.id === inverterId ? {
      ...entry,
      web_enabled: true,
      fields: [
        { key: "conduction_mode", label: "Conduction mode", gui_label: "Conduction mode", unit: "", default: "CCM", input_type: "select", required: true, choices: ["CCM", "TCM"], exclusive_minimum: null },
        { key: "vdc_nom", label: "DC bus nominal", gui_label: "DC bus nominal [V]", unit: "V", default: "400", input_type: "number", required: true, choices: [], exclusive_minimum: null },
        { key: "note", label: "Design note", gui_label: "Design note", unit: "", default: "auto", input_type: "text", required: true, choices: [], exclusive_minimum: null },
      ],
      operating_point: {
        defaults: { vin_v: 400, load_ratio: 1, power_factor: 1 },
        fields: [
          { key: "load_ratio", label: "Load ratio", unit: "p.u.", minimum: 0 },
          { key: "power_factor", label: "Power factor", unit: "", minimum: -1, maximum: 1 },
        ],
      },
    } : entry),
  };
  await page.route("**/api/v1/topologies", route => route.fulfill({ json: multiCatalog }));
  let submitted: unknown;
  await page.route("**/api/v1/design-jobs", async route => {
    submitted = route.request().postDataJSON();
    await route.fulfill({ status: 202, json: { ...job("queued"), topology: inverterId } });
  });
  await page.route(`**${path}`, route => route.fulfill({ json: { ...job("succeeded"), topology: inverterId } }));
  await page.route(`**${path}/result`, route => route.fulfill({ json: { ...result, topology: inverterId } }));
  await page.route(`**${path}/artifacts`, route => route.fulfill({ json: [] }));

  await page.goto("/");
  await page.getByRole("button").filter({ has: page.getByRole("heading", { name: "DC-AC", exact: true }) }).click();
  await page.getByRole("button").filter({ has: page.getByRole("heading", { name: "Single-Phase Full-Bridge Inverter", exact: true }) }).click();
  await page.getByLabel("Conduction mode").selectOption("TCM");
  await page.getByRole("spinbutton", { name: "DC bus nominal V", exact: true }).fill("420");
  await page.getByLabel("Design note").fill("browser-value");
  await reviewAndConfirm(page);
  await expect.poll(() => submitted).toEqual({
    request: { topology: inverterId, raw_input: { conduction_mode: "TCM", vdc_nom: 420, note: "browser-value" } },
    execution_profile: "complete",
  });
  await expect(page.getByRole("spinbutton", { name: "功率因数", exact: true })).toHaveValue("1");
  await expect(page.getByRole("spinbutton", { name: "运行点 Vin", exact: true })).toHaveCount(0);
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

test("refreshes an operating point through the fixed-hardware waveform action", async ({ page }) => {
  await setup(page);
  await page.addInitScript(({ id }) => localStorage.setItem("pe-claw-web-v1", JSON.stringify({ jobId: id })), { id });
  await page.route(`**${path}`, route => route.fulfill({ json: job("succeeded") }));
  const actionId = "fixed-hardware-action";
  const actionPath = `${path}/actions/${actionId}`;
  let submitted: unknown;
  await page.route(`**${path}/actions/waveforms`, async route => {
    submitted = route.request().postDataJSON();
    await route.fulfill({ status: 202, json: {
      action_id: actionId, job_id: id, action: "waveforms", status: "queued",
      progress: 0, stage: "queued", created_at: "2026-09-14T10:05:00Z",
    } });
  });
  await page.route(`**${actionPath}/result`, route => route.fulfill({ json: {
    schema_version: "1.0", action_id: actionId, job_id: id, action: "waveforms",
    summary: {
      ...result.summary,
      waveform: {
        available: true,
        input_voltage: { value: 42, unit: "V", source: "operating_point.input" },
        load_ratio: { value: 0.5, unit: "p.u.", source: "operating_point.input" },
      },
    },
    warnings: [], artifacts: [],
  } }));
  await page.route(`**${actionPath}`, route => route.fulfill({ json: {
    action_id: actionId, job_id: id, action: "waveforms", status: "succeeded",
    progress: 100, stage: "finalize", created_at: "2026-09-14T10:05:00Z",
    result_url: `${actionPath}/result`,
  } }));

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "固定硬件工作点刷新" })).toBeVisible();
  await page.getByRole("spinbutton", { name: "运行点 Vin" }).fill("42");
  await page.getByRole("spinbutton", { name: "负载比例" }).fill("0.5");
  await page.getByRole("button", { name: "刷新固定硬件工作点" }).click();

  await expect(page.getByText("当前显示：42 V / 0.5 p.u.（固定硬件）", { exact: true })).toBeVisible();
  expect(submitted).toEqual({
    job_id: id,
    action: "waveforms",
    operating_point: { vin_v: 42, load_ratio: 0.5 },
  });
  await page.getByRole("tab", { name: "Waveforms", exact: true }).click();
  await expect(page.getByRole("cell", { name: "input_voltage", exact: true }).locator("..")).toContainText("42");
});

test("runs an independent fixed-hardware efficiency action", async ({ page }) => {
  await setup(page);
  await page.addInitScript(({ id }) => localStorage.setItem("pe-claw-web-v1", JSON.stringify({ jobId: id })), { id });
  await page.route(`**${path}`, route => route.fulfill({ json: job("succeeded") }));
  const actionId = "efficiency-action";
  const actionPath = `${path}/actions/${actionId}`;
  let submitted: unknown;
  await page.route(`**${path}/actions/efficiency-sweep`, async route => {
    submitted = route.request().postDataJSON();
    await route.fulfill({ status: 202, json: {
      action_id: actionId, job_id: id, action: "efficiency_sweep", status: "queued",
      progress: 0, stage: "queued", created_at: "2026-09-14T10:05:00Z",
    } });
  });
  await page.route(`**${actionPath}/result`, route => route.fulfill({ json: {
    schema_version: "1.0", action_id: actionId, job_id: id, action: "efficiency_sweep",
    summary: {
      ...result.summary,
      efficiency_sweep: {
        available: true, status: "available",
        points: [{ load_ratio: 0.5, efficiency: 0.91 }, { load_ratio: 1, efficiency: 0.94 }],
      },
    },
    warnings: [], artifacts: [],
  } }));
  await page.route(`**${actionPath}`, route => route.fulfill({ json: {
    action_id: actionId, job_id: id, action: "efficiency_sweep", status: "succeeded",
    progress: 100, stage: "finalize", created_at: "2026-09-14T10:05:00Z",
    result_url: `${actionPath}/result`,
  } }));

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "独立阶段操作" })).toBeVisible();
  await expect(page.getByRole("button", { name: "重新运行电容设计" })).toBeVisible();
  await expect(page.getByRole("button", { name: "重新运行磁件设计" })).toBeVisible();
  await page.getByRole("button", { name: "刷新固定硬件效率扫描" }).click();

  await expect(page.getByText("efficiency_sweep 已完成，结果视图已更新。", { exact: true })).toBeVisible();
  expect(submitted).toEqual({ job_id: id, action: "efficiency_sweep" });
  await page.getByRole("tab", { name: "Efficiency", exact: true }).click();
  await expect(page.getByRole("img", { name: "效率与负载曲线" })).toBeVisible();
});

test("renders Web equivalents for specialized Tkinter result pages", async ({ page }) => {
  await setup(page);
  await page.addInitScript(({ id }) => localStorage.setItem("pe-claw-web-v1", JSON.stringify({ jobId: id })), { id });
  await page.route(`**${path}`, route => route.fulfill({ json: job("succeeded") }));
  await page.route(`**${path}/result`, route => route.fulfill({ json: {
    ...result,
    summary: {
      ...result.summary,
      waveform: { available: true, samples: {
        time_s: [0, 0.000005, 0.00001], inductor_current_a: [9, 11, 9],
        switch_node_voltage_v: [0, 48, 0], switch_current_a: [0, 11, 0], gate_s1: [0, 1, 0],
      } },
      capacitor: { available: true, input: { pareto: [
        { part_number: "CAP-A", volume_cm3: 10, loss_w: 0.9, recommended: false },
        { part_number: "CAP-B", volume_cm3: 13, loss_w: 0.5, recommended: true },
      ] }, output: { pareto: [
        { part_number: "CAP-C", volume_cm3: 8, loss_w: 0.8, recommended: false },
        { part_number: "CAP-D", volume_cm3: 11, loss_w: 0.4, recommended: true },
      ] } },
      magnetic: { available: true, candidate_comparison: [
        { design_id: "L-A", volume_m3: 0.000002, loss_w: 2.1 },
        { design_id: "L-B", volume_m3: 0.000003, loss_w: 1.2 },
      ], representatives: [{ design_id: "L-B", turns: 12 }] },
      geometry: { available: true, targets: [{ role: "recommended", label: "Recommended", layout: {
        core_name: "E42", turns: 12, outer_width_mm: 42, outer_height_mm: 35,
        window_width_mm: 20, window_height_mm: 12, overall_width_mm: 46,
        overall_height_mm: 39, overall_depth_mm: 22,
      } }] },
      efficiency_sweep: { available: true, status: "available", points: [
        { load_ratio: 0.5, efficiency: 0.91, total_loss: 8 },
        { load_ratio: 1, efficiency: 0.94, total_loss: 12 },
      ], pf_points: [
        { power_factor: 0.8, efficiency: 0.9 }, { power_factor: 1, efficiency: 0.94 },
      ] },
    },
  } }));

  await page.goto("/");
  await page.getByRole("tab", { name: "Waveforms", exact: true }).click();
  await expect(page.getByRole("img", { name: "多通道工作点波形" })).toBeVisible();
  await page.getByRole("tab", { name: "Capacitor PF", exact: true }).click();
  await expect(page.getByRole("img", { name: "输入电容 Pareto · 体积/损耗" })).toBeVisible();
  await expect(page.getByRole("img", { name: "输出电容 Pareto · 体积/损耗" })).toBeVisible();
  await page.getByRole("tab", { name: "Inductor PF", exact: true }).click();
  await expect(page.getByRole("img", { name: "磁件候选比较 · 体积/损耗" })).toBeVisible();
  await page.getByRole("tab", { name: "Inductor", exact: true }).click();
  await expect(page.getByRole("img", { name: "磁件 2D/3D 几何比较" })).toBeVisible();
  await page.getByRole("tab", { name: "Efficiency", exact: true }).click();
  await expect(page.getByRole("img", { name: "损耗分解 · 固定硬件负载扫描" })).toBeVisible();
  await expect(page.getByRole("img", { name: "功率因数扫描 · 效率" })).toBeVisible();
});

test("failed complete job shows saved results and resumes same job", async ({ page }) => {
  await setup(page);
  await page.addInitScript(({ id }) => localStorage.setItem("pe-claw-web-v1", JSON.stringify({ jobId: id })), { id });
  let resumed=false;
  await page.route(`**${path}`, route => route.fulfill({ json: resumed ? { ...job("running"), attempt:2 } : {
    ...job("failed"), stage:"magnetics", retryable:true, result_url:`${path}/result`, attempt:1,
    stages:{topology:"succeeded", devices:"succeeded", magnetics:"failed"},
    stage_details:{
      topology:{schema_version:"1.0",status:"succeeded",progress:100,warnings:[]},
      devices:{schema_version:"1.0",status:"succeeded",progress:100,warnings:[]},
      magnetics:{schema_version:"1.0",status:"failed",progress:100,warnings:["磁件候选不足"],error:{code:"DESIGN_FAILED",message:"磁件阶段失败"}},
    },
    error:{code:"DESIGN_FAILED",message:"Design failed at magnetics; completed stages were saved"},
  } }));
  await page.route(`**${path}/retry?restart=false`, route => {
    resumed=true;
    return route.fulfill({ status:202, json:{...job("queued"),attempt:1} });
  });
  await page.goto("/");
  await expect(page.getByRole("cell",{name:"candidate.inductance",exact:true})).toBeVisible();
  await page.getByText("阶段状态 · 第 1 次执行", { exact: true }).click();
  await expect(page.getByText("磁件候选不足", { exact: true })).toBeVisible();
  await expect(page.getByText("磁件阶段失败", { exact: true })).toBeVisible();
  await page.getByRole("button",{name:"从已保存阶段恢复",exact:true}).click();
  await expect(page.getByRole("status")).toHaveText("计算中");
  await expect(page.getByRole("cell",{name:"candidate.inductance",exact:true})).toHaveCount(0);
});

test("cancels an active job and stops presenting it as running", async ({ page }) => {
  await setup(page);
  await page.addInitScript(({ id }) => localStorage.setItem("pe-claw-web-v1", JSON.stringify({ jobId: id })), { id });
  let cancelled = false;
  await page.route(`**${path}`, route => route.fulfill({ json: cancelled
    ? { ...job("cancelled"), stage: "cancelled", finished_at: "2026-09-14T10:01:00Z" }
    : job("running") }));
  await page.route(`**${path}/cancel`, route => {
    cancelled = true;
    return route.fulfill({ json: { ...job("cancelled"), stage: "cancelled", finished_at: "2026-09-14T10:01:00Z" } });
  });

  await page.goto("/");
  await expect(page.getByRole("status")).toHaveText("计算中");
  await page.getByRole("button", { name: "取消任务", exact: true }).click();
  await expect(page.getByRole("status")).toHaveText("已取消");
  await expect(page.getByText("此任务已结束，可以提交新的设计。", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "取消任务", exact: true })).toHaveCount(0);
});

test("lists, filters and opens only the signed-in user's history", async ({ page }) => {
  await setup(page);
  const historyJob = { ...job("succeeded"), progress: 100 };
  let requested = "";
  await page.route("**/api/v1/design-jobs?*", route => {
    requested = route.request().url();
    return route.fulfill({ json: [historyJob] });
  });
  await page.route(`**${path}`, route => route.fulfill({ json: historyJob }));

  await page.goto("/");
  await page.getByRole("button", { name: "我的任务", exact: true }).click();
  await expect(page.getByRole("heading", { name: "我的历史任务" })).toBeVisible();
  await expect(page.getByRole("cell", { name: id, exact: true })).toBeVisible();
  await page.getByLabel("任务状态").selectOption("succeeded");
  await expect.poll(() => requested).toContain("status=succeeded");
  await page.getByLabel("任务编号").fill(id.slice(0, 8));
  await page.getByRole("button", { name: "搜索", exact: true }).click();
  await expect.poll(() => requested).toContain(`query=${id.slice(0, 8)}`);
  await page.getByRole("button", { name: "查看", exact: true }).click();
  await expect(page.getByRole("status")).toHaveText("已完成");
});

test("idempotent submission reloads results when the server reuses the job ID", async ({ page }) => {
  await setup(page);
  await page.route("**/api/v1/design-jobs", route => route.fulfill({status:202,json:job("succeeded")}));
  await page.route(`**${path}`, route => route.fulfill({json:job("succeeded")}));
  await openBuck(page);
  for (let i=0;i<2;i++) {
    await reviewAndConfirm(page);
    await expect(page.getByRole("cell",{name:"candidate.inductance",exact:true})).toBeVisible();
  }
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
  await expect(page.getByRole("img", { name: "Waveforms · 当前任务计算曲线" })).toHaveAttribute("src", /^blob:/);
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
    .getByRole("button", { name: "检查并确认设计", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText(
    "Vin max 必须大于或等于 Vin min",
  );
  expect(submissions).toBe(0);
});
test("Buck output voltage relationship matches the API contract", async ({ page }) => {
  await setup(page);
  let submissions = 0;
  await page.route("**/api/v1/design-jobs", (route) => {
    submissions++;
    return route.fulfill({ json: job() });
  });
  await openBuck(page);
  await page.getByRole("spinbutton", { name: "Vout V", exact: true }).fill("36");
  await page.getByRole("button", { name: "检查并确认设计", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Vout 小于 Vin min");
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
  await reviewAndConfirm(page);
  await expect(page.getByRole("alert")).toContainText(
    "Design execution failed",
  );
  await expect(
    page.getByRole("button", { name: "检查并确认设计", exact: true }),
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
  await authenticate(page);
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

test("login stores only the bearer session and logout clears prior user workspace", async ({ page }) => {
  await page.addInitScript(({ id }) =>
    localStorage.setItem("pe-claw-web-v1", JSON.stringify({ jobId: id, draft: { pout: "999" } })), { id });
  await page.route("**/api/v1/topologies", (route) => route.fulfill({ json: catalog }));
  await page.route("**/api/v1/auth/login", async (route) => {
    expect(route.request().postDataJSON()).toEqual({ username: "student", password: "valid-password" });
    await route.fulfill({ json: { schema_version: "1.0", access_token: "fresh-token", token_type: "bearer", expires_at: "2026-12-01T00:00:00Z", user: { user_id: "test-user", username: "student", role: "user" } } });
  });
  await page.route("**/api/v1/auth/logout", async (route) => {
    expect(route.request().headers().authorization).toBe("Bearer fresh-token");
    await route.fulfill({ status: 204 });
  });
  await page.goto("/");
  await page.getByLabel("用户名").fill("student");
  await page.getByLabel("密码").fill("valid-password");
  await page.getByRole("button", { name: "登录", exact: true }).click();
  await expect(page.getByRole("banner")).toContainText("student");
  expect(await page.evaluate(() => sessionStorage.getItem("pe-claw-session-v1"))).toBe("fresh-token");
  expect(await page.evaluate(() => localStorage.getItem("pe-claw-web-v1"))).not.toContain("999");
  await page.getByRole("button", { name: "退出", exact: true }).click();
  await expect(page.getByRole("heading", { name: "登录设计工作区" })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem("pe-claw-session-v1"))).toBeNull();
});
test("registers a user and changes the password with session revocation", async ({ page }) => {
  await page.route("**/api/v1/topologies", route => route.fulfill({ json: catalog }));
  await page.route("**/api/v1/auth/register", async route => {
    expect(route.request().postDataJSON()).toEqual({ username: "new-student", password: "valid-password-123" });
    await route.fulfill({ status: 201, json: { schema_version: "1.0", access_token: "registered-token", token_type: "bearer", expires_at: "2026-12-01T00:00:00Z", user: { user_id: "new-user", username: "new-student", role: "user" } } });
  });
  await page.route("**/api/v1/auth/change-password", async route => {
    expect(route.request().headers().authorization).toBe("Bearer registered-token");
    expect(route.request().postDataJSON()).toEqual({ current_password: "valid-password-123", new_password: "updated-password-456" });
    await route.fulfill({ status: 204 });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "创建新账户", exact: true }).click();
  await page.getByLabel("用户名").fill("new-student");
  await page.getByLabel("密码", { exact: true }).fill("valid-password-123");
  await page.getByLabel("确认密码", { exact: true }).fill("valid-password-123");
  await page.getByRole("button", { name: "注册并登录", exact: true }).click();
  await expect(page.getByRole("banner")).toContainText("new-student");
  await page.getByRole("button", { name: "账户", exact: true }).click();
  await page.getByLabel("当前密码").fill("valid-password-123");
  await page.getByLabel("新密码", { exact: true }).fill("updated-password-456");
  await page.getByLabel("确认新密码", { exact: true }).fill("updated-password-456");
  await page.getByRole("button", { name: "修改密码", exact: true }).click();
  await expect(page.getByRole("heading", { name: "登录设计工作区" })).toBeVisible();
  expect(await page.evaluate(() => sessionStorage.getItem("pe-claw-session-v1"))).toBeNull();
});
test("admin manages users and reviews audit events", async ({ page }) => {
  const admin = { user_id: "admin-user", username: "root-admin", role: "admin" };
  const managed = { user_id: "managed-user", username: "student", role: "user", active: true, created_at: "2026-09-01T00:00:00Z" };
  await page.addInitScript(() => sessionStorage.setItem("pe-claw-session-v1", "admin-token"));
  await page.route("**/api/v1/auth/session", route => route.fulfill({ json: { schema_version: "1.0", expires_at: "2026-12-01T00:00:00Z", user: admin } }));
  await page.route("**/api/v1/topologies", route => route.fulfill({ json: catalog }));
  await page.route("**/api/v1/admin/users", route => route.request().method() === "GET"
    ? route.fulfill({ json: [{ ...admin, active: true, created_at: "2026-08-01T00:00:00Z" }, managed] })
    : route.fulfill({ status: 201, json: { ...managed, user_id: "new-user", username: "second-student" } }));
  await page.route("**/api/v1/admin/audit-events?limit=100", route => route.fulfill({ json: [{
    event_id: "audit-1", occurred_at: "2026-09-01T01:00:00Z", actor_user_id: admin.user_id,
    action: "admin.user.create", resource_type: "user", resource_id: managed.user_id,
    outcome: "succeeded", details: {},
  }] }));
  let updateBody: unknown;
  await page.route(`**/api/v1/admin/users/${managed.user_id}/update`, async route => {
    updateBody = route.request().postDataJSON();
    await route.fulfill({ json: { ...managed, active: false } });
  });
  let resetBody: unknown;
  await page.route(`**/api/v1/admin/users/${managed.user_id}/reset-password`, async route => {
    resetBody = route.request().postDataJSON();
    await route.fulfill({ status: 204 });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "管理", exact: true }).click();
  await expect(page.getByRole("heading", { name: "用户与审计管理" })).toBeVisible();
  await expect(page.getByText("admin.user.create", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "student 禁用", exact: true }).click();
  await expect.poll(() => updateBody).toEqual({ active: false });
  await page.getByLabel("student 新密码").fill("replacement-password");
  await page.getByRole("button", { name: "student 重置密码", exact: true }).click();
  await expect.poll(() => resetBody).toEqual({ new_password: "replacement-password" });
});
test("queue errors preserve inputs and keep submit available", async ({
  page,
}) => {
  await setup(page);
  await page.route("**/api/v1/design-jobs", (route) =>
    route.fulfill({
      status: 503,
      json: { code: "QUEUE_UNAVAILABLE", message: "设计队列暂不可用，请稍后重试。" },
    }),
  );
  await openBuck(page);
  await page
    .getByRole("spinbutton", { name: "Pout W", exact: true })
    .fill("200");
  await reviewAndConfirm(page);
  await expect(page.getByRole("alert")).toContainText(
    "设计队列暂不可用",
  );
  await page.getByRole("button", { name: "返回修改", exact: true }).click();
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
  await review(page);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: info.outputPath("buck-confirmation-mobile.png"),
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
  await reviewAndConfirm(page);
  await expect(page.getByRole("status")).toHaveText("计算中");
  await expect(page).toHaveURL(new RegExp(`\\?job=${id}$`));
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await expect(page.getByRole("status")).toHaveText("计算中");
  await expect(
    page.getByRole("button", { name: "设计运行中…", exact: true }),
  ).toBeDisabled();
  expect(submissions).toBe(1);
  const saved = await page.evaluate(() => JSON.parse(localStorage.getItem("pe-claw-web-v1") || "{}"));
  expect(Object.keys(saved).sort()).toEqual(["draft", "jobId"]);
  expect(Object.values(saved.draft).every((value) => typeof value === "string")).toBe(true);
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
    page.getByRole("button", { name: "检查并确认设计", exact: true }),
  ).toBeEnabled();
});

test("confirmation submit lock prevents duplicate clicks", async ({ page }) => {
  await setup(page);
  let submissions = 0;
  await page.route("**/api/v1/design-jobs", async (route) => {
    submissions++;
    await new Promise((resolve) => setTimeout(resolve, 150));
    await route.fulfill({ status: 202, json: job() });
  });
  await page.route(`**${path}`, (route) => route.fulfill({ json: job("running") }));
  await openBuck(page);
  await review(page);
  await page
    .getByRole("button", { name: "确认并运行完整设计", exact: true })
    .dblclick();
  await expect(page.getByRole("status")).toHaveText("计算中");
  expect(submissions).toBe(1);
});
