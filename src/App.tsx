import { useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Database,
  Info,
  Layers3,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  Wind,
} from "lucide-react";
import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Analysis, Interval, Metrics } from "./types";

const API = import.meta.env?.VITE_API_BASE || "";
type View = "desk" | "accuracy" | "method";
const fmt = (n: number | null | undefined, digits = 0) =>
  n == null
    ? "—"
    : n.toLocaleString("en-GB", {
        maximumFractionDigits: digits,
        minimumFractionDigits: digits,
      });
const signed = (n: number | null | undefined, digits = 0) =>
  n == null ? "—" : `${n > 0 ? "+" : ""}${fmt(n, digits)}`;
const dateLabel = (value: string, short = false) =>
  new Date(`${value}T12:00:00Z`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: short ? "short" : "long",
    timeZone: "Europe/London",
  });
const timeLabel = (value: string) =>
  new Date(value).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/London",
  });
const fullStamp = (value: string | null) =>
  value
    ? `${dateLabel(value.slice(0, 10), true)} ${timeLabel(value)} GMT`
    : "Unavailable";

function Metric({
  label,
  value,
  detail,
  icon,
  accent,
}: {
  label: string;
  value: string;
  detail: string;
  icon?: React.ReactNode;
  accent?: boolean;
}) {
  return (
    <article className={`metric ${accent ? "metric-accent" : ""}`}>
      <div className="metric-label">
        {label}
        {icon}
      </div>
      <div className="metric-value">
        {value}
        <span>MW</span>
      </div>
      <p>{detail}</p>
    </article>
  );
}

