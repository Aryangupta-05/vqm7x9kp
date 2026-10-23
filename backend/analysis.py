"""Pure historical selection and error analysis. All values are MW, never MWh."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from math import isfinite, sqrt
from zoneinfo import ZoneInfo

LONDON = ZoneInfo('Europe/London')
UTC = timezone.utc
FIRST_DECISION = date(2026, 1, 1)
LAST_DECISION = date(2026, 1, 31)


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('Timestamps must contain a timezone')
    return parsed.astimezone(UTC)


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')


def validate_records(rows: list, kind: str) -> tuple[list[dict], dict]:
    """Deduplicate exact keys. Conflicting values are excluded, never arbitrarily chosen."""
    if not isinstance(rows, list):
        raise ValueError('Expected a JSON array from the stream endpoint')
    records: dict[tuple, dict] = {}
    conflicts: set[tuple] = set()
    stats = dict(input=len(rows), invalid=0, duplicates=0, conflicts=0, other_fuel=0)
    for row in rows:
        try:
            if not isinstance(row, dict):
                raise ValueError('Not an object')
            if kind == 'actual' and row.get('fuelType') != 'WIND':
                stats['other_fuel'] += 1
                continue
            if row.get('dataset') != ('FUELHH' if kind == 'actual' else 'WINDFOR'):
                raise ValueError('Wrong dataset')
            target, published = timestamp(row['startTime']), timestamp(row['publishTime'])
            value = row['generation']
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError('Missing/non-numeric generation')
            if not isfinite(value) or value < 0:
                raise ValueError('Invalid generation')
            # Validate observed source resolutions, rather than rounding timestamps.
            if target.second or target.microsecond or target.minute not in ((0, 30) if kind == 'actual' else (0,)):
                raise ValueError('Unexpected target resolution')
            key = (target, published)
            normalized = dict(startTime=iso(target), publishTime=iso(published), generation=value,
                              dataset=row['dataset'])
            if kind == 'actual':
                normalized['fuelType'] = 'WIND'
            if key in records:
                if records[key]['generation'] != value:
                    conflicts.add(key)
                else:
                    stats['duplicates'] += 1
            else:
                records[key] = normalized
        except (KeyError, ValueError, TypeError, OverflowError):
            stats['invalid'] += 1
    for key in conflicts:
        del records[key]
    stats['conflicts'] = len(conflicts)
    stats['accepted'] = len(records)
    return sorted(records.values(), key=lambda r: (r['startTime'], r['publishTime'])), stats


def decision_cutoff(day: date, cutoff: str) -> datetime:
    if len(cutoff) != 5 or cutoff[2] != ':':
        raise ValueError('Decision time must be HH:MM')
    parsed = time.fromisoformat(cutoff)
    if parsed.tzinfo is not None:
        raise ValueError('Decision time is local Europe/London')
    return datetime.combine(day, parsed, LONDON).astimezone(UTC)


def delivery_hours(day: date) -> list[datetime]:
    """Calendar delivery date in London, half-open [00:00, next 00:00)."""
    first = datetime.combine(day, time.min, LONDON).astimezone(UTC)
    end = datetime.combine(day + timedelta(days=1), time.min, LONDON).astimezone(UTC)
    return [first + timedelta(hours=i) for i in range(int((end-first).total_seconds() / 3600))]


def metrics(rows: list[dict]) -> dict:
    matched = [r for r in rows if r['error_mw'] is not None]
    errors = [r['error_mw'] for r in matched]
    count = len(errors)
    return dict(
        expected=len(rows), matched=count,
        coverage_pct=round(100 * count / len(rows), 4) if rows else 0,
        forecast_available=sum(r['forecast_mw'] is not None for r in rows),
        actual_available=sum(r['actual_mw'] is not None for r in rows),
        mae_mw=sum(abs(e) for e in errors) / count if count else None,
        rmse_mw=sqrt(sum(e*e for e in errors) / count) if count else None,
        bias_mw=sum(errors) / count if count else None,
        max_abs_error_mw=max(map(abs, errors)) if count else None,
        mean_forecast_mw=sum(r['forecast_mw'] for r in matched) / count if count else None,
        mean_actual_mw=sum(r['actual_mw'] for r in matched) / count if count else None,
        overforecast_hours=sum(e > 0 for e in errors),
        underforecast_hours=sum(e < 0 for e in errors),
    )


def analyze(actuals: list[dict], forecasts: list[dict], start: date, end: date, cutoff: str) -> dict:
    if not FIRST_DECISION <= start <= end <= LAST_DECISION:
        raise ValueError('Choose decision dates from 1 through 31 January 2026, in order')
    decision_cutoff(start, cutoff)
    actuals, actual_quality = validate_records(actuals, 'actual')
    forecasts, forecast_quality = validate_records(forecasts, 'forecast')
    actual_by_time: dict[datetime, dict] = {}
    for row in actuals:
        target = timestamp(row['startTime'])
        if target not in actual_by_time or row['publishTime'] > actual_by_time[target]['publishTime']:
            actual_by_time[target] = row
    forecast_by_time: dict[datetime, list[dict]] = defaultdict(list)
    for row in forecasts:
        forecast_by_time[timestamp(row['startTime'])].append(row)
    intervals, days = [], []
    day = start
    while day <= end:
        delivery = day + timedelta(days=1)
        as_of = decision_cutoff(day, cutoff)
        daily = []
        for target in delivery_hours(delivery):
            candidates = forecast_by_time.get(target, [])
            eligible = [r for r in candidates if timestamp(r['publishTime']) <= as_of]
            selected = max(eligible, key=lambda r: timestamp(r['publishTime']), default=None)
            halves = [actual_by_time.get(target + timedelta(minutes=m)) for m in (0, 30)]
            actual = sum(r['generation'] for r in halves)/2 if all(halves) else None
            forecast = selected['generation'] if selected else None
            error = forecast - actual if forecast is not None and actual is not None else None
            row = dict(
                decision_date=day.isoformat(), delivery_date=delivery.isoformat(),
                start_time=iso(target), end_time=iso(target + timedelta(hours=1)),
                cutoff=iso(as_of), forecast_mw=forecast, actual_mw=actual, error_mw=error,
                publish_time=selected['publishTime'] if selected else None,
                forecast_age_hours=(as_of-timestamp(selected['publishTime'])).total_seconds()/3600 if selected else None,
                lead_hours=(target-as_of).total_seconds()/3600,
                actual_half_hours=[dict(start_time=r['startTime'], publish_time=r['publishTime'], generation_mw=r['generation']) if r else None for r in halves],
                eligible_revisions=len(eligible), excluded_future_revisions=len(candidates)-len(eligible),
                status='matched' if error is not None else ('missing_forecast_and_actual' if forecast is None and actual is None else 'missing_forecast' if forecast is None else 'missing_actual'),
            )
            daily.append(row)
        intervals.extend(daily)
        days.append(dict(decision_date=day.isoformat(), delivery_date=delivery.isoformat(), cutoff=iso(as_of), **metrics(daily)))
        day += timedelta(days=1)
    return dict(
        policy=dict(decision_start=start.isoformat(), decision_end=end.isoformat(), decision_time=cutoff,
                    timezone='Europe/London', delivery_convention='Next calendar day, 00:00–24:00 Europe/London',
                    alignment='Hourly forecast compared with mean of two half-hour FUELHH MW actuals',
                    error_sign='forecast minus actual; positive means wind was overforecast', unit='MW'),
        metrics=metrics(intervals), days=days, intervals=intervals,
        quality=dict(actual=actual_quality, forecast=forecast_quality),
    )
