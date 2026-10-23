export type Metrics = {
  expected: number;
  matched: number;
  coverage_pct: number;
  forecast_available: number;
  actual_available: number;
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  max_abs_error_mw: number | null;
  mean_forecast_mw: number | null;
  mean_actual_mw: number | null;
  overforecast_hours: number;
  underforecast_hours: number;
};
export type Day = Metrics & {
  decision_date: string;
  delivery_date: string;
  cutoff: string;
};
export type Interval = {
  decision_date: string;
  delivery_date: string;
  start_time: string;
  end_time: string;
  cutoff: string;
  forecast_mw: number | null;
  actual_mw: number | null;
  error_mw: number | null;
  publish_time: string | null;
  forecast_age_hours: number | null;
  lead_hours: number;
  eligible_revisions: number;
  excluded_future_revisions: number;
  status: string;
  actual_half_hours: ({
    start_time: string;
    publish_time: string;
    generation_mw: number;
  } | null)[];
};
export type Analysis = {
  policy: {
    decision_start: string;
    decision_end: string;
    decision_time: string;
    timezone: string;
    delivery_convention: string;
    alignment: string;
    error_sign: string;
    unit: string;
  };
  metrics: Metrics;
  days: Day[];
  intervals: Interval[];
  quality: Record<string, Record<string, number>>;
  source: {
    retrieved_at: string;
    snapshot_id: string;
    mode: string;
    requests: number;
    publication_window: { start: string; end_exclusive: string };
    files: Record<string, { records: number; sha256: string }>;
    attribution: string;
  };
};