function Plot({ rows, error = false }: { rows: Interval[]; error?: boolean }) {
  const gradient = useId().replaceAll(":", "");
  const data = rows.map((r) => ({ ...r, hour: timeLabel(r.start_time) }));
  return (
    <div
      className="plot"
      role="img"
      aria-label={
        error
          ? "Hourly signed wind forecast error in megawatts. Values are also in the interval table."
          : "Hourly forecast and actual wind generation in megawatts. Values are also in the interval table."
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{ top: 20, right: 12, bottom: 4, left: 6 }}
        >
          <defs>
            <linearGradient id={gradient} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#43877d" stopOpacity={0.16} />
              <stop offset="100%" stopColor="#43877d" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            stroke="#e7ebe7"
            strokeDasharray="3 5"
            vertical={false}
          />
          <XAxis
            dataKey="hour"
            tick={{ fill: "#77847c", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            minTickGap={35}
          />
          <YAxis
            tick={{ fill: "#77847c", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={57}
            tickFormatter={(n) => `${fmt(n / 1000, 1)}k`}
          />
          <Tooltip
            contentStyle={{
              border: "1px solid #dbe3dc",
              borderRadius: 9,
              fontSize: 12,
              boxShadow: "0 8px 24px #1233",
            }}
            labelFormatter={(v) =>
              `${v}–${String((Number(String(v).slice(0, 2)) + 1) % 24).padStart(2, "0")}:00 GMT`
            }
            formatter={(v, name) => [`${fmt(Number(v), 1)} MW`, name]}
          />
          {error ? (
            <>
              <ReferenceLine y={0} stroke="#99aaa0" />
              <Bar
                dataKey="error_mw"
                name="Forecast − actual"
                fill="#ba8244"
                radius={[3, 3, 0, 0]}
                maxBarSize={23}
              />
            </>
          ) : (
            <>
              <Area
                type="linear"
                dataKey="actual_mw"
                name="Actual (hourly mean)"
                stroke="#24766a"
                strokeWidth={2.5}
                fill={`url(#${gradient})`}
                connectNulls={false}
              />
              <Line
                type="linear"
                dataKey="forecast_mw"
                name="Forecast at cutoff"
                stroke="#c49343"
                strokeWidth={2}
                strokeDasharray="6 5"
                dot={false}
                activeDot={{ r: 5 }}
                connectNulls={false}
              />
            </>
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function IntervalTable({ rows }: { rows: Interval[] }) {
  const [opened, setOpened] = useState<string | null>(null);
  return (
    <div className="table-scroll">
      <table>
        <caption className="sr-only">
          Hourly source values and forecast publication provenance
        </caption>
        <thead>
          <tr>
            <th>Delivery hour · GMT</th>
            <th>Forecast MW</th>
            <th>Actual MW</th>
            <th>Error MW</th>
            <th>Published before cutoff</th>
            <th>Source detail</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <Rows
              key={r.start_time}
              row={r}
              opened={opened === r.start_time}
              toggle={() =>
                setOpened(opened === r.start_time ? null : r.start_time)
              }
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Rows({
  row: r,
  opened,
  toggle,
}: {
  row: Interval;
  opened: boolean;
  toggle: () => void;
}) {
  return (
    <>
      <tr>
        <td>
          <strong>{timeLabel(r.start_time)}</strong>
          <span className="muted"> – {timeLabel(r.end_time)}</span>
        </td>
        <td>{fmt(r.forecast_mw)}</td>
        <td>{fmt(r.actual_mw, 1)}</td>
        <td>
          <span
            className={
              r.error_mw == null
                ? "muted"
                : r.error_mw > 0
                  ? "error-positive"
                  : "error-negative"
            }
          >
            {signed(r.error_mw, 1)}
          </span>
        </td>
        <td className="publication">{fullStamp(r.publish_time)}</td>
        <td>
          <button
            className="text-button"
            aria-expanded={opened}
            aria-label={`Inspect source for ${timeLabel(r.start_time)}`}
            onClick={toggle}
          >
            {opened ? "Close" : "Inspect"}
            <ChevronRight size={13} />
          </button>
        </td>
      </tr>
      {opened && (
        <tr className="detail-row">
          <td colSpan={6}>
            <div className="source-detail">
              <div>
                <b>Historical selection</b>
                <p>
                  Cutoff: {fullStamp(r.cutoff)}
                  <br />
                  {r.eligible_revisions} eligible revisions;{" "}
                  {r.excluded_future_revisions} later revisions excluded.
                  <br />
                  Selected: {fullStamp(r.publish_time)}
                </p>
              </div>
              <div>
                <b>Hourly actual calculation</b>
                <p>
                  {r.actual_half_hours.map((h, i) => (
                    <span key={i}>
                      {h
                        ? `${timeLabel(h.start_time)}: ${fmt(h.generation_mw)} MW (published ${fullStamp(h.publish_time)})`
                        : "Half-hour unavailable"}
                      <br />
                    </span>
                  ))}
                  Both present: mean of the two MW values. Otherwise excluded.
                </p>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function Method({ result }: { result: Analysis }) {
  return (
    <div className="method-grid">
      <article className="panel method-card">
        <span className="eyebrow">01 / THE DECISION</span>
        <h2>Rewind the information clock.</h2>
        <p>
          For every delivery hour, Windward selects the latest WINDFOR row with
          a publication time at or before that day’s historical decision cutoff.
          Later revisions never enter the score.
        </p>
        <div className="formula">
          publishTime ≤ decision cutoff
          <br />
          <span>then choose max(publishTime) per startTime</span>
        </div>
        <p>
          The default is <b>09:00 Europe/London</b>, a pilot policy ahead of the
          historical morning auction times documented by the UK government. It
          is adjustable and is not a universal market deadline.
        </p>
      </article>
      <article className="panel method-card">
        <span className="eyebrow">02 / THE DELIVERY WINDOW</span>
        <h2>January decisions, next-day delivery.</h2>
        <p>
          Decisions from <b>1–31 January 2026</b> cover calendar delivery dates{" "}
          <b>2 January–1 February</b>. The window is midnight to midnight in
          Europe/London, which is GMT in January.
        </p>
        <p>
          We use calendar days for this pilot; exchange products may use
          different boundaries, including a 23:00 power-day start. This does not
          reproduce an exchange order book.
        </p>
        <p>
          Adjacent December publication dates are fetched only to find eligible
          forecasts for early January decisions. All displayed delivery targets
          remain in scope.
        </p>
      </article>
      <article className="panel method-card">
        <span className="eyebrow">03 / LIKE-FOR-LIKE COMPARISON</span>
        <h2>Different resolutions. Explicit alignment.</h2>
        <p>
          Observed WINDFOR targets are hourly; FUELHH WIND values are 30-minute
          average MW. For target hour <b>t</b>, we derive an hourly actual as{" "}
          <b>(actual[t] + actual[t+30m]) / 2</b>. Both records must exist.
        </p>
        <p>
          This is a transparent comparison convention: the forecast’s hourly
          point is compared to an hourly mean actual. We do not claim these
          sources have identical measurement semantics, interpolate forecasts,
          or fill gaps with zero.
        </p>
        <p>
          Exact duplicate keys are removed. Conflicting values at the same
          target/publication key are excluded. Actuals use the latest available
          publication in the retrieved historical snapshot and are evaluated
          after delivery.
        </p>
      </article>
      <article className="panel method-card">
        <span className="eyebrow">04 / WHAT THE NUMBERS MEAN</span>
        <h2>One error sign. Three useful measures.</h2>
        <div className="formula">
          error = forecast − actual <span>(MW)</span>
        </div>
        <p>
          <b>MAE</b> = mean absolute error; typical error magnitude.
          <br />
          <b>RMSE</b> = square root of mean squared error; emphasizes larger
          misses.
          <br />
          <b>Bias</b> = mean signed error; positive means wind was overforecast.
        </p>
        <p>
          All metrics use matched eligible hourly records only, with equal
          one-hour weights. No percentage error metric is used, so zero actuals
          need no special denominator. Empty samples return no score.
        </p>
      </article>
      <article className="panel method-card method-wide">
        <div className="section-head">
          <div>
            <span className="eyebrow">05 / DATA RECEIPT</span>
            <h2>Real source data. Reproducible results.</h2>
          </div>
          <Database size={24} />
        </div>
        <p>
          Snapshot <code>{result.source.snapshot_id}</code> · retrieved{" "}
          {fullStamp(result.source.retrieved_at)} · {result.source.requests}{" "}
          bounded source requests. This fixed historical snapshot keeps the
          pilot usable during Elexon outages; it is not a live data feed. Python
          selects and calculates results on every new query.
        </p>
        <div className="receipt-grid">
          {Object.entries(result.source.files).map(([name, file]) => (
            <div key={name}>
              <b>
                {name}: {fmt(file.records)} source records
              </b>
              <code className="hash">SHA-256 {file.sha256}</code>
            </div>
          ))}
        </div>
        <p>
          Use <code>python scripts/fetch_data.py --refresh</code> to retrieve a
          new snapshot. Validation and retrieval receipts are saved in{" "}
          <code>data/manifest.json</code>. Refreshing data requires restarting
          the Python service.
        </p>
        <div className="source-links">
          <a
            href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream"
            target="_blank"
            rel="noreferrer"
          >
            FUELHH documentation <ArrowUpRight size={14} />
          </a>
          <a
            href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream"
            target="_blank"
            rel="noreferrer"
          >
            WINDFOR documentation <ArrowUpRight size={14} />
          </a>
          <a
            href="https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1179971/recoupling-gb-auctions-for-cross-border-trade-with-eu-consultation-government-response.pdf"
            target="_blank"
            rel="noreferrer"
          >
            Market timing context (2023) <ArrowUpRight size={14} />
          </a>
        </div>
      </article>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState<View>("desk");
  const formRef = useRef<HTMLFormElement>(null);
  const [query, setQuery] = useState({
    start: "2026-01-01",
    end: "2026-01-31",
    time: "09:00",
  });
  const [result, setResult] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [focus, setFocus] = useState("2026-01-15");
  const [tableVisible, setTableVisible] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setResult(null);
    const params = new URLSearchParams({
      decision_start: query.start,
      decision_end: query.end,
      decision_time: query.time,
    });
    fetch(`${API}/api/analysis?${params}`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(
            typeof body.detail === "string"
              ? body.detail
              : `Data request failed (${response.status}). Please retry.`,
          );
        }
        return response.json() as Promise<Analysis>;
      })
      .then((data) => {
        setResult(data);
        setFocus((day) =>
          data.days.some((d) => d.decision_date === day)
            ? day
            : data.days[0].decision_date,
        );
      })
      .catch((e: Error) => {
        if (e.name !== "AbortError") setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [query, retry]);
  function apply(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    // Read the committed native values too: date/time controls can commit on blur.
    const values = new FormData(e.currentTarget);
    const next = {
      start: String(values.get("start")),
      end: String(values.get("end")),
      time: String(values.get("time")),
    };
    if (next.start > next.end) {
      setError("The start decision date must be on or before the end date.");
      return;
    }
    setQuery(next);
  }
  const rows = result?.intervals.filter((r) => r.decision_date === focus) || [];
  const day = result?.days.find((d) => d.decision_date === focus);
  const m: Metrics | undefined = result?.metrics;
  const maxError = Math.max(
    ...(result?.days.map((d) => d.mae_mw || 0) || [1]),
    1,
  );
  const selectedIndex =
    result?.days.findIndex((d) => d.decision_date === focus) ?? -1;
  const worst = rows.reduce<Interval | null>(
    (best, r) =>
      r.error_mw != null &&
      (best?.error_mw == null || Math.abs(r.error_mw) > Math.abs(best.error_mw))
        ? r
        : best,
    null,
  );
  const dateRange = result
    ? `${dateLabel(result.policy.decision_start, true)}–${dateLabel(result.policy.decision_end, true)} 2026`
    : "January 2026";
  const exportUrl = `${API}/api/export.csv?${new URLSearchParams({ decision_start: query.start, decision_end: query.end, decision_time: query.time })}`;
  return (
    <div className="app-shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setView("desk");
          }}
          aria-label="Windward home"
        >
          <span className="brand-mark">
            <Wind size={24} />
          </span>
          windward<span className="brand-period">.</span>
        </a>
        <div className="workspace">
          <span className="workspace-icon">
            <Layers3 size={16} />
          </span>
          <div>
            Procurement workspace<small>GB · National wind</small>
          </div>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {(
            [
              { id: "desk", label: "Decision desk", icon: Wind },
              { id: "accuracy", label: "Accuracy review", icon: BarChart3 },
              { id: "method", label: "Data & methodology", icon: Database },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              className={`nav-item ${view === item.id ? "active" : ""}`}
              onClick={() => setView(item.id)}
              aria-current={view === item.id ? "page" : undefined}
            >
              <item.icon size={18} />
              {item.label}
              {view === item.id && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="status-dot" />
          HISTORICAL PILOT
          <h3>
            A clearer view
            <br />
            before the decision.
          </h3>
          <p>
            Replay what was known.
            <br />
            Understand what happened.
          </p>
          <div className="mini-wind">
            <Wind size={77} strokeWidth={0.8} />
          </div>
        </div>
        <div className="sidebar-bottom">
          <ShieldCheck size={16} />
          <span>
            Elexon source data<small>January 2026 edition</small>
          </span>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={12} />
            <span>
              {view === "desk"
                ? "Decision desk"
                : view === "accuracy"
                  ? "Accuracy review"
                  : "Data & methodology"}
            </span>
          </div>
          <div className="topbar-right">
            <span className="pilot-pill">PILOT v1.0</span>
            <span className="market-time">
              <Clock3 size={13} />
              Europe/London · GMT
            </span>
          </div>
        </header>
        <main id="main">
          <div className="page-heading">
            <div>
              <div className="eyebrow">DAY-AHEAD / WIND INTELLIGENCE</div>
              <h1>
                {view === "desk"
                  ? "Know the forecast. Understand the risk."
                  : view === "accuracy"
                    ? "Put forecast performance in perspective."
                    : "Every number has a source."}
              </h1>
              <p>
                {view === "desk"
                  ? "The wind outlook available at your decision time, measured against what actually happened."
                  : view === "accuracy"
                    ? "Review the size, direction, and daily pattern of historical forecast errors."
                    : "An auditable route from Elexon publications to historical decisions."}
              </p>
            </div>
            <div className="edition">
              <CalendarDays size={17} />
              <div>
                JANUARY 2026<small>Decision-date edition</small>
              </div>
            </div>
          </div>
          <form ref={formRef} className="filter-bar" onSubmit={apply}>
            <div className="filter-intro">
              <CalendarDays size={19} />
              <span>
                Decision window<small>Purchasing day, D−1</small>
              </span>
            </div>
            <label>
              From
              <input
                name="start"
                aria-label="First decision date"
                type="date"
                min="2026-01-01"
                max="2026-01-31"
                required
                defaultValue="2026-01-01"
              />
            </label>
            <span className="range-arrow">
              <ArrowRight size={15} />
            </span>
            <label>
              To
              <input
                name="end"
                aria-label="Last decision date"
                type="date"
                min="2026-01-01"
                max="2026-01-31"
                required
                defaultValue="2026-01-31"
              />
            </label>
            <div className="filter-divider" />
            <label>
              Decision time · GMT
              <input
                name="time"
                aria-label="Decision time in Europe London"
                type="time"
                required
                defaultValue="09:00"
              />
            </label>
            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? (
                <LoaderCircle size={15} className="spin" />
              ) : (
                <RefreshCw size={14} />
              )}
              Apply window
            </button>
          </form>
          <div className="context-row">
            <span>
              <ShieldCheck size={14} />
              As-of selection · later forecasts excluded
            </span>
            <button
              className="text-button"
              onClick={() => {
                formRef.current?.reset();
                setQuery({
                  start: "2026-01-01",
                  end: "2026-01-31",
                  time: "09:00",
                });
              }}
            >
              Reset to January <RefreshCw size={12} />
            </button>
          </div>
          {error && (
            <section className="error-box" role="alert">
              <Info size={20} />
              <div>
                <h2>We couldn’t load this analysis</h2>
                <p>{error}</p>
                <button
                  className="primary-button"
                  onClick={() => setRetry((n) => n + 1)}
                >
                  Retry data request
                </button>
              </div>
            </section>
          )}
          {loading && (
            <div className="loading-state" role="status">
              <LoaderCircle className="spin" size={26} />
              <h2>Replaying the historical decision window</h2>
              <p>Checking eligible publications and matching wind actuals…</p>
              <div className="loading-bars">
                <i />
                <i />
                <i />
              </div>
            </div>
          )}
          {!loading && result && (
            <>
              {view === "method" ? (
                <Method result={result} />
              ) : (
                <>
                  <div className="section-caption">
                    <span>
                      WINDOW PERFORMANCE{" "}
                      <span className="caption-date">/ {dateRange}</span>
                    </span>
                    <span className="coverage-pill">
                      <span className="status-dot" />
                      {fmt(m?.matched)} / {fmt(m?.expected)} matched hours ·{" "}
                      {fmt(m?.coverage_pct, 1)}%
                    </span>
                  </div>
                  <div className="metrics-grid">
                    <Metric
                      label="Mean absolute error"
                      value={fmt(m?.mae_mw)}
                      detail="Typical size of the hourly miss"
                      icon={<BarChart3 size={15} />}
                      accent
                    />
                    <Metric
                      label="Root mean squared error"
                      value={fmt(m?.rmse_mw)}
                      detail="Larger misses carry more weight"
                    />
                    <Metric
                      label="Forecast bias"
                      value={signed(m?.bias_mw)}
                      detail={
                        m?.bias_mw == null
                          ? "No matched hours to score"
                          : m.bias_mw === 0
                            ? "No net signed error"
                            : m.bias_mw > 0
                              ? "Wind overforecast on average"
                              : "Wind underforecast on average"
                      }
                    />
                    <Metric
                      label="Mean actual wind"
                      value={fmt(m?.mean_actual_mw)}
                      detail="Across matched delivery hours"
                      icon={<Wind size={16} />}
                    />
                  </div>
                  {m && m.matched < m.expected && (
                    <div className="warning-box" role="status">
                      <Info size={17} />
                      <span>
                        <b>
                          {m.expected - m.matched}{" "}
                          {m.expected - m.matched === 1 ? "hour" : "hours"}{" "}
                          excluded.
                        </b>{" "}
                        {m.expected - m.forecast_available} lack an eligible
                        forecast; {m.expected - m.actual_available} lack a
                        complete actual pair. These counts can overlap. No gap
                        is filled with zero.
                      </span>
                    </div>
                  )}
                  <div className="chart-layout">
                    <section className="panel chart-panel">
                      <div className="section-head">
                        <div>
                          <span className="eyebrow">
                            {view === "accuracy"
                              ? "ERROR PROFILE"
                              : "DELIVERY OUTLOOK"}
                          </span>
                          <h2>
                            {day
                              ? dateLabel(day.delivery_date)
                              : "Delivery day"}{" "}
                            <span className="year-muted">2026</span>
                          </h2>
                          <p>
                            Decision {dateLabel(focus, true)} at{" "}
                            {result.policy.decision_time} GMT ·{" "}
                            {day?.matched ?? 0}/{day?.expected ?? 24} matched
                            hours
                          </p>
                        </div>
                        <div className="day-controls">
                          <button
                            aria-label="Previous decision day"
                            disabled={selectedIndex <= 0}
                            onClick={() =>
                              setFocus(
                                result.days[selectedIndex - 1].decision_date,
                              )
                            }
                          >
                            <ChevronLeft size={16} />
                          </button>
                          <label className="sr-only" htmlFor="delivery-day">
                            Delivery date
                          </label>
                          <select
                            id="delivery-day"
                            value={focus}
                            onChange={(e) => setFocus(e.target.value)}
                          >
                            {result.days.map((d) => (
                              <option
                                value={d.decision_date}
                                key={d.decision_date}
                              >
                                {dateLabel(d.delivery_date, true)} delivery
                              </option>
                            ))}
                          </select>
                          <button
                            aria-label="Next decision day"
                            disabled={selectedIndex >= result.days.length - 1}
                            onClick={() =>
                              setFocus(
                                result.days[selectedIndex + 1].decision_date,
                              )
                            }
                          >
                            <ChevronRight size={16} />
                          </button>
                        </div>
                      </div>
                      <div className="chart-legend">
                        <span
                          className={
                            view === "accuracy"
                              ? "legend-error"
                              : "legend-actual"
                          }
                        >
                          {view === "accuracy"
                            ? "Forecast − actual"
                            : "Actual wind · hourly mean"}
                        </span>
                        {view !== "accuracy" && (
                          <span className="legend-forecast">
                            Forecast at cutoff
                          </span>
                        )}
                        <span className="legend-unit">MW</span>
                      </div>
                      <Plot rows={rows} error={view === "accuracy"} />
                      <div className="chart-footnote">
                        <Info size={13} />
                        <span>
                          Hourly comparison. Actual = mean of both half-hours.
                          Gaps remain visible.
                        </span>
                      </div>
                    </section>
                    <aside className="panel insight-panel">
                      <div className="insight-label">
                        <span className="status-dot" />
                        DECISION BRIEF
                      </div>
                      <h2>
                        The outlook,
                        <br />
                        with hindsight.
                      </h2>
                      <p className="brief-date">
                        For{" "}
                        {day
                          ? dateLabel(day.delivery_date)
                          : "selected delivery"}{" "}
                        delivery
                      </p>
                      <div className="brief-stat">
                        <span>Day’s typical error</span>
                        <strong>
                          {fmt(day?.mae_mw)} <small>MW</small>
                        </strong>
                      </div>
                      <div className="brief-stat">
                        <span>Direction of bias</span>
                        <strong>
                          {signed(day?.bias_mw)} <small>MW</small>
                        </strong>
                        <p>
                          {day?.bias_mw == null
                            ? "No matched sample."
                            : day.bias_mw > 0
                              ? "Forecast wind exceeded actual output."
                              : day.bias_mw < 0
                                ? "Actual wind exceeded the forecast."
                                : "No net signed error."}
                        </p>
                      </div>
                      <div className="brief-callout">
                        <ArrowUpRight size={17} />
                        <p>
                          {worst ? (
                            <>
                              Largest hourly miss:{" "}
                              <b>{fmt(Math.abs(worst.error_mw!))} MW</b> at{" "}
                              <b>{timeLabel(worst.start_time)} GMT</b>.
                            </>
                          ) : (
                            "No matched hours available for this day."
                          )}
                        </p>
                      </div>
                      <p className="brief-limit">
                        Historical errors describe this sample. They are not a
                        calibrated forecast uncertainty band.
                      </p>
                    </aside>
                  </div>
                  <section className="panel daily-panel">
                    <div className="section-head">
                      <div>
                        <span className="eyebrow">DAILY COMPARISON</span>
                        <h2>Find the days that deserve a closer look.</h2>
                        <p>
                          Select a decision day to inspect next-day delivery
                          above.
                        </p>
                      </div>
                      <span className="scale-label">
                        Lower error <i />
                        <i />
                        <i /> Higher error
                      </span>
                    </div>
                    <div className="day-grid">
                      {result.days.map((d) => (
                        <button
                          key={d.decision_date}
                          className={`day-tile ${d.decision_date === focus ? "selected" : ""}`}
                          aria-label={`${dateLabel(d.decision_date)} decision; ${dateLabel(d.delivery_date)} delivery; MAE ${fmt(d.mae_mw)} megawatts; ${d.matched} matched hours`}
                          aria-pressed={d.decision_date === focus}
                          onClick={() => setFocus(d.decision_date)}
                        >
                          <span>{Number(d.decision_date.slice(-2))}</span>
                          <i
                            style={{
                              background:
                                d.mae_mw == null
                                  ? "#d8ddda"
                                  : `rgba(40,116,96,${0.12 + (0.7 * d.mae_mw) / maxError})`,
                            }}
                          />
                          <small>
                            {d.mae_mw == null ? "No data" : fmt(d.mae_mw)}
                          </small>
                        </button>
                      ))}
                    </div>
                    <div className="daily-footer">
                      <span>
                        January decision dates · cell values = daily MAE in MW
                      </span>
                      <span>Delivery is the following calendar day</span>
                    </div>
                  </section>
                  <section className="panel interval-panel">
                    <div className="section-head">
                      <div>
                        <span className="eyebrow">SOURCE-LEVEL INSPECTION</span>
                        <h2>Follow the forecast back to its publication.</h2>
                        <p>
                          {day ? dateLabel(day.delivery_date) : ""} delivery ·
                          signed error = forecast − actual
                        </p>
                      </div>
                      <div className="button-group">
                        <a className="secondary-button" href={exportUrl}>
                          <ArrowDownToLine size={14} />
                          Export window CSV
                        </a>
                        <button
                          className="secondary-button"
                          onClick={() => setTableVisible((v) => !v)}
                          aria-expanded={tableVisible}
                        >
                          {tableVisible ? "Hide" : "Show"} {rows.length} hours
                        </button>
                      </div>
                    </div>
                    {tableVisible && <IntervalTable rows={rows} />}
                  </section>
                </>
              )}
              <div className="scope-note">
                <Info size={16} />
                <p>
                  <b>One part of the procurement picture.</b> National wind data
                  helps quantify forecast risk. Demand and the utility’s other
                  generation are not provided, so Windward does not calculate an
                  exact additional purchase requirement.
                </p>
                <button
                  className="text-button"
                  onClick={() => setView("method")}
                >
                  Read methodology <ArrowRight size={14} />
                </button>
              </div>
              <footer>
                <span>{result.source.attribution}</span>
                <span>
                  <Check size={12} /> Snapshot {result.source.snapshot_id} ·
                  retrieved{" "}
                  {dateLabel(result.source.retrieved_at.slice(0, 10), true)}
                </span>
              </footer>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
