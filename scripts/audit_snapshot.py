"""Independent decimal calculation against original cached source responses.

Does not import application selection/metric code. Run after fetch_data.py.
"""
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, getcontext
from pathlib import Path
from urllib.request import urlopen
import argparse

getcontext().prec = 32
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    args=parser.parse_args()
    cache=ROOT/'.cache'/'elexon'
    a=[r for p in cache.glob('actuals-*.json') for r in json.loads(p.read_text())]
    f=[r for p in cache.glob('forecasts-*.json') for r in json.loads(p.read_text())]
    assert a and f, 'Run scripts/fetch_data.py to retain original source response chunks for independent audit'
    actual={r['startTime']:Decimal(r['generation']) for r in a if r['fuelType']=='WIND'}
    errors, samples=[],[]
    for d in range(31):
        decision=date(2026,1,1)+timedelta(days=d)
        cutoff=f'{decision}T09:00:00Z'
        delivery=decision+timedelta(days=1)
        targets={}
        for r in f:
            if r['startTime'][:10]==str(delivery) and r['publishTime']<=cutoff:
                if r['startTime'] not in targets or r['publishTime']>targets[r['startTime']]['publishTime']:
                    targets[r['startTime']]=r
        for hour in range(24):
            t=f'{delivery}T{hour:02d}:00:00Z'
            t30=f'{delivery}T{hour:02d}:30:00Z'
            if t not in targets or t not in actual or t30 not in actual: continue
            chosen=targets[t]
            outturn=(actual[t]+actual[t30])/2
            error=Decimal(chosen['generation'])-outturn
            errors.append(error)
            if d in (0,14,30) and hour in (0,12,23):
                samples.append(dict(decision_date=str(decision),target=t,cutoff=cutoff,selected_publication=chosen['publishTime'],forecast_mw=chosen['generation'],actual_half_hours_mw=[float(actual[t]),float(actual[t30])],actual_mean_mw=float(outturn),error_mw=float(error)))
    n=Decimal(len(errors))
    independent=dict(matched=len(errors),mae_mw=float(sum(map(abs,errors))/n),rmse_mw=float((sum(e*e for e in errors)/n).sqrt()),bias_mw=float(sum(errors)/n))
    with urlopen(args.base_url+'/api/analysis',timeout=90) as response:
        app=json.load(response)
    for key,value in independent.items():
        assert abs(app['metrics'][key]-value)<1e-8,(key,value,app['metrics'][key])
    for sample in samples:
        row=next(r for r in app['intervals'] if r['start_time']==sample['target'])
        assert row['publish_time']==sample['selected_publication']
        assert row['error_mw']==sample['error_mw']
    report=dict(checked_at=datetime.now(timezone.utc).isoformat(),method='Independent Decimal arithmetic and original source response scan; no backend analysis imports',source_responses=dict(actuals=len(a),forecasts=len(f)),independent_metrics=independent,api_metrics=app['metrics'],sample_checks=samples,passed=True)
    (ROOT/'docs').mkdir(exist_ok=True)
    (ROOT/'docs'/'independent-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(independent,indent=2));print(f'PASS: {len(samples)} selected records independently checked; all metrics agree within 1e-8 MW')


if __name__=='__main__': main()
