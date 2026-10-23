import csv
import io
from datetime import date

from fastapi.testclient import TestClient
from backend.main import app
from backend.data import load_snapshot
from backend.analysis import analyze, timestamp

client = TestClient(app)


def test_real_snapshot_health_and_full_window():
    assert client.get('/api/health').json()['service'] == 'python-fastapi'
    response = client.get('/api/analysis')
    assert response.status_code == 200
    r = response.json()
    assert r['metrics']['expected'] == 744
    assert r['metrics']['matched'] == 744
    assert r['source']['files']['actuals']['records'] == 1488
    assert all(timestamp(i['publish_time']) <= timestamp(i['cutoff']) for i in r['intervals'] if i['publish_time'])


def test_real_cutoff_change_changes_selection_but_never_leaks_future():
    early = client.get('/api/analysis?decision_start=2026-01-01&decision_end=2026-01-01&decision_time=09:00').json()
    late = client.get('/api/analysis?decision_start=2026-01-01&decision_end=2026-01-01&decision_time=10:00').json()
    assert early['intervals'][0]['publish_time'] == '2026-01-01T07:30:00Z'
    assert late['intervals'][0]['publish_time'] == '2026-01-01T09:30:00Z'


def test_api_validates_dates_and_cutoff():
    for query in ['decision_start=2026-02-01','decision_end=2025-12-31','decision_time=25:00','decision_time=09:00:30','decision_start=bad-date']:
        assert client.get('/api/analysis?'+query).status_code == 422


def test_csv_matches_api_and_escapes_empty_values():
    query = '?decision_start=2026-01-31&decision_end=2026-01-31'
    response = client.get('/api/export.csv'+query)
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert response.status_code == 200 and len(rows) == 24
    assert rows[0]['delivery_date'] == '2026-02-01'
    expected = client.get('/api/analysis'+query).json()['intervals'][0]
    assert float(rows[0]['actual_mw']) == expected['actual_mw']


def test_missing_real_source_records_excluded_from_metrics():
    actuals, forecasts, _ = load_snapshot()
    partial = [r for r in actuals if r['startTime'] != '2026-01-02T00:30:00Z']
    r = analyze(partial, forecasts, date(2026,1,1),date(2026,1,1),'09:00')
    assert r['metrics']['matched'] == 23
    assert r['intervals'][0]['actual_mw'] is None


def test_unavailable_data_is_service_error(monkeypatch):
    import backend.main as main
    main.calculate.cache_clear()
    def missing():
        raise FileNotFoundError('test unavailable snapshot')
    with monkeypatch.context() as context:
        context.setattr(main, 'load_snapshot', missing)
        assert client.get('/api/analysis').status_code == 503
        assert client.get('/api/health').status_code == 503
    main.calculate.cache_clear()
