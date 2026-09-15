import { useEffect, useState, type FormEvent } from "react";
import {
  ApiError,
  BUCK,
  jobPath,
  request,
  type Artifact,
  type Catalog,
  type Job,
  type Result,
  type Topology,
} from "./api";
import Results from "./Results";

const storageKey = "pe-claw-web-v1";
type Saved = { jobId?: string; draft?: Record<string, string> };
function restore(): Saved {
  try {
    return JSON.parse(localStorage.getItem(storageKey) || "{}") ?? {};
  } catch {
    return {};
  }
}
function save(data: Saved) {
  try {
    localStorage.setItem(storageKey, JSON.stringify(data));
  } catch {
    /* Storage may be disabled by browser policy. */
  }
}
const statusLabels: Record<string, string> = {
  queued: "排队中",
  running: "计算中",
  succeeded: "已完成",
  failed: "设计失败",
  cancelled: "已取消",
  expired: "结果已过期",
};
const errorText = (error: unknown) =>
  error instanceof Error ? error.message : "操作失败，请重试。";

export default function App() {
  const [initial] = useState(restore);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catalogError, setCatalogError] = useState("");
  const [catalogRetry, setCatalogRetry] = useState(0);
  const [page, setPage] = useState<"categories" | "topologies" | "workspace">(
    initial.jobId ? "workspace" : "categories",
  );
  const [category, setCategory] = useState(initial.jobId ? "dc_dc" : "");
  const [selected, setSelected] = useState(BUCK);
  const [draft, setDraft] = useState<Record<string, string>>(
    initial.draft || {},
  );
  const [jobId, setJobId] = useState(initial.jobId || "");
  const [job, setJob] = useState<Job | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [pollError, setPollError] = useState("");
  const [retry, setRetry] = useState(0);
  const [submitted, setSubmitted] = useState<Record<string, string> | null>(
    null,
  );
  const [recoverId, setRecoverId] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setCatalogError("");
    request<Catalog>("/api/v1/topologies", { signal: controller.signal })
      .then(setCatalog)
      .catch((e) => {
        if (!controller.signal.aborted) setCatalogError(errorText(e));
      });
    return () => controller.abort();
  }, [catalogRetry]);
  useEffect(() => {
    save({ jobId, draft });
  }, [jobId, draft]);
  useEffect(() => {
    if (!jobId) return;
    setResult(null);
    setArtifacts([]);
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async () => {
      try {
        const next = await request<Job>(jobPath(jobId), {
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setJob(next);
        setPollError("");
        if (next.status === "succeeded") {
          const [data, files] = await Promise.all([
            request<Result>(`${jobPath(jobId)}/result`, {
              signal: controller.signal,
            }),
            request<Artifact[]>(`${jobPath(jobId)}/artifacts`, {
              signal: controller.signal,
            }),
          ]);
          if (controller.signal.aborted) return;
          setResult(data);
          setArtifacts(files);
        } else if (next.status === "failed" && next.result_url) {
          const data = await request<Result>(`${jobPath(jobId)}/result`, { signal: controller.signal });
          if (!controller.signal.aborted) setResult(data);
        } else if (next.status === "queued" || next.status === "running") {
          timer = setTimeout(poll, 1800);
        }
      } catch (e) {
        if (!controller.signal.aborted)
          setPollError(
            e instanceof ApiError && e.status === 404
              ? "任务或结果不存在，可能已清理。请恢复其他任务或新建设计。"
              : errorText(e),
          );
      }
    };
    void poll();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [jobId, retry]);

  const topology = catalog?.topologies.find((t) => t.id === selected);
  const values = Object.fromEntries(
    (topology?.fields || []).map((f) => [f.key, draft[f.key] ?? f.default]),
  );
  const busy =
    submitting ||
    (!!jobId &&
      !pollError &&
      (!job || job.status === "queued" || job.status === "running"));
  function openTopology(t: Topology) {
    setSelected(t.id);
    setPage("workspace");
    setError("");
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!topology || busy) return;
    setError("");
    const numbers = Object.fromEntries(
      topology.fields.map((f) => [f.key, Number(values[f.key])]),
    );
    if (
      topology.fields.some(
        (f) =>
          !values[f.key]?.trim() ||
          !Number.isFinite(numbers[f.key]) ||
          (f.exclusive_minimum !== null &&
            numbers[f.key] <= f.exclusive_minimum),
      )
    ) {
      setError("请输入有效的正数，所有设计参数均为必填项。");
      return;
    }
    if (numbers.vin_max < numbers.vin_min) {
      setError("Vin max 必须大于或等于 Vin min。");
      return;
    }
    setSubmitting(true);
    try {
      const next = await request<Job>("/api/v1/design-jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request: { topology: selected, ...numbers }, execution_profile: "complete", operating_point: { vin_v: (numbers.vin_min + numbers.vin_max) / 2, load_ratio: 1 } }),
      });
      setResult(null);
      setArtifacts([]);
      setPollError("");
      setJob(next);
      setSubmitted({ ...values });
      setJobId(next.job_id);
      setRetry(v => v + 1); // An idempotent submission can return the current job ID.
    } catch (e) {
      setError(errorText(e));
    } finally {
      setSubmitting(false);
    }
  }
  const selectCategory = (id: string) => {
    setCategory(id);
    setPage("topologies");
  };
  async function resumeJob(restart = false) {
    if (submitting) return;
    setSubmitting(true);
    setError("");
    try {
      const next = await request<Job>(`${jobPath(jobId)}/retry?restart=${restart}`, { method: "POST" });
      setJob(next);
      setResult(null);
      setArtifacts([]);
      setRetry(v => v + 1);
    } catch (e) { setError(errorText(e)); }
    finally { setSubmitting(false); }
  }
  return (
    <>
      <header className="masthead">
        <div className="brand">
          <span className="logo">PE</span>
          <div>
            <strong>PE-Claw</strong>
            <small>POWER ELECTRONICS DESIGN</small>
          </div>
        </div>
        <div className="header-right">
          <span className="dot" />
          Converter workspace <span className="version">WEB · 0.1</span>
        </div>
      </header>
      <nav className="navigation" aria-label="工作区导航">
        <button onClick={() => setPage("categories")}>Categories</button>
        <span>/</span>
        <button disabled={!category} onClick={() => setPage("topologies")}>
          Topologies
        </button>
        <span>/</span>
        <span className="breadcrumb">
          {catalog?.categories.find((c) => c.id === category)?.name ||
            "选择转换器分类"}
          {page === "workspace" && ` → ${topology?.name || "Buck"}`}
        </span>
        {jobId && (
          <button
            className="return-task"
            onClick={() => {
              setPage("workspace");
              setCategory("dc_dc");
              setSelected(BUCK);
            }}
          >
            当前任务
          </button>
        )}
      </nav>
      <main>
        {catalogError ? (
          <div className="panel service-error" role="alert">
            <h2>设计服务暂不可用</h2>
            <p>{catalogError}</p>
            <button onClick={() => setCatalogRetry((v) => v + 1)}>
              重新连接
            </button>
          </div>
        ) : !catalog ? (
          <p role="status" className="loading">
            正在读取转换器与参数配置…
          </p>
        ) : page === "categories" ? (
          <>
            <div className="page-title">
              <span className="eyebrow">01 / CONVERTER CATEGORY</span>
              <h1>选择转换器分类</h1>
              <p>从输入与输出类型开始，进入你的设计工作区。</p>
            </div>
            <div className="category-grid">
              {catalog.categories.map((c) => (
                <button
                  key={c.id}
                  className="category-card"
                  onClick={() => selectCategory(c.id)}
                >
                  <span className="category-symbol">
                    {c.id.toUpperCase().replace("_", " → ")}
                  </span>
                  <h2>{c.name}</h2>
                  <p>{c.description}</p>
                  <span className="card-link">
                    查看拓扑 <span>↗</span>
                  </span>
                </button>
              ))}
            </div>
            <form
              className="recover panel"
              onSubmit={(e) => {
                e.preventDefault();
                if (recoverId.trim()) {
                  setJob(null);
                  setResult(null);
                  setArtifacts([]);
                  setPollError("");
                  setJobId(recoverId.trim());
                  setRetry((v) => v + 1);
                  setPage("workspace");
                  setCategory("dc_dc");
                }
              }}
            >
              <label htmlFor="recover">恢复设计任务</label>
              <input
                id="recover"
                value={recoverId}
                onChange={(e) => setRecoverId(e.target.value)}
                placeholder="输入任务编号"
                required
              />
              <button>恢复任务</button>
            </form>
          </>
        ) : page === "topologies" ? (
          <>
            <div className="page-title">
              <span className="eyebrow">02 / TOPOLOGY</span>
              <h1>{catalog.categories.find((c) => c.id === category)?.name}</h1>
              <p>选择拓扑。当前网页版已接入 Buck 二极管整流设计。</p>
            </div>
            <div className="topology-grid">
              {catalog.topologies
                .filter((t) => t.category_id === category)
                .map((t) => (
                  <button
                    className="topology-card"
                    disabled={!t.web_enabled}
                    key={t.id}
                    onClick={() => openTopology(t)}
                  >
                    <span className={`tag ${t.web_enabled ? "ready" : ""}`}>
                      {t.web_enabled ? "可开始设计" : "尚未接入 Web"}
                    </span>
                    <h2>{t.name}</h2>
                    <p>
                      {t.web_enabled
                        ? "电气参数 · 器件选择 · 结构化报告"
                        : "保留桌面版拓扑，等待后续接入。"}
                    </p>
                  </button>
                ))}
            </div>
            {!catalog.topologies.some((t) => t.category_id === category) && (
              <div className="panel empty">此分类暂无已注册拓扑。</div>
            )}
          </>
        ) : (
          <>
            <div className="workspace-title">
              <div>
                <span className="eyebrow">03 / DESIGN WORKSPACE</span>
                <h1>{topology?.name}</h1>
              </div>
              <span className="tag ready">DC-DC / Buck</span>
            </div>
            <div className="workspace">
              <aside>
                <form className="panel input-panel" onSubmit={submit}>
                  <div className="panel-head">
                    <div>
                      <span className="eyebrow">DESIGN INPUTS</span>
                      <h2>设计参数</h2>
                    </div>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => {
                        setDraft({});
                        setError("");
                      }}
                    >
                      重置
                    </button>
                  </div>
                  <fieldset disabled={busy}>
                    {topology?.fields.map((f) => (
                      <label className="field" key={f.key} htmlFor={f.key}>
                        <span>{f.label}</span>
                        <div className="input-unit">
                          <input
                            id={f.key}
                            type="number"
                            step="any"
                            required
                            value={values[f.key]}
                            onChange={(e) => {
                              setDraft((v) => ({
                                ...v,
                                [f.key]: e.target.value,
                              }));
                              setError("");
                            }}
                          />
                          <span>{f.unit}</span>
                        </div>
                      </label>
                    ))}
                  </fieldset>
                  {error && (
                    <div role="alert" className="error">
                      {error}
                    </div>
                  )}
                  <button
                    className="primary run"
                    disabled={busy || !topology}
                    type="submit"
                  >
                    {submitting
                      ? "正在提交…"
                      : busy
                        ? "设计运行中…"
                        : job?.status === "failed"
                          ? "重新运行设计"
                          : "Run Design · 运行设计"}
                  </button>
                  <p className="form-note">
                    参数提交后由本地后端计算。离开页面不会取消已提交的任务。
                  </p>
                </form>
                <section className="panel help"><h3>完整设计流程</h3><p>确认输入后将自动依次执行电容、磁件、运行点波形、损耗、热分析和效率扫描。</p></section>
              </aside>
              <div className="output-column">
                {jobId && (
                  <section
                    className={`panel job ${job?.status || ""}`}
                    aria-label="任务状态"
                  >
                    <div className="job-heading">
                      <strong role="status">
                        {job ? statusLabels[job.status] : "正在恢复任务…"}
                      </strong>
                      <span>
                        {job?.stage || "等待状态"} · {job?.progress ?? 0}%
                      </span>
                    </div>
                    <progress
                      aria-label="设计进度"
                      max="100"
                      value={job?.progress ?? 0}
                    />
                    <div className="job-meta">
                      <span>任务编号</span>
                      <code>{jobId}</code>
                    </div>
                    {job?.error && (
                      <div className="error" role="alert">
                        {job.error.message} <small>({job.error.code})</small>
                      </div>
                    )}
                    {job?.status === "failed" && job.retryable !== undefined && <>
                      <p>已完成阶段的结果保留在本任务中；恢复沿用原输入与已选硬件。</p>
                      <button disabled={submitting} onClick={() => void resumeJob(!job.retryable)}>
                        {job.retryable ? "从已保存阶段恢复" : "快照不可用，从头重新运行"}
                      </button>
                    </>}
                    {job?.stages && <details><summary>阶段状态 · 第 {job.attempt || 0} 次执行</summary>
                      <dl>{Object.entries(job.stages).map(([stage, status]) => <div key={stage}><dt>{stage}</dt><dd>{status}</dd></div>)}</dl>
                    </details>}
                    {(job?.status === "cancelled" ||
                      job?.status === "expired") && (
                      <p>此任务已结束，可以提交新的设计。</p>
                    )}
                    {pollError && (
                      <div className="error" role="alert">
                        {pollError}{" "}
                        <button
                          onClick={() => {
                            setPollError("");
                            setRetry((v) => v + 1);
                          }}
                        >
                          重试查询
                        </button>
                      </div>
                    )}
                    {submitted && (
                      <details>
                        <summary>查看本次提交参数</summary>
                        <dl>
                          {Object.entries(submitted).map(([k, v]) => (
                            <div key={k}>
                              <dt>{k}</dt>
                              <dd>{v}</dd>
                            </div>
                          ))}
                        </dl>
                      </details>
                    )}
                  </section>
                )}
                {result && result.warnings.length > 0 && (
                  <details className="warnings panel">
                    <summary>
                      设计提示与警告（{result.warnings.length}）
                    </summary>
                    <ul>
                      {result.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </details>
                )}
                <Results key={jobId} result={result?.job_id === jobId ? result : null} artifacts={result?.job_id === jobId ? artifacts : []} />
              </div>
            </div>
          </>
        )}
      </main>
      <footer>
        <span>PE-Claw / Engineering workspace</span>
        <span>数值与单位以当前任务报告为准</span>
      </footer>
    </>
  );
}
