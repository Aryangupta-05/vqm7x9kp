"""Fetch only the two assignment datasets. Atomic cached chunks, retries, source receipts."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.analysis import validate_records, timestamp

BASE = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/'


def request_json(url: str, cache: Path, refresh: bool):
    if cache.exists() and not refresh:
        return json.loads(cache.read_text()), 'cache'
    for attempt in range(4):
        try:
            request = Request(url, headers={'Accept': 'application/json', 'User-Agent': 'Windward-assignment/1.0'})
            with urlopen(request, timeout=90) as response:
                content = response.read()
            data = json.loads(content)
            if not isinstance(data, list):
                raise ValueError('Incomplete/unexpected stream response: expected JSON array')
            temp = cache.with_suffix('.tmp')
            temp.write_bytes(content)
            os.replace(temp, cache)
            return data, 'network'
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            if isinstance(exc, HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 3:
                raise
            time.sleep(min(2 ** attempt, 8))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Refetch source chunks; default reuses successful cached requests')
    args = parser.parse_args()
    data_dir, cache_dir = ROOT/'data', ROOT/'.cache'/'elexon'
    data_dir.mkdir(exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    tasks = []
    # WINDFOR may include superseded/past targets. Explicit publication bounds are essential.
    # 72h leading window covers the observed forecast horizon and the first midnight decision.
    for kind, start, count in [('forecasts', date(2025,12,29),34), ('actuals',date(2026,1,2),31)]:
        for offset in range(count):
            day = start + timedelta(days=offset)
            if kind == 'actuals':
                endpoint = 'FUELHH/stream'
                params = dict(settlementDateFrom=str(day),settlementDateTo=str(day),fuelType='WIND')
            else:
                endpoint = 'WINDFOR/stream'
                params = dict(publishDateTimeFrom=f'{day}T00:00:00Z',publishDateTimeTo=f'{day+timedelta(days=1)}T00:00:00Z')
            tasks.append((kind,day,BASE+endpoint+'?'+urlencode(params)))
    def fetch(task):
        kind, day, url = task
        cache = cache_dir/f'{kind}-{day}.json'
        rows, origin = request_json(url, cache, args.refresh)
        print(f'{kind} {day}: {len(rows)} [{origin}]', flush=True)
        return kind, rows, dict(url=url, records=len(rows), sha256=hashlib.sha256(cache.read_bytes()).hexdigest(), day=str(day))
    records, receipts = dict(actuals=[],forecasts=[]), []
    with ThreadPoolExecutor(max_workers=3) as executor:
        for kind, rows, receipt in executor.map(fetch, tasks):
            records[kind].extend(rows)
            receipts.append(receipt)
    files = {}
    lower, upper = timestamp('2026-01-02T00:00:00Z'), timestamp('2026-02-02T00:00:00Z')
    for kind, rows in records.items():
        valid, quality = validate_records(rows, 'actual' if kind == 'actuals' else 'forecast')
        # Keep every revision for relevant delivery targets, never just today's latest.
        scoped = [r for r in valid if lower <= timestamp(r['startTime']) < upper]
        payload = gzip.compress(json.dumps(scoped,separators=(',',':')).encode(),mtime=0)
        name = f'{kind}.json.gz'
        (data_dir/name).write_bytes(payload)
        files[kind] = dict(name=name,records=len(scoped),sha256=hashlib.sha256(payload).hexdigest(),validation=quality,
                           target_start=min((r['startTime'] for r in scoped),default=None),target_end=max((r['startTime'] for r in scoped),default=None))
    digest = hashlib.sha256(''.join(f['sha256'] for f in files.values()).encode()).hexdigest()[:12]
    manifest = dict(snapshot_id=digest,retrieved_at=datetime.now(timezone.utc).isoformat(),
                    publication_window=dict(start='2025-12-29T00:00:00Z',end_exclusive='2026-02-01T00:00:00Z'),
                    delivery_window=dict(start='2026-01-02',end_inclusive='2026-02-01'),
                    observed_resolution_minutes=dict(actuals=30,forecasts=60),files=files,requests=receipts,
                    attribution='Contains BMRS data © Elexon Limited copyright and database right 2026.')
    manifest_temp = data_dir/'manifest.tmp'
    manifest_temp.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    os.replace(manifest_temp,data_dir/'manifest.json')
    print(json.dumps(files,indent=2))


if __name__ == '__main__':
    main()
