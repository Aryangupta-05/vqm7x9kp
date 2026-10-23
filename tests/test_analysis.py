from datetime import date
from math import sqrt

import pytest

from backend.analysis import analyze, decision_cutoff, delivery_hours, timestamp, validate_records


def forecast(value=100, published='2026-01-01T07:30:00Z', target='2026-01-02T00:00:00Z'):
    return dict(dataset='WINDFOR', startTime=target, publishTime=published, generation=value)


def actual(value=80, target='2026-01-02T00:00:00Z', published='2026-01-02T01:00:00Z'):
    return dict(dataset='FUELHH', fuelType='WIND', startTime=target, publishTime=published, generation=value)


def run(a=None, f=None, start=date(2026, 1, 1), end=date(2026, 1, 1), cutoff='09:00'):
    return analyze(a or [], f or [], start, end, cutoff)


def pair(first=80, second=120):
    return [actual(first), actual(second, '2026-01-02T00:30:00Z')]


def test_future_revision_excluded_and_latest_eligible_selected_including_equality():
    result = run(pair(), [forecast(90), forecast(105, '2026-01-01T09:00:00Z'), forecast(999, '2026-01-01T09:00:01Z')])
    row = result['intervals'][0]
    assert row['forecast_mw'] == 105
    assert row['publish_time'] == row['cutoff']
    assert row['excluded_future_revisions'] == 1
    assert row['eligible_revisions'] == 2


def test_selection_is_per_target_not_just_latest_file():
    result = run([], [forecast(100), forecast(200, target='2026-01-02T01:00:00Z', published='2026-01-01T08:00:00Z')])
    assert [r['forecast_mw'] for r in result['intervals'][:2]] == [100, 200]


def test_unordered_input_gives_same_selection():
    f = [forecast(500, '2026-01-01T11:30:00Z'), forecast(90), forecast(110, '2026-01-01T08:30:00Z')]
    assert run(pair(), f) == run(list(reversed(pair())), list(reversed(f)))


def test_timestamp_offsets_normalize_and_match():
    f = [forecast(90, target='2026-01-02T01:00:00+01:00')]
    assert run(pair(), f)['intervals'][0]['error_mw'] == -10


def test_naive_timestamps_rejected():
    with pytest.raises(ValueError, match='timezone'):
        timestamp('2026-01-02T00:00:00')
    rows, stats = validate_records([forecast(target='2026-01-02T00:00:00')], 'forecast')
    assert rows == [] and stats['invalid'] == 1


def test_hourly_mean_requires_both_halves_no_zero_fill():
    result = run([actual(80)], [forecast(100)])
    assert result['intervals'][0]['actual_mw'] is None
    assert result['intervals'][0]['forecast_mw'] == 100
    assert result['metrics']['matched'] == 0
    assert result['metrics']['mae_mw'] is None
    assert result['intervals'][0]['status'] == 'missing_actual'


def test_metrics_use_matched_hours_only_and_error_sign_is_forecast_minus_actual():
    a = pair(60, 100) + [actual(40, '2026-01-02T01:00:00Z'), actual(80, '2026-01-02T01:30:00Z')]
    f = [forecast(100), forecast(20, target='2026-01-02T01:00:00Z'), forecast(999, target='2026-01-02T02:00:00Z')]
    m = run(a, f)['metrics']
    assert m['matched'] == 2 and m['expected'] == 24
    assert m['mae_mw'] == 30
    assert m['rmse_mw'] == sqrt(1000)
    assert m['bias_mw'] == -10
    assert m['coverage_pct'] == pytest.approx(100*2/24, abs=.0001)
    assert m['mean_actual_mw'] == 70
    assert m['overforecast_hours'] == m['underforecast_hours'] == 1


def test_zero_actual_is_valid_and_not_treated_as_missing():
    r = run(pair(0, 0), [forecast(10)])
    assert r['metrics']['matched'] == 1
    assert r['metrics']['mae_mw'] == 10


def test_no_eligible_forecast_stays_missing():
    r = run(pair(), [forecast(100, '2026-01-01T09:30:00Z')])
    assert r['intervals'][0]['forecast_mw'] is None
    assert r['intervals'][0]['status'] == 'missing_forecast'
    assert r['metrics']['coverage_pct'] == 0


def test_duplicate_keys_dont_double_weight_and_conflicts_are_excluded():
    rows, stats = validate_records([forecast(10), forecast(10), forecast(20)], 'forecast')
    assert rows == []
    assert stats['duplicates'] == 1 and stats['conflicts'] == 1
    m = run(pair()+pair(), [forecast(), forecast()])['metrics']
    assert m['matched'] == 1


@pytest.mark.parametrize('value', [None, True, float('nan'), float('inf'), -1, '100'])
def test_invalid_generation_rejected(value):
    assert validate_records([forecast(value)], 'forecast')[1]['invalid'] == 1


def test_only_wind_and_expected_resolution_used():
    gas = actual(); gas['fuelType'] = 'CCGT'
    assert validate_records([gas], 'actual')[1]['other_fuel'] == 1
    assert validate_records([forecast(target='2026-01-02T00:30:00Z')], 'forecast')[1]['invalid'] == 1
    assert validate_records([actual(target='2026-01-02T00:15:00Z')], 'actual')[1]['invalid'] == 1


def test_actual_revisions_use_latest_retrieved_value():
    a = pair() + [actual(180, published='2026-01-03T00:00:00Z')]
    assert run(a, [forecast()])['intervals'][0]['actual_mw'] == 150


def test_january_scope_includes_february_delivery_and_excludes_jan1_delivery():
    r = run(start=date(2026,1,1),end=date(2026,1,31))
    assert len(r['intervals']) == 31*24
    assert r['intervals'][0]['start_time'] == '2026-01-02T00:00:00Z'
    assert r['intervals'][-1]['end_time'] == '2026-02-02T00:00:00Z'
    assert r['days'][-1]['delivery_date'] == '2026-02-01'


def test_end_boundary_exclusive_and_midnight_publication_eligible():
    r = run([], [forecast(70,'2026-01-01T00:00:00Z'),forecast(30,target='2026-01-03T00:00:00Z')],cutoff='00:00')
    assert r['intervals'][0]['forecast_mw'] == 70
    assert len(r['intervals']) == 24
    assert all(row['forecast_mw'] != 30 for row in r['intervals'])


@pytest.mark.parametrize('start,end', [(date(2025,12,31),date(2026,1,2)),(date(2026,1,1),date(2026,2,1)),(date(2026,1,3),date(2026,1,2))])
def test_invalid_date_range_rejected(start,end):
    with pytest.raises(ValueError,match='January'):
        run(start=start,end=end)


@pytest.mark.parametrize('cutoff', ['24:00','9:00','09:00:30','09:60','xx:yy'])
def test_invalid_cutoffs_rejected(cutoff):
    with pytest.raises(ValueError):
        decision_cutoff(date(2026,1,1), cutoff)


def test_london_calendar_day_and_aware_utc_including_dst():
    assert len(delivery_hours(date(2026,3,29))) == 23
    assert len(delivery_hours(date(2026,10,25))) == 25
    assert decision_cutoff(date(2026,1,1),'09:00').isoformat() == '2026-01-01T09:00:00+00:00'
