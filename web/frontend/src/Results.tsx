import { useEffect, useState } from "react";
import { artifactBlob, safeDownload, type Artifact, type Json, type Result } from "./api";

function ArtifactDownload({ artifact }: { artifact: Artifact }) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  if (!safeDownload(artifact.download_url)) return <span>下载地址不可用</span>;
  return <button className="button" disabled={busy} onClick={async () => {
    setBusy(true); setFailed(false);
    try {
      const blob = await artifactBlob(artifact.download_url);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url; link.download = artifact.name; link.click();
      URL.revokeObjectURL(url);
    } catch { setFailed(true); }
    finally { setBusy(false); }
  }}>{failed ? "下载失败，重试" : busy ? "正在下载…" : "下载"}</button>;
}

function ArtifactImage({ artifact, alt }: { artifact: Artifact; alt: string }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let active = true;
    let objectUrl = "";
    artifactBlob(artifact.download_url).then((blob) => {
      if (!active) return;
      objectUrl = URL.createObjectURL(blob);
      setUrl(objectUrl);
    }).catch(() => setUrl(""));
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [artifact.download_url]);
  return url ? <figure className="chart"><img className="artifact-preview" src={url} alt={alt} /></figure> : null;
}

const sections = [
  ["summary", "Summary", "设计摘要"],
  ["hardware", "Hardware Overview", "硬件总览"],
  ["waveform", "Waveforms", "波形"],
  ["stress", "Stress", "电气应力"],
  ["devices", "Devices", "半导体"],
  ["capacitor", "Capacitor", "电容"],
  ["capacitor_pf", "Capacitor PF", "电容 Pareto"],
  ["magnetic", "Magnetics", "磁性器件"],
  ["inductor_pf", "Inductor PF", "磁件 Pareto"],
  ["inductor", "Inductor", "电感综合"],
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

const colors = ["#16705c", "#d06b37", "#4a67a1", "#9a4f8f", "#768638", "#2b8aa0", "#b24b4b", "#6558a5"];

function WaveformChannels({ data }: { data: Json }) {
  if (!object(data) || !object(data.samples) || !Array.isArray(data.samples.time_s)) return null;
  const times = data.samples.time_s.filter((item): item is number => typeof item === "number" && Number.isFinite(item));
  const channels = Object.entries(data.samples)
    .filter(([name, values]) => name !== "time_s" && Array.isArray(values) && values.length === times.length)
    .slice(0, 8)
    .map(([name, values]) => ({ name, values: (values as Json[]).map(number) }))
    .filter((channel) => channel.values.every((item) => item !== undefined)) as { name: string; values: number[] }[];
  if (times.length < 2 || channels.length === 0) return null;
  const sampleIndexes = Array.from({ length: Math.min(times.length, 320) }, (_, index) =>
    Math.min(times.length - 1, Math.floor(index * (times.length - 1) / Math.max(Math.min(times.length, 320) - 1, 1))),
  );
  const minTime = times[0], span = Math.max(times[times.length - 1] - minTime, Number.EPSILON);
  const laneHeight = 72;
  return <figure className="chart waveform-channels">
    <figcaption>多通道工作点波形 · 与当前固定硬件结果绑定</figcaption>
    <svg viewBox={`0 0 760 ${channels.length * laneHeight + 35}`} role="img" aria-label="多通道工作点波形">
      {channels.map((channel, lane) => {
        const low = Math.min(...channel.values), high = Math.max(...channel.values);
        const range = Math.max(high - low, Number.EPSILON);
        const top = lane * laneHeight + 10;
        const points = sampleIndexes.map((index) => {
          const x = 150 + ((times[index] - minTime) / span) * 590;
          const y = top + 48 - ((channel.values[index] - low) / range) * 42;
          return `${x},${y}`;
        }).join(" ");
        return <g key={channel.name}>
          <line x1="150" x2="740" y1={top + 48} y2={top + 48} stroke="#dce4e5" />
          <text x="5" y={top + 25}>{channel.name.replace(/_/g, " ")}</text>
          <polyline fill="none" stroke={colors[lane % colors.length]} strokeWidth="1.8" points={points} />
          <text x="82" y={top + 8}>{format(high)}</text><text x="82" y={top + 51}>{format(low)}</text>
        </g>;
      })}
      <text x="150" y={channels.length * laneHeight + 25}>{format(minTime)} s</text>
      <text x="680" y={channels.length * laneHeight + 25}>{format(times[times.length - 1])} s</text>
    </svg>
  </figure>;
}

function ScatterChart({ title, points, xKey, yKey, labelKey = "design_id" }: {
  title: string; points: Json | undefined; xKey: string; yKey: string; labelKey?: string;
}) {
  if (!Array.isArray(points)) return null;
  const values = points.filter(object).map((point) => ({
    x: number(point[xKey]), y: number(point[yKey]),
    label: String(point[labelKey] ?? point.part_number ?? "candidate"),
    recommended: point.recommended === true,
  })).filter((point): point is { x: number; y: number; label: string; recommended: boolean } => point.x !== undefined && point.y !== undefined);
  if (values.length === 0) return null;
  const xs = values.map((point) => point.x), ys = values.map((point) => point.y);
  const xMin = Math.min(...xs), xSpan = Math.max(Math.max(...xs) - xMin, Number.EPSILON);
  const yMin = Math.min(...ys), ySpan = Math.max(Math.max(...ys) - yMin, Number.EPSILON);
  return <figure className="chart pareto-chart">
    <figcaption>{title}</figcaption>
    <svg viewBox="0 0 720 300" role="img" aria-label={title}>
      <line x1="70" x2="690" y1="250" y2="250" stroke="#829398" />
      <line x1="70" x2="70" y1="20" y2="250" stroke="#829398" />
      {values.map((point, index) => <circle key={`${point.label}-${index}`}
        cx={70 + ((point.x - xMin) / xSpan) * 620}
        cy={250 - ((point.y - yMin) / ySpan) * 220}
        r={point.recommended ? 7 : 4} fill={point.recommended ? "#d06b37" : "#16705c"}>
        <title>{point.label}: {xKey}={format(point.x)}, {yKey}={format(point.y)}</title>
      </circle>)}
      <text x="320" y="285">{xKey.replace(/_/g, " ")}</text>
      <text x="8" y="18">{yKey.replace(/_/g, " ")}</text>
    </svg>
  </figure>;
}

function CapacitorPareto({ data }: { data: Json }) {
  if (!object(data)) return null;
  return <div className="specialized-grid">
    {["input", "output"].map((side) => {
      const value = object(data[side]) ? data[side] : {};
      return <ScatterChart key={side} title={`${side === "input" ? "输入" : "输出"}电容 Pareto · 体积/损耗`}
        points={value.pareto} xKey="volume_cm3" yKey="loss_w" labelKey="part_number" />;
    })}
  </div>;
}

function GeometryComparison({ data }: { data: Json }) {
  if (!object(data) || !Array.isArray(data.targets)) return null;
  const targets = data.targets.filter(object).filter((target) => object(target.layout));
  if (targets.length === 0) return null;
  return <figure className="chart geometry-comparison">
    <figcaption>磁件 2D/3D 几何比较 · Min-volume / Min-loss / Recommended</figcaption>
    <div className="geometry-grid" role="img" aria-label="磁件 2D/3D 几何比较">
      {targets.map((target, index) => {
        const layout = target.layout as Record<string, Json>;
        const outerW = number(layout.outer_width_mm) || 1, outerH = number(layout.outer_height_mm) || 1;
        const windowW = Math.min(number(layout.window_width_mm) || outerW * .4, outerW * .8);
        const windowH = Math.min(number(layout.window_height_mm) || outerH * .4, outerH * .8);
        const x = 15 + (outerW - windowW) / outerW * 50;
        const y = 15 + (outerH - windowH) / outerH * 35;
        const w = windowW / outerW * 100, h = windowH / outerH * 70;
        return <div key={`${String(target.role)}-${index}`}>
          <strong>{String(target.label || target.role)}</strong>
          <svg viewBox="0 0 150 120">
            <rect x="15" y="15" width="100" height="70" rx="5" fill="#9fb3af" stroke="#345b55" />
            <rect x={x} y={y} width={w} height={h} fill="#fff" stroke="#345b55" />
            <path d="M115 15 L135 30 L135 98 L115 85 Z M15 85 L35 100 L135 98 L115 85 Z" fill="#728f89" opacity=".65" />
            <rect x="45" y="35" width="40" height="30" fill="none" stroke="#d06b37" strokeWidth="5" />
          </svg>
          <small>{format(layout.overall_width_mm)} × {format(layout.overall_height_mm)} × {format(layout.overall_depth_mm)} mm</small>
          <small>{String(layout.core_name || "")} · {format(layout.turns)} turns</small>
        </div>;
      })}
    </div>
  </figure>;
}

function EfficiencySpecialized({ data }: { data: Json }) {
  if (!object(data)) return null;
  return <>
    <EfficiencyChart data={data} />
    <ScatterChart title="损耗分解 · 固定硬件负载扫描" points={data.points} xKey="load_ratio" yKey="total_loss" labelKey="load_ratio" />
    <ScatterChart title="功率因数扫描 · 效率" points={data.pf_points} xKey="power_factor" yKey="efficiency" labelKey="power_factor" />
  </>;
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
      : key === "devices" && summary && object(summary.hardware)
        ? summary.hardware.semiconductor
      : key === "capacitor_pf"
        ? summary?.capacitor
      : key === "inductor_pf"
        ? summary?.magnetic
      : key === "inductor" && summary
        ? {
            magnetic: summary.magnetic ?? null,
            loss: summary.loss ?? null,
            thermal: summary.thermal ?? null,
            geometry: summary.geometry ?? null,
          }
      : summary?.[key];
  const unavailable =
    value === undefined ||
    value === null ||
    (object(value) && (value.available === false ||
      ["blocked", "unavailable", "not_available", "not_evaluated", "failed", "not_applicable"].includes(String(value.status))));
  const stageWarnings = object(value) && object(value.metadata) && Array.isArray(value.metadata.warnings)
    ? value.metadata.warnings.map(format) : [];
  const previewStage = key === "capacitor_pf" ? "capacitor" : key === "inductor_pf" || key === "inductor" ? "magnetic" : key;
  const preview = artifacts.find((a) => a.stage === previewStage && a.media_type === "image/png");
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
                        {a.stage ? ` · 阶段：${a.stage}` : ""}
                        {a.schema_version ? ` · 格式版本：${a.schema_version}` : ""}
                        {a.sha256 ? <><br /><code className="checksum">SHA-256: {a.sha256}</code></> : ""}
                      </small>
                    </div>
                    <ArtifactDownload artifact={a} />
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
            <h3>{object(value) && value.status === "blocked" ? "此阶段被阻塞" : "此阶段尚未提供数据"}</h3>
            <p>{object(value) && value.blocked_reason ? format(value.blocked_reason) : `当前任务没有可用的 ${title} 结果。`}</p>
            {stageWarnings.map((warning, i) => <p key={i}>{warning}</p>)}
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
            {key === "waveform" && !(object(value) && object(value.samples)) && (
              <p className="notice">
                当前报告提供波形统计值，未包含时域采样序列。
              </p>
            )}
            {key === "waveform" && <WaveformChannels data={value!} />}
            {key === "capacitor_pf" && <CapacitorPareto data={value!} />}
            {key === "inductor_pf" && object(value) && <ScatterChart title="磁件候选比较 · 体积/损耗" points={value.candidate_comparison} xKey="volume_m3" yKey="loss_w" />}
            {key === "inductor" && summary?.geometry && <GeometryComparison data={summary.geometry} />}
            {key === "geometry" && <GeometryComparison data={value!} />}
            {key === "efficiency_sweep" && <EfficiencySpecialized data={value!} />}
            {preview && safeDownload(preview.download_url) && <ArtifactImage artifact={preview} alt={`${title} · 当前任务计算曲线`} />}
            {stageWarnings.map((warning, i) => <p className="notice" key={i}>{warning}</p>)}
            <DataTable key={`${tab}-${result.job_id}`} value={object(value) ? Object.fromEntries(Object.entries(value).filter(([name]) =>
              !["samples", "pareto", "candidate_comparison"].includes(name),
            )) : value!} />
          </>
        )}
      </div>
    </section>
  );
}
