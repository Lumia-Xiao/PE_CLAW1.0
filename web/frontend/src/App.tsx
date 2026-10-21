import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  ApiError,
  BUCK,
  authToken,
  clearAuthToken,
  jobPath,
  request,
  setAuthToken,
  type Artifact,
  type ActionResult,
  type AdminUser,
  type AuditEvent,
  type Catalog,
  type DesignAction,
  type Job,
  type Result,
  type Session,
  type SessionInfo,
  type StageState,
  type Topology,
  type User,
} from "./api";
import Results from "./Results";

const storageKey = "pe-claw-web-v1";
type Saved = { jobId?: string; draft?: Record<string, string> };
function restore(): Saved {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || "{}") ?? {};
    const jobId = new URLSearchParams(window.location.search).get("job");
    return jobId ? { ...saved, jobId } : saved;
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
const stageStatusLabels: Record<string, string> = {
  pending: "等待",
  running: "执行中",
  succeeded: "完成",
  failed: "失败",
  blocked: "已阻塞",
  unavailable: "不可用",
};
const errorText = (error: unknown) =>
  error instanceof Error ? error.message : "操作失败，请重试。";
const defaultOperatingVoltage = (input: Record<string, string>) => Number(
  input.vin_nom ?? input.vdc_nom ?? input.vac_rms ?? input.vll_rms ?? input.vac_ll_rms ??
  ((Number(input.vin_min) + Number(input.vin_max)) / 2),
);

