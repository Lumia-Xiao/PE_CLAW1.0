import { useState } from "react";
import { safeDownload, type Artifact, type Json, type Result } from "./api";

const sections = [
  ["summary", "Summary", "设计摘要"],
  ["hardware", "Hardware Overview", "硬件总览"],
  ["waveform", "Waveforms", "波形"],
  ["stress", "Stress", "电气应力"],
  ["hardware", "Devices", "半导体"],
  ["capacitor", "Capacitor", "电容"],
  ["magnetic", "Magnetics", "磁性器件"],
  ["loss", "Loss", "损耗"],
  ["thermal", "Thermal", "热分析"],
  ["geometry", "Geometry", "几何"],
  ["efficiency_sweep", "Efficiency", "效率"],
  ["files", "Files", "报告下载"],
] as const;

const object = (v: Json | undefined): v is Record<string, Json> =>
  !!v && typeof v === "object" && !Array.isArray(v);
const number = (v: Json | undefined): number | undefined => {
  const value = object(v) ? v.value : v;
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
};
export const format = (v: Json | undefined): string =>
  v === null || v === undefined
    ? "未提供"
    : typeof v === "number"
      ? Number(v.toPrecision(6)).toString()
      : String(v);

type Row = { name: string; value: Json; unit: string; source: string };
function rowsOf(value: Json, path = ""): Row[] {
  if (object(value) && "value" in value && "unit" in value) {
    return [
      {
        name: path,
        value: value.value,
        unit: String(value.unit ?? ""),
        source: String(value.source ?? ""),
      },
    ];
  }
  if (value && typeof value === "object") {
    return Object.entries(value).flatMap(([key, child]) =>
      rowsOf(child, path ? `${path}.${key}` : key),
    );
  }
  return [{ name: path, value, unit: "", source: "" }];
}
function DataTable({ value }: { value: Json }) {
  const rows = rowsOf(value);
  const [limit, setLimit] = useState(80);
  if (!rows.length) return <p className="empty-small">此阶段暂无结果。</p>;
  return (
    <>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>参数 / Parameter</th>
              <th>数值</th>
              <th>单位</th>
              <th>来源</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, limit).map((row, i) => (
              <tr key={`${row.name}-${i}`}>
                <td>{row.name}</td>
                <td>{format(row.value)}</td>
                <td>{row.unit || "—"}</td>
                <td className="source">{row.source || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > limit && (
        <button onClick={() => setLimit(limit + 200)}>
          显示更多（{limit} / {rows.length}）
        </button>
      )}
    </>
  );
}
function EfficiencyChart({ data }: { data: Json }) {
  if (!object(data) || !Array.isArray(data.points)) return null;
  const points = data.points
    .filter(object)
    .map((p) => ({ x: number(p.load_ratio), y: number(p.efficiency) }))
    .filter(
      (p): p is { x: number; y: number } =>
        p.x !== undefined && p.y !== undefined,
    )
    .sort((a, b) => a.x - b.x);
  if (points.length < 2) return null;
  const maxX = Math.max(...points.map((p) => p.x), 1);
  const ys = points.map((p) => p.y * 100);
  const low = Math.floor(Math.min(...ys) - 1),
    high = Math.ceil(Math.max(...ys) + 1);
  const x = (v: number) => 60 + (v / maxX) * 620;
  const y = (v: number) => 225 - ((v * 100 - low) / (high - low)) * 190;
  return (
    <figure className="chart">
      <figcaption>效率曲线 · 固定硬件负载扫描</figcaption>
      <svg viewBox="0 0 730 275" role="img" aria-label="效率与负载曲线">
        {[0, 1, 2, 3, 4].map((i) => (
          <g key={i}>
            <line
              x1="60"
              x2="680"
              y1={225 - i * 47.5}
              y2={225 - i * 47.5}
              stroke="#dce4e5"
            />
            <text x="5" y={229 - i * 47.5}>
              {(low + ((high - low) * i) / 4).toFixed(1)}%
            </text>
          </g>
        ))}
        <polyline
          fill="none"
          stroke="#16705c"
          strokeWidth="3"
          points={points.map((p) => `${x(p.x)},${y(p.y)}`).join(" ")}
        />
        {points.map((p, i) => (
          <circle key={i} cx={x(p.x)} cy={y(p.y)} r="4" fill="#16705c">
            <title>
              {p.x} p.u. / {(p.y * 100).toFixed(3)}%
            </title>
          </circle>
        ))}
        <text x="60" y="249">
          0
        </text>
        <text x="650" y="249">
          {maxX} p.u.
        </text>
        <text x="320" y="268">
          负载 Load
        </text>
      </svg>
    </figure>
  );
}

export default function Results({
  result,
  artifacts,
}: {
  result: Result | null;
  artifacts: Artifact[];
}) {
  const [tab, setTab] = useState(0);
  const [key, title, chinese] = sections[tab];
  const summary = result?.summary;
  const value: Json | undefined =
    key === "summary" && summary
      ? {
          candidate: summary.candidate ?? null,
          request: summary.request ?? null,
          status: summary.status ?? null,
        }
      : summary?.[key];
  const unavailable =
    value === undefined ||
    value === null ||
    (object(value) && value.available === false);
  const candidate =
    summary && object(summary.candidate) ? summary.candidate : {};
  return (
    <section className="results panel" aria-label="设计结果">
      <div className="panel-head">
        <div>
          <span className="eyebrow">DESIGN RESULTS</span>
          <h2>设计结果</h2>
        </div>
        <span className="tag">{result ? "已加载" : "等待设计"}</span>
      </div>
      <div className="tabs" role="tablist" aria-label="结果页面">
        {sections.map(([, name], i) => (
          <button
            id={`tab-${i}`}
            key={i}
            role="tab"
            aria-selected={tab === i}
            aria-controls="result-panel"
            onClick={() => setTab(i)}
          >
            {name}
          </button>
        ))}
      </div>
      <div
        id="result-panel"
        role="tabpanel"
        aria-labelledby={`tab-${tab}`}
        className="result-content"
      >
        <h3>
          {title} <small>{chinese}</small>
        </h3>
        {!result ? (
          <div className="empty">
            <span className="empty-mark">∿</span>
            <h3>从一次设计开始</h3>
            <p>填写左侧参数并运行设计。结果、警告与文件将在这里显示。</p>
          </div>
        ) : key === "files" ? (
          <>
            <p className="muted">下载当前任务生成的文件。</p>
            {artifacts.length === 0 ? (
              <p>此任务尚未生成可下载文件。</p>
            ) : (
              <ul className="file-list">
                {artifacts.map((a) => (
                  <li key={a.id}>
                    <div>
                      <strong>{a.name}</strong>
                      <small>
                        {a.media_type} · {(a.size / 1024).toFixed(1)} KB
                      </small>
                    </div>
                    {safeDownload(a.download_url) ? (
                      <a
                        className="button"
                        href={safeDownload(a.download_url)}
                        download={a.name}
                      >
                        下载
                      </a>
                    ) : (
                      <span>下载地址不可用</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
            <details>
              <summary>查看完整结果 JSON</summary>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </details>
          </>
        ) : unavailable ? (
          <div className="empty">
            <h3>此阶段尚未提供数据</h3>
            <p>当前任务没有 {title} 结果。这里不会显示估算或示例数据。</p>
          </div>
        ) : (
          <>
            {key === "summary" && (
              <div className="metrics">
                {[
                  ["inductance", "电感"],
                  ["capacitance", "电容"],
                  ["duty", "占空比"],
                  ["output_current", "输出电流"],
                ].map(([name, label]) => {
                  const v = candidate[name];
                  return (
                    <div key={name}>
                      <span>{label}</span>
                      <strong>{object(v) ? format(v.value) : "—"}</strong>
                      <small>{object(v) ? String(v.unit ?? "") : ""}</small>
                    </div>
                  );
                })}
              </div>
            )}
            {key === "waveform" && (
              <p className="notice">
                当前报告提供波形统计值，未包含时域采样序列。
              </p>
            )}
            {key === "efficiency_sweep" && <EfficiencyChart data={value!} />}
            <DataTable key={`${tab}-${result.job_id}`} value={value!} />
          </>
        )}
      </div>
    </section>
  );
}
