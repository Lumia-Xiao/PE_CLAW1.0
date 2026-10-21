export const BUCK = "buck_diode_rectified_unidirectional";
export interface Field {
  key: string;
  label: string;
  gui_label?: string;
  unit: string;
  default: string;
  input_type?: "number" | "select" | "text";
  choices?: string[];
  required?: boolean;
  exclusive_minimum: number | null;
}
export interface OptionField {
  key: string;
  label: string;
  unit: string;
  default: string;
  input_type: "number" | "select";
  choices?: string[];
  minimum?: number;
  maximum?: number;
}
export interface Topology {
  id: string;
  name: string;
  category_id: string;
  web_enabled: boolean;
  fields: Field[];
  options?: OptionField[];
  operating_point?: {
    defaults: Record<string, number>;
    fields: { key: "vin_v" | "vout_v" | "load_ratio" | "power_factor"; label: string; unit: string; minimum?: number; maximum?: number }[];
  };
}
export interface Catalog {
  categories: { id: string; name: string; description: string }[];
  topologies: Topology[];
}
export type JobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "expired";
export type StageStatus =
  | "pending"
  | "running"
  | "succeeded"
  | "failed"
  | "blocked"
  | "unavailable";
export interface StageState {
  schema_version: "1.0";
  status: StageStatus;
  progress: number;
  warnings: string[];
  error?: {
    code: string;
    message: string;
    correlation_id?: string | null;
  } | null;
  started_at?: string | null;
  finished_at?: string | null;
}
export interface Job {
  job_id: string;
  topology: string;
  status: JobStatus;
  progress: number;
  stage: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  result_url?: string | null;
  attempt?: number;
  stages?: Record<string, string>;
  stage_details?: Record<string, StageState>;
  retryable?: boolean;
  error?: {
    code: string;
    message: string;
    correlation_id?: string | null;
  } | null;
}
export type Json =
  | string
  | number
  | boolean
  | null
  | Json[]
  | { [key: string]: Json };
export interface Artifact {
  id: string;
  name: string;
  media_type: string;
  size: number;
  download_url: string;
  sha256?: string;
  schema_version?: string;
  stage?: string;
}
export interface Result {
  job_id: string;
  topology: string;
  summary: Record<string, Json>;
  warnings: string[];
  artifacts: Artifact[];
}
export type ActionStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "expired";
export interface DesignAction {
  action_id: string;
  job_id: string;
  action: "capacitor" | "magnetics" | "waveforms" | "efficiency_sweep";
  status: ActionStatus;
  progress: number;
  stage?: string | null;
  result_url?: string | null;
  error?: {
    code: string;
    message: string;
    correlation_id?: string | null;
  } | null;
}
export interface ActionResult {
  schema_version: "1.0";
  action_id: string;
  job_id: string;
  action: DesignAction["action"];
  summary: Record<string, Json>;
  warnings: string[];
  artifacts: Artifact[];
}
export interface User {
  user_id: string;
  username: string;
  role: "user" | "admin";
}
export interface AdminUser extends User {
  active: boolean;
  created_at: string;
}
export interface AuditEvent {
  event_id: string;
  occurred_at: string;
  actor_user_id?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  outcome: string;
  details: Record<string, string | number | boolean | null>;
}
export interface Session {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  user: User;
}
export interface SessionInfo {
  expires_at: string;
  user: User;
}

const authKey = "pe-claw-session-v1";
export const authToken = () => sessionStorage.getItem(authKey) || "";
export const setAuthToken = (token: string) => sessionStorage.setItem(authKey, token);
export const clearAuthToken = () => sessionStorage.removeItem(authKey);

function authenticatedOptions(options: RequestInit): RequestInit {
  const headers = new Headers(options.headers);
  const token = authToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return { ...options, headers };
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function request<T>(
  url: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    const timeout = AbortSignal.timeout(15000);
    const signal = options.signal
      ? AbortSignal.any([options.signal, timeout])
      : timeout;
    response = await fetch(url, authenticatedOptions({ ...options, signal }));
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new ApiError("无法连接设计服务，请检查服务是否已启动后重试。", 0);
  }
  if (!response.ok) {
    if (response.status === 401) {
      clearAuthToken();
      window.dispatchEvent(new Event("pe-claw-auth-expired"));
    }
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof body.message === "string"
      ? body.message
      : Array.isArray(detail)
      ? detail
          .map(
            (e: { loc: string[]; msg: string }) =>
              `${e.loc.join(".")}: ${e.msg}`,
          )
          .join("；")
        : typeof detail === "string"
          ? detail
          : `请求失败（${response.status}）`;
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export async function artifactBlob(url: string): Promise<Blob> {
  const safe = safeDownload(url);
  if (!safe) throw new ApiError("无效的文件地址。", 400);
  const response = await fetch(safe, authenticatedOptions({ signal: AbortSignal.timeout(30000) }));
  if (!response.ok) {
    if (response.status === 401) {
      clearAuthToken();
      window.dispatchEvent(new Event("pe-claw-auth-expired"));
    }
    throw new ApiError(`文件下载失败（${response.status}）`, response.status);
  }
  return response.blob();
}
export const jobPath = (id: string) =>
  `/api/v1/design-jobs/${encodeURIComponent(id)}`;
export function safeDownload(url: string): string | undefined {
  try {
    const target = new URL(url, window.location.origin);
    return target.origin === window.location.origin &&
      target.pathname.startsWith("/api/v1/design-jobs/")
      ? target.href
      : undefined;
  } catch {
    return undefined;
  }
}