export default function App() {
  const [initial] = useState(() => {
    if (authToken()) return restore();
    save({});
    return {};
  });
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catalogError, setCatalogError] = useState("");
  const [catalogRetry, setCatalogRetry] = useState(0);
  const [page, setPage] = useState<"categories" | "topologies" | "workspace" | "history" | "account" | "admin">(
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
  const [confirmation, setConfirmation] = useState<Record<
    string,
    string
  > | null>(null);
  const [recoverId, setRecoverId] = useState("");
  const submissionLock = useRef(false);
  const observedJobTopology = useRef("");
  const [authState, setAuthState] = useState<"checking" | "anonymous" | "authenticated">(
    authToken() ? "checking" : "anonymous",
  );
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [signedInAs, setSignedInAs] = useState("");
  const [signedInUser, setSignedInUser] = useState<User | null>(null);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirm, setNewPasswordConfirm] = useState("");
  const [passwordBusy, setPasswordBusy] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminError, setAdminError] = useState("");
  const [adminRefresh, setAdminRefresh] = useState(0);
  const [managedUsername, setManagedUsername] = useState("");
  const [managedPassword, setManagedPassword] = useState("");
  const [managedRole, setManagedRole] = useState<"user" | "admin">("user");
  const [resetPasswords, setResetPasswords] = useState<Record<string, string>>({});
  const [operatingVin, setOperatingVin] = useState("48");
  const [operatingLoad, setOperatingLoad] = useState("1");
  const [operatingVout, setOperatingVout] = useState("48");
  const [operatingPowerFactor, setOperatingPowerFactor] = useState("1");
  const [operatingAction, setOperatingAction] = useState<DesignAction | null>(null);
  const [operatingBusy, setOperatingBusy] = useState(false);
  const [operatingError, setOperatingError] = useState("");
  const [stageAction, setStageAction] = useState<DesignAction | null>(null);
  const [stageBusy, setStageBusy] = useState(false);
  const [stageError, setStageError] = useState("");
  const [cancelBusy, setCancelBusy] = useState(false);
  const [history, setHistory] = useState<Job[]>([]);
  const [historyStatus, setHistoryStatus] = useState("");
  const [historyQuery, setHistoryQuery] = useState("");
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyRefresh, setHistoryRefresh] = useState(0);

  useEffect(() => {
    const expired = () => {
      clearAuthToken();
      save({});
      setAuthState("anonymous");
      setSignedInAs("");
      setSignedInUser(null);
      setJobId("");
      setDraft({});
      setJob(null);
      setResult(null);
      setArtifacts([]);
    };
    window.addEventListener("pe-claw-auth-expired", expired);
    if (authToken()) {
      request<SessionInfo>("/api/v1/auth/session")
        .then((session) => {
          setSignedInAs(session.user.username);
          setSignedInUser(session.user);
          setAuthState("authenticated");
        })
        .catch(() => expired());
    }
    return () => window.removeEventListener("pe-claw-auth-expired", expired);
  }, []);

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
    const url = new URL(window.location.href);
    if (jobId) url.searchParams.set("job", jobId);
    else url.searchParams.delete("job");
    window.history.replaceState(null, "", url);
  }, [jobId, draft]);
  useEffect(() => {
    if (!jobId) return;
    setResult(null);
    setArtifacts([]);
    setOperatingAction(null);
    setOperatingError("");
    setStageAction(null);
    setStageError("");
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async () => {
      try {
        const next = await request<Job>(jobPath(jobId), {
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setJob(next);
        if (observedJobTopology.current !== next.topology) {
          const restoredTopology = catalog?.topologies.find((entry) => entry.id === next.topology);
          observedJobTopology.current = restoredTopology ? next.topology : "";
          setSelected(next.topology);
          setCategory(restoredTopology?.category_id || "dc_dc");
          applyOperatingDefaults(restoredTopology);
        }
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
  }, [jobId, retry, catalog]);

  useEffect(() => {
    if (authState !== "authenticated" || page !== "history") return;
    const controller = new AbortController();
    const parameters = new URLSearchParams({ limit: "100" });
    if (historyStatus) parameters.set("status", historyStatus);
    if (historyQuery.trim()) parameters.set("query", historyQuery.trim());
    setHistoryLoading(true);
    setHistoryError("");
    request<Job[]>(`/api/v1/design-jobs?${parameters.toString()}`, { signal: controller.signal })
      .then(setHistory)
      .catch((nextError) => {
        if (!controller.signal.aborted) setHistoryError(errorText(nextError));
      })
      .finally(() => {
        if (!controller.signal.aborted) setHistoryLoading(false);
      });
    return () => controller.abort();
  }, [authState, page, historyStatus, historyRefresh]);

  useEffect(() => {
    if (authState !== "authenticated" || page !== "admin" || signedInUser?.role !== "admin") return;
    const controller = new AbortController();
    setAdminLoading(true);
    setAdminError("");
    Promise.all([
      request<AdminUser[]>("/api/v1/admin/users", { signal: controller.signal }),
      request<AuditEvent[]>("/api/v1/admin/audit-events?limit=100", { signal: controller.signal }),
    ]).then(([users, events]) => {
      setAdminUsers(users);
      setAuditEvents(events);
    }).catch((nextError) => {
      if (!controller.signal.aborted) setAdminError(errorText(nextError));
    }).finally(() => {
      if (!controller.signal.aborted) setAdminLoading(false);
    });
    return () => controller.abort();
  }, [authState, page, signedInUser?.role, adminRefresh]);

  const topology = catalog?.topologies.find((t) => t.id === selected);
  const inputFields = [
    ...(topology?.fields || []),
    ...(topology?.options || []).map((field) => ({
      ...field,
      gui_label: field.label,
      required: true,
      exclusive_minimum: null,
    })),
  ];
  const operatingFields = topology?.operating_point?.fields.map((field) => field.key) || ["vin_v", "load_ratio"];
  const values = Object.fromEntries(
    inputFields.map((f) => [
      f.key,
      draft[f.key] ?? f.default,
    ]),
  );
  const busy =
    submitting ||
    operatingBusy ||
    stageBusy ||
    cancelBusy ||
    (!!jobId &&
      !pollError &&
      (!job || job.status === "queued" || job.status === "running"));
  function applyOperatingDefaults(t?: Topology) {
    const defaults = t?.operating_point?.defaults;
    if (defaults) {
      setOperatingVin(String(defaults.vin_v));
      setOperatingLoad(String(defaults.load_ratio));
      if (defaults.vout_v !== undefined) setOperatingVout(String(defaults.vout_v));
      if (defaults.power_factor !== undefined) setOperatingPowerFactor(String(defaults.power_factor));
    }
  }
  function openTopology(t: Topology) {
    setSelected(t.id);
    setPage("workspace");
    setConfirmation(null);
    setError("");
    applyOperatingDefaults(t);
  }
  function review(event: FormEvent) {
    event.preventDefault();
    if (!topology || busy) return;
    setError("");
    const numericFields = inputFields.filter((field) => (field.input_type || "number") === "number");
    const numbers = Object.fromEntries(
      numericFields.map((f) => [f.key, Number(values[f.key])]),
    );
    if (
      numericFields.some(
        (f) =>
          (f.required !== false && !values[f.key]?.trim()) ||
          !Number.isFinite(numbers[f.key]) ||
          (f.exclusive_minimum !== null &&
            numbers[f.key] <= f.exclusive_minimum),
      )
    ) {
      setError("请输入有效的正数，所有设计参数均为必填项。");
      return;
    }
    if (inputFields.some((field) => {
      const value = values[field.key]?.trim() || "";
      if (field.required !== false && !value) return true;
      return field.input_type === "select" && !field.choices?.includes(value);
    })) {
      setError("请填写所有必填字段并选择有效选项。");
      return;
    }
    if ("vin_min" in numbers && "vin_max" in numbers && numbers.vin_max < numbers.vin_min) {
      setError("Vin max 必须大于或等于 Vin min。");
      return;
    }
    if (selected === BUCK && numbers.vout >= numbers.vin_min) {
      setError("Buck 拓扑要求 Vout 小于 Vin min。");
      return;
    }
    setConfirmation({ ...values });
  }
  async function runConfirmed() {
    if (!topology || !confirmation || busy || submissionLock.current) return;
    const rawInput = Object.fromEntries(inputFields.map((field) => [
      field.key,
      (field.input_type || "number") === "number" && confirmation[field.key] !== ""
        ? Number(confirmation[field.key])
        : confirmation[field.key],
    ]));
    submissionLock.current = true;
    setSubmitting(true);
    setError("");
    try {
      const next = await request<Job>("/api/v1/design-jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request: { topology: selected, raw_input: rawInput }, execution_profile: "complete" }),
      });
      setResult(null);
      setArtifacts([]);
      setPollError("");
      setJob(next);
      observedJobTopology.current = selected;
      setSubmitted({ ...confirmation });
      const nominalInput = defaultOperatingVoltage(confirmation);
      if (Number.isFinite(nominalInput)) setOperatingVin(String(nominalInput));
      setOperatingLoad("1");
      const vout = Number(confirmation.vout_nom ?? confirmation.vout ?? confirmation.vout_v);
      if (Number.isFinite(vout)) setOperatingVout(String(vout));
      const powerFactor = Number(confirmation.power_factor ?? confirmation.power_factor_target ?? 1);
      if (Number.isFinite(powerFactor)) setOperatingPowerFactor(String(powerFactor));
      setConfirmation(null);
      setJobId(next.job_id);
      setRetry(v => v + 1); // An idempotent submission can return the current job ID.
    } catch (e) {
      setError(errorText(e));
    } finally {
      submissionLock.current = false;
      setSubmitting(false);
    }
  }
  const selectCategory = (id: string) => {
    setCategory(id);
    setPage("topologies");
  };
  const openHistoryJob = (item: Job) => {
    setJob(null);
    setResult(null);
    setArtifacts([]);
    setPollError("");
    setJobId(item.job_id);
    setSelected(item.topology);
    observedJobTopology.current = item.topology;
    const restoredTopology = catalog?.topologies.find((entry) => entry.id === item.topology);
    setCategory(restoredTopology?.category_id || "dc_dc");
    applyOperatingDefaults(restoredTopology);
    setPage("workspace");
    setRetry((value) => value + 1);
  };
  async function resumeJob(restart = false) {
    if (submitting || submissionLock.current) return;
    submissionLock.current = true;
    setSubmitting(true);
    setError("");
    try {
      const next = await request<Job>(`${jobPath(jobId)}/retry?restart=${restart}`, { method: "POST" });
      setJob(next);
      setResult(null);
      setArtifacts([]);
      setRetry(v => v + 1);
    } catch (e) { setError(errorText(e)); }
    finally {
      submissionLock.current = false;
      setSubmitting(false);
    }
  }
  async function cancelJob() {
    if (!jobId || !job || !["queued", "running"].includes(job.status) || cancelBusy) return;
    setCancelBusy(true);
    setError("");
    try {
      const next = await request<Job>(`${jobPath(jobId)}/cancel`, { method: "POST" });
      setJob(next);
      setResult(null);
      setArtifacts([]);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setCancelBusy(false);
    }
  }
  async function refreshOperatingPoint(event: FormEvent) {
    event.preventDefault();
    if (!jobId || job?.status !== "succeeded" || operatingBusy) return;
    const vin = Number(operatingVin);
    const load = Number(operatingLoad);
    const vout = Number(operatingVout);
    const powerFactor = Number(operatingPowerFactor);
    const vinMinText = submitted?.vin_min ?? submitted?.vac_rms_min;
    const vinMaxText = submitted?.vin_max ?? submitted?.vac_rms_max;
    const vinMin = Number(vinMinText);
    const vinMax = Number(vinMaxText);
    setOperatingError("");
    if (!Number.isFinite(vin) || vin <= 0 || (
      vinMinText !== undefined && vinMaxText !== undefined && (vin < vinMin || vin > vinMax)
    )) {
      setOperatingError(vinMinText !== undefined && vinMaxText !== undefined
        ? `运行点输入电压必须位于设计范围 ${vinMin}–${vinMax} V。`
        : "运行点输入电压必须是正数。");
      return;
    }
    if (!Number.isFinite(load) || load < 0) {
      setOperatingError("负载比例必须是大于或等于 0 的数值。");
      return;
    }
    if (operatingFields.includes("vout_v") && (!Number.isFinite(vout) || vout <= 0)) {
      setOperatingError("运行点输出电压必须是正数。");
      return;
    }
    if (operatingFields.includes("power_factor") && (
      !Number.isFinite(powerFactor) || powerFactor < -1 || powerFactor > 1
    )) {
      setOperatingError("功率因数必须位于 -1 到 1 之间。");
      return;
    }
    setOperatingBusy(true);
    try {
      const base = `${jobPath(jobId)}/actions`;
      let action = await request<DesignAction>(`${base}/waveforms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: jobId,
          action: "waveforms",
          operating_point: {
            vin_v: vin,
            load_ratio: load,
            ...(operatingFields.includes("vout_v") ? { vout_v: vout } : {}),
            ...(operatingFields.includes("power_factor") ? { power_factor: powerFactor } : {}),
          },
        }),
      });
      setOperatingAction(action);
      while (action.status === "queued" || action.status === "running") {
        await new Promise((resolve) => window.setTimeout(resolve, 800));
        action = await request<DesignAction>(`${base}/${encodeURIComponent(action.action_id)}`);
        setOperatingAction(action);
      }
      if (action.status !== "succeeded") {
        throw new Error(action.error?.message || "运行点刷新未完成。");
      }
      const refreshed = await request<ActionResult>(
        `${base}/${encodeURIComponent(action.action_id)}/result`,
      );
      setResult({
        job_id: jobId,
        topology: result?.topology || selected,
        summary: refreshed.summary,
        warnings: refreshed.warnings,
        artifacts: refreshed.artifacts,
      });
      setArtifacts((current) => [
        ...refreshed.artifacts,
        ...current.filter((item) => !refreshed.artifacts.some((next) => next.id === item.id)),
      ]);
    } catch (e) {
      setOperatingError(errorText(e));
    } finally {
      setOperatingBusy(false);
    }
  }
  async function runStageAction(actionName: "capacitor" | "magnetics" | "efficiency_sweep") {
    if (!jobId || job?.status !== "succeeded" || stageBusy) return;
    setStageBusy(true);
    setStageError("");
    try {
      const base = `${jobPath(jobId)}/actions`;
      const slug = actionName === "efficiency_sweep" ? "efficiency-sweep" : actionName;
      let action = await request<DesignAction>(`${base}/${slug}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, action: actionName }),
      });
      setStageAction(action);
      while (action.status === "queued" || action.status === "running") {
        await new Promise((resolve) => window.setTimeout(resolve, 800));
        action = await request<DesignAction>(`${base}/${encodeURIComponent(action.action_id)}`);
        setStageAction(action);
      }
      if (action.status !== "succeeded") {
        throw new Error(action.error?.message || "阶段操作未完成。");
      }
      const refreshed = await request<ActionResult>(
        `${base}/${encodeURIComponent(action.action_id)}/result`,
      );
      setResult({
        job_id: jobId,
        topology: result?.topology || selected,
        summary: refreshed.summary,
        warnings: refreshed.warnings,
        artifacts: refreshed.artifacts,
      });
      setArtifacts((current) => [
        ...refreshed.artifacts,
        ...current.filter((item) => !refreshed.artifacts.some((next) => next.id === item.id)),
      ]);
    } catch (e) {
      setStageError(errorText(e));
    } finally {
      setStageBusy(false);
    }
  }
  async function signIn(event: FormEvent) {
    event.preventDefault();
    if (authBusy) return;
    setAuthBusy(true);
    setAuthError("");
    try {
      const session = await request<Session>("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      setAuthToken(session.access_token);
      save({});
      setPassword("");
      setSignedInAs(session.user.username);
      setSignedInUser(session.user);
      setAuthState("authenticated");
      setJobId("");
      setDraft({});
      setRetry((value) => value + 1);
    } catch (e) {
      setAuthError(errorText(e));
    } finally {
      setAuthBusy(false);
    }
  }
  async function registerAccount(event: FormEvent) {
    event.preventDefault();
    if (authBusy) return;
    setAuthError("");
    if (password !== confirmPassword) {
      setAuthError("两次输入的密码不一致。");
      return;
    }
    setAuthBusy(true);
    try {
      const session = await request<Session>("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      setAuthToken(session.access_token);
      save({});
      setPassword("");
      setConfirmPassword("");
      setSignedInAs(session.user.username);
      setSignedInUser(session.user);
      setAuthState("authenticated");
      setJobId("");
      setDraft({});
    } catch (e) {
      setAuthError(errorText(e));
    } finally {
      setAuthBusy(false);
    }
  }
  async function changeOwnPassword(event: FormEvent) {
    event.preventDefault();
    if (passwordBusy) return;
    setPasswordError("");
    if (newPassword !== newPasswordConfirm) {
      setPasswordError("两次输入的新密码不一致。");
      return;
    }
    setPasswordBusy(true);
    try {
      await request<void>("/api/v1/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      clearAuthToken();
      save({});
      setCurrentPassword("");
      setNewPassword("");
      setNewPasswordConfirm("");
      setSignedInAs("");
      setSignedInUser(null);
      setAuthState("anonymous");
      setAuthMode("login");
    } catch (e) {
      setPasswordError(errorText(e));
    } finally {
      setPasswordBusy(false);
    }
  }
  async function createManagedUser(event: FormEvent) {
    event.preventDefault();
    setAdminError("");
    try {
      await request<AdminUser>("/api/v1/admin/users", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: managedUsername, password: managedPassword, role: managedRole }),
      });
      setManagedUsername("");
      setManagedPassword("");
      setManagedRole("user");
      setAdminRefresh((value) => value + 1);
    } catch (e) { setAdminError(errorText(e)); }
  }
  async function updateManagedUser(user: AdminUser, changes: { role?: "user" | "admin"; active?: boolean }) {
    setAdminError("");
    try {
      await request<AdminUser>(`/api/v1/admin/users/${encodeURIComponent(user.user_id)}/update`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(changes),
      });
      setAdminRefresh((value) => value + 1);
    } catch (e) { setAdminError(errorText(e)); }
  }
  async function resetManagedPassword(user: AdminUser) {
    const next = resetPasswords[user.user_id] || "";
    setAdminError("");
    try {
      await request<void>(`/api/v1/admin/users/${encodeURIComponent(user.user_id)}/reset-password`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ new_password: next }),
      });
      setResetPasswords((current) => ({ ...current, [user.user_id]: "" }));
      setAdminRefresh((value) => value + 1);
    } catch (e) { setAdminError(errorText(e)); }
  }
  async function signOut() {
    try { await request<void>("/api/v1/auth/logout", { method: "POST" }); }
    catch { /* Local revocation still prevents reuse in this browser. */ }
    clearAuthToken();
    save({});
    setAuthState("anonymous");
    setSignedInAs("");
    setSignedInUser(null);
    setJobId("");
    setDraft({});
    setJob(null);
    setResult(null);
    setArtifacts([]);
  }
  const stageEntries: [string, StageState][] = job?.stage_details
    ? Object.entries(job.stage_details)
    : Object.entries(job?.stages || {}).map(([stage, status]) => [
        stage,
        {
          schema_version: "1.0",
          status: status as StageState["status"],
          progress: ["succeeded", "failed", "blocked", "unavailable"].includes(status) ? 100 : 0,
          warnings: [],
        },
      ]);
  if (authState !== "authenticated") {
    return <>
      <header className="masthead">
        <div className="brand"><span className="logo">PE</span><div><strong>PE-Claw</strong><small>POWER ELECTRONICS DESIGN</small></div></div>
      </header>
      <main className="login-shell">
        {authState === "checking" ? <p role="status" className="loading">正在验证会话…</p> :
          <form className="panel login-panel" onSubmit={authMode === "login" ? signIn : registerAccount}>
            <span className="eyebrow">SECURE WORKSPACE</span>
            <h1>{authMode === "login" ? "登录设计工作区" : "注册设计账户"}</h1>
            <p>{authMode === "login" ? "任务、结果和下载仅对其所有者可见。" : "用户名使用小写字母开头；密码至少 12 个字符。"}</p>
            <label>用户名<input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required /></label>
            <label>密码<input type="password" minLength={authMode === "register" ? 12 : 1} autoComplete={authMode === "login" ? "current-password" : "new-password"} value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
            {authMode === "register" && <label>确认密码<input type="password" minLength={12} autoComplete="new-password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required /></label>}
            {authError && <div className="error" role="alert">{authError}</div>}
            <button className="primary" disabled={authBusy}>{authBusy ? "正在处理…" : authMode === "login" ? "登录" : "注册并登录"}</button>
            <button type="button" onClick={() => { setAuthMode(authMode === "login" ? "register" : "login"); setAuthError(""); setPassword(""); setConfirmPassword(""); }}>
              {authMode === "login" ? "创建新账户" : "返回登录"}
            </button>
          </form>}
      </main>
    </>;
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
          <span className="dot" /> {signedInAs}
          <button className="logout" onClick={() => setPage("account")}>账户</button>
          {signedInUser?.role === "admin" && <button className="logout" onClick={() => setPage("admin")}>管理</button>}
          <button className="logout" onClick={() => void signOut()}>退出</button>
          <span className="version">WEB · 0.1</span>
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
        <button onClick={() => setPage("history")}>我的任务</button>
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
                  observedJobTopology.current = "";
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
              <p>选择拓扑。所有已注册设计表单均通过同一 Web 输入契约运行。</p>
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
                      {t.web_enabled ? "可开始设计" : "尚未实现"}
                    </span>
                    <h2>{t.name}</h2>
                    <p>
                      {t.web_enabled
                        ? "电气参数 · 器件选择 · 结构化报告"
                        : "此拓扑尚未实现。"}
                    </p>
                  </button>
                ))}
            </div>
            {!catalog.topologies.some((t) => t.category_id === category) && (
              <div className="panel empty">此分类暂无已注册拓扑。</div>
            )}
          </>
        ) : page === "history" ? (
          <>
            <div className="page-title">
              <span className="eyebrow">MY DESIGN JOBS</span>
              <h1>我的历史任务</h1>
              <p>仅显示当前账户拥有的任务，按创建时间倒序排列。</p>
            </div>
            <section className="panel history-panel" aria-labelledby="history-title">
              <form className="history-filters" onSubmit={(event) => {
                event.preventDefault();
                setHistoryRefresh((value) => value + 1);
              }}>
                <label>任务状态
                  <select value={historyStatus} onChange={(event) => setHistoryStatus(event.target.value)}>
                    <option value="">全部状态</option>
                    {Object.entries(statusLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </label>
                <label>任务编号
                  <input value={historyQuery} maxLength={64} onChange={(event) => setHistoryQuery(event.target.value)} placeholder="输入完整或部分编号" />
                </label>
                <button type="submit">搜索</button>
              </form>
              {historyError && <div className="error" role="alert">{historyError}</div>}
              {historyLoading ? <p role="status" className="loading">正在读取历史任务…</p> : history.length === 0 ? (
                <div className="empty"><h2 id="history-title">暂无匹配任务</h2><p>运行设计后，任务会保存在这里。</p></div>
              ) : (
                <div className="history-table-wrap">
                  <table className="history-table">
                    <caption id="history-title">最近 {history.length} 个任务</caption>
                    <thead><tr><th>创建时间</th><th>拓扑</th><th>状态</th><th>进度</th><th>任务编号</th><th /></tr></thead>
                    <tbody>{history.map((item) => <tr key={item.job_id}>
                      <td>{new Date(item.created_at).toLocaleString()}</td>
                      <td>{catalog.topologies.find((entry) => entry.id === item.topology)?.name || item.topology}</td>
                      <td><span className={`history-status ${item.status}`}>{statusLabels[item.status]}</span></td>
                      <td>{item.progress}%</td>
                      <td><code>{item.job_id}</code></td>
                      <td><button onClick={() => openHistoryJob(item)}>查看</button></td>
                    </tr>)}</tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        ) : page === "account" ? (
          <>
            <div className="page-title">
              <span className="eyebrow">ACCOUNT SECURITY</span>
              <h1>账户设置</h1>
              <p>{signedInUser?.username} · {signedInUser?.role === "admin" ? "管理员" : "用户"}</p>
            </div>
            <form className="panel account-panel" onSubmit={changeOwnPassword}>
              <h2>修改密码</h2>
              <p>修改成功后，所有设备上的现有会话都会失效，请使用新密码重新登录。</p>
              <label>当前密码<input type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} required /></label>
              <label>新密码<input type="password" minLength={12} autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required /></label>
              <label>确认新密码<input type="password" minLength={12} autoComplete="new-password" value={newPasswordConfirm} onChange={(event) => setNewPasswordConfirm(event.target.value)} required /></label>
              {passwordError && <div className="error" role="alert">{passwordError}</div>}
              <button className="primary" disabled={passwordBusy}>{passwordBusy ? "正在修改…" : "修改密码"}</button>
            </form>
          </>
        ) : page === "admin" && signedInUser?.role === "admin" ? (
          <>
            <div className="page-title">
              <span className="eyebrow">ADMINISTRATION</span>
              <h1>用户与审计管理</h1>
              <p>创建账户、调整权限、禁用访问、重置密码并查看最近审计事件。</p>
            </div>
            {adminError && <div className="error" role="alert">{adminError}</div>}
            <form className="panel admin-create" onSubmit={createManagedUser}>
              <h2>创建用户</h2>
              <label>新用户名<input value={managedUsername} onChange={(event) => setManagedUsername(event.target.value)} required /></label>
              <label>初始密码<input type="password" minLength={12} value={managedPassword} onChange={(event) => setManagedPassword(event.target.value)} required /></label>
              <label>角色<select value={managedRole} onChange={(event) => setManagedRole(event.target.value as "user" | "admin")}><option value="user">用户</option><option value="admin">管理员</option></select></label>
              <button className="primary">创建用户</button>
            </form>
            {adminLoading ? <p role="status" className="loading">正在读取管理数据…</p> : <>
              <section className="panel admin-section" aria-labelledby="admin-users-title">
                <h2 id="admin-users-title">用户</h2>
                <div className="history-table-wrap"><table className="history-table"><thead><tr><th>用户名</th><th>角色</th><th>状态</th><th>创建时间</th><th>密码重置</th><th>操作</th></tr></thead>
                  <tbody>{adminUsers.map((user) => <tr key={user.user_id}>
                    <td>{user.username}{user.user_id === signedInUser.user_id ? "（当前）" : ""}</td>
                    <td><select aria-label={`${user.username} 角色`} value={user.role} disabled={user.user_id === signedInUser.user_id} onChange={(event) => void updateManagedUser(user, { role: event.target.value as "user" | "admin" })}><option value="user">用户</option><option value="admin">管理员</option></select></td>
                    <td>{user.active ? "启用" : "禁用"}</td>
                    <td>{new Date(user.created_at).toLocaleString()}</td>
                    <td><div className="admin-reset"><input aria-label={`${user.username} 新密码`} type="password" minLength={12} value={resetPasswords[user.user_id] || ""} onChange={(event) => setResetPasswords((current) => ({ ...current, [user.user_id]: event.target.value }))} /><button aria-label={`${user.username} 重置密码`} disabled={(resetPasswords[user.user_id] || "").length < 12} onClick={() => void resetManagedPassword(user)}>重置</button></div></td>
                    <td><button aria-label={`${user.username} ${user.active ? "禁用" : "启用"}`} disabled={user.user_id === signedInUser.user_id} onClick={() => void updateManagedUser(user, { active: !user.active })}>{user.active ? "禁用" : "启用"}</button></td>
                  </tr>)}</tbody>
                </table></div>
              </section>
              <section className="panel admin-section" aria-labelledby="audit-title">
                <h2 id="audit-title">最近审计事件</h2>
                <div className="history-table-wrap"><table className="history-table"><thead><tr><th>时间</th><th>操作</th><th>结果</th><th>操作者</th><th>资源</th></tr></thead><tbody>{auditEvents.map((event) => <tr key={event.event_id}><td>{new Date(event.occurred_at).toLocaleString()}</td><td>{event.action}</td><td>{event.outcome}</td><td><code>{event.actor_user_id || "system"}</code></td><td>{event.resource_type} / {event.resource_id || "-"}</td></tr>)}</tbody></table></div>
              </section>
            </>}
          </>
        ) : (
          <>
            <div className="workspace-title">
              <div>
                <span className="eyebrow">03 / DESIGN WORKSPACE</span>
                <h1>{topology?.name}</h1>
              </div>
              <span className="tag ready">{category.toUpperCase().replace("_", "-")}</span>
            </div>
            <div className="workspace">
              <aside>
                {confirmation ? (
                  <section className="panel confirmation-panel" aria-labelledby="confirmation-title">
                    <div className="panel-head">
                      <div>
                        <span className="eyebrow">DESIGN CONFIRMATION</span>
                        <h2 id="confirmation-title">确认完整设计</h2>
                      </div>
                      <span className="tag ready">准备提交</span>
                    </div>
                    <div className="confirmation-body">
                      <p>请确认拓扑、输入单位与运行点。提交后将启动一个完整顺序任务。</p>
                      <dl className="confirmation-values">
                        <div><dt>拓扑</dt><dd>{topology?.name}</dd></div>
                        {inputFields.map((field) => (
                          <div key={field.key}>
                            <dt>{field.label}</dt>
                            <dd>{confirmation[field.key]} {field.unit}</dd>
                          </div>
                        ))}
                        {Number.isFinite(defaultOperatingVoltage(confirmation)) && <div>
                          <dt>默认运行点输入</dt><dd>{defaultOperatingVoltage(confirmation)} V</dd>
                        </div>}
                        <div><dt>默认运行点负载</dt><dd>1 p.u.</dd></div>
                      </dl>
                      <ol className="sequence" aria-label="完整设计阶段">
                        {[
                          "Validate", "Topology", "Devices", "Capacitor", "Magnetics",
                          "Operating point", "Loss", "Thermal", "Efficiency", "Report", "Finalize",
                        ].map((stage) => <li key={stage}>{stage}</li>)}
                      </ol>
                      {error && <div role="alert" className="error">{error}</div>}
                      <div className="confirmation-actions">
                        <button type="button" disabled={submitting} onClick={() => { setConfirmation(null); setError(""); }}>
                          返回修改
                        </button>
                        <button className="primary" type="button" disabled={submitting} onClick={() => void runConfirmed()}>
                          {submitting ? "正在提交…" : "确认并运行完整设计"}
                        </button>
                      </div>
                      <p className="form-note">同一次点击只创建或复用一个任务；浏览器仅保存任务编号和表单草稿。</p>
                    </div>
                  </section>
                ) : (
                <form className="panel input-panel" onSubmit={review}>
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
                        setConfirmation(null);
                        setError("");
                      }}
                    >
                      重置
                    </button>
                  </div>
                  <fieldset disabled={busy}>
                    {inputFields.map((f) => (
                      <label className="field" key={f.key} htmlFor={f.key}>
                        <span>{f.label}</span>
                        <div className="input-unit">
                          {f.input_type === "select" ? <select
                            id={f.key}
                            required={f.required !== false}
                            value={values[f.key]}
                            onChange={(e) => {
                              setDraft((v) => ({
                                ...v,
                                [f.key]: e.target.value,
                              }));
                              setError("");
                            }}
                          >{(f.choices || []).map((choice) => <option key={choice} value={choice}>{choice}</option>)}</select> : <input
                            id={f.key}
                            type={f.input_type === "text" ? "text" : "number"}
                            step={f.input_type === "text" ? undefined : "any"}
                            required={f.required !== false}
                            value={values[f.key]}
                            onChange={(e) => {
                              setDraft((v) => ({ ...v, [f.key]: e.target.value }));
                              setError("");
                            }}
                          />}
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
                        : "检查并确认设计"}
                  </button>
                  <p className="form-note">
                    参数提交后由本地后端计算。离开页面不会取消已提交的任务。
                  </p>
                </form>
                )}
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
                    {(job?.status === "queued" || job?.status === "running") && (
                      <button className="danger" disabled={cancelBusy} onClick={() => void cancelJob()}>
                        {cancelBusy ? "正在取消…" : "取消任务"}
                      </button>
                    )}
                    {stageEntries.length > 0 && <details><summary>阶段状态 · 第 {job?.attempt || 0} 次执行</summary>
                      <ol className="stage-list">{stageEntries.map(([stage, detail]) => <li key={stage} className={detail.status}>
                        <div><strong>{stage}</strong><span>{stageStatusLabels[detail.status] || detail.status}</span></div>
                        {detail.warnings.map((warning, index) => <small key={index}>{warning}</small>)}
                        {detail.error && <small>{detail.error.message}</small>}
                      </li>)}</ol>
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
                {job?.status === "succeeded" && result && (
                  <section className="panel stage-actions" aria-labelledby="stage-actions-title">
                    <div className="panel-head">
                      <div>
                        <span className="eyebrow">DERIVED DESIGN ACTIONS</span>
                        <h2 id="stage-actions-title">独立阶段操作</h2>
                      </div>
                      <span className="tag ready">基于当前任务</span>
                    </div>
                    <div className="stage-action-buttons">
                      <button disabled={stageBusy} onClick={() => void runStageAction("capacitor")}>重新运行电容设计</button>
                      <button disabled={stageBusy} onClick={() => void runStageAction("magnetics")}>重新运行磁件设计</button>
                      <button disabled={stageBusy} onClick={() => void runStageAction("efficiency_sweep")}>刷新固定硬件效率扫描</button>
                    </div>
                    <p className="form-note">每项操作从当前成功任务的最终快照派生；不会重新综合拓扑或重新选择半导体器件。</p>
                    {stageAction?.status === "succeeded" && (
                      <p className="success" role="status">{stageAction.action} 已完成，结果视图已更新。</p>
                    )}
                    {stageAction && stageAction.status !== "succeeded" && !stageError && (
                      <p role="status">{statusLabels[stageAction.status] || stageAction.status} · {stageAction.stage || "queued"} · {stageAction.progress}%</p>
                    )}
                    {stageError && <div className="error" role="alert">{stageError}</div>}
                  </section>
                )}
                {job?.status === "succeeded" && result && (
                  <section className="panel operating-point" aria-labelledby="operating-point-title">
                    <div className="panel-head">
                      <div>
                        <span className="eyebrow">FIXED HARDWARE OPERATING POINT</span>
                        <h2 id="operating-point-title">固定硬件工作点刷新</h2>
                      </div>
                      <span className="tag ready">不重新选型</span>
                    </div>
                    <form onSubmit={refreshOperatingPoint}>
                      {operatingFields.includes("vin_v") && <label>
                        <span>运行点 Vin</span>
                        <div className="input-unit">
                          <input type="number" step="any" value={operatingVin} onChange={(event) => setOperatingVin(event.target.value)} required />
                          <span>V</span>
                        </div>
                      </label>}
                      {operatingFields.includes("vout_v") && <label>
                        <span>运行点 Vout</span>
                        <div className="input-unit">
                          <input type="number" step="any" min="0" value={operatingVout} onChange={(event) => setOperatingVout(event.target.value)} required />
                          <span>V</span>
                        </div>
                      </label>}
                      <label>
                        <span>负载比例</span>
                        <div className="input-unit">
                          <input type="number" step="any" min="0" value={operatingLoad} onChange={(event) => setOperatingLoad(event.target.value)} required />
                          <span>p.u.</span>
                        </div>
                      </label>
                      {operatingFields.includes("power_factor") && <label>
                        <span>功率因数</span>
                        <div className="input-unit">
                          <input type="number" step="any" min="-1" max="1" value={operatingPowerFactor} onChange={(event) => setOperatingPowerFactor(event.target.value)} required />
                        </div>
                      </label>}
                      <button className="primary" disabled={operatingBusy}>
                        {operatingBusy ? "正在刷新…" : "刷新固定硬件工作点"}
                      </button>
                    </form>
                    <p className="form-note">沿用当前任务已选候选、器件、电容和磁件，只刷新工作点相关波形、应力、损耗与热结果。</p>
                    {operatingAction?.status === "succeeded" && (
                      <p className="success" role="status">当前显示：{operatingFields.includes("vin_v") ? `${operatingVin} V / ` : ""}{operatingFields.includes("vout_v") ? `${operatingVout} Vout / ` : ""}{operatingLoad} p.u.{operatingFields.includes("power_factor") ? ` / PF ${operatingPowerFactor}` : ""}（固定硬件）</p>
                    )}
                    {operatingAction && operatingAction.status !== "succeeded" && !operatingError && (
                      <p role="status">{statusLabels[operatingAction.status] || operatingAction.status} · {operatingAction.stage || "queued"} · {operatingAction.progress}%</p>
                    )}
                    {operatingError && <div className="error" role="alert">{operatingError}</div>}
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
