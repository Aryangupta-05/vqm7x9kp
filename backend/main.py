import csv
import io
import logging
from datetime import date
from pathlib import Path
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from .analysis import analyze
from .data import load_snapshot

app = FastAPI(title='Windward | historical wind intelligence', version='1.0.0')
logger = logging.getLogger(__name__)


@app.get('/api/health')
def health():
    try:
        _, _, manifest = load_snapshot()
        return dict(status='ok', snapshot_retrieved_at=manifest['retrieved_at'], service='python-fastapi')
    except (OSError, ValueError, KeyError) as exc:
        logger.exception('Snapshot unavailable')
        raise HTTPException(503, 'Historical snapshot unavailable. Retry or rebuild it with scripts/fetch_data.py.') from exc


@lru_cache(maxsize=256)
def calculate(start: date, end: date, cutoff: str):
    actual, forecast, manifest = load_snapshot()
    result = analyze(actual, forecast, start, end, cutoff)
    result['source'] = dict(retrieved_at=manifest['retrieved_at'], snapshot_id=manifest['snapshot_id'],
                            mode='Reproducible Elexon historical snapshot',
                            files=manifest['files'], requests=len(manifest['requests']),
                            publication_window=manifest['publication_window'],
                            attribution='Contains BMRS data © Elexon Limited copyright and database right 2026.')
    return result


def get_analysis(start, end, cutoff):
    try:
        return calculate(start, end, cutoff)
    except ValueError as exc:
        if 'integrity' in str(exc) or 'manifest' in str(exc):
            logger.exception('Snapshot integrity check failed')
            raise HTTPException(503, 'Historical source integrity check failed. Please rebuild the snapshot.') from exc
        raise HTTPException(422, str(exc)) from exc
    except (OSError, KeyError) as exc:
        logger.exception('Analysis failed')
        raise HTTPException(503, 'Historical source snapshot unavailable. Please retry.') from exc


@app.get('/api/analysis')
def analysis(decision_start: date = date(2026, 1, 1), decision_end: date = date(2026, 1, 31),
             decision_time: str = Query('09:00', pattern=r'^([01]\d|2[0-3]):[0-5]\d$')):
    return get_analysis(decision_start, decision_end, decision_time)


@app.get('/api/export.csv')
def export(decision_start: date = date(2026, 1, 1), decision_end: date = date(2026, 1, 31),
           decision_time: str = Query('09:00', pattern=r'^([01]\d|2[0-3]):[0-5]\d$')):
    result = get_analysis(decision_start, decision_end, decision_time)
    output = io.StringIO(newline='')
    fields = ['decision_date', 'delivery_date', 'start_time', 'end_time', 'cutoff', 'forecast_mw',
              'actual_mw', 'error_mw', 'publish_time', 'eligible_revisions', 'excluded_future_revisions', 'status']
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(result['intervals'])
    return Response(output.getvalue(), media_type='text/csv', headers={
        'Content-Disposition': f'attachment; filename="windward-{decision_start}-{decision_end}.csv"'})


@app.get('/api/methodology')
def methodology():
    return dict(
        sources=[
            dict(title='Elexon FUELHH stream', url='https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream'),
            dict(title='Elexon WINDFOR stream', url='https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream'),
            dict(title='Official API schema', url='https://data.elexon.co.uk/swagger/v1/swagger.json'),
            dict(title='GB auction context (government, 2023)', url='https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1179971/recoupling-gb-auctions-for-cross-border-trade-with-eu-consultation-government-response.pdf'),
        ],
        limitation='National wind only. Demand, prices, embedded wind and the utility portfolio are not supplied. This is not a procurement quantity or trading recommendation.',
    )


dist = Path(__file__).resolve().parents[1] / 'dist'
if dist.is_dir():
    app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
