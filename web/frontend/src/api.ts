export const BUCK = "buck_diode_rectified_unidirectional";
export interface Field {
  key: string;
  label: string;
  unit: string;
  default: string;
  exclusive_minimum: number | null;
}
export interface Topology {
  id: string;
  name: string;
  category_id: string;
  web_enabled: boolean;
  fields: Field[];
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
export interface Job {
  job_id: string;
  topology: string;
  status: JobStatus;
  progress: number;
  stage: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
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
    response = await fetch(url, { ...options, signal });
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new ApiError("无法连接设计服务，请检查服务是否已启动后重试。", 0);
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = Array.isArray(detail)
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
  return response.json() as Promise<T>;
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
