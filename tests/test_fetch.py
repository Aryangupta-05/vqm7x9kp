import importlib.util
from pathlib import Path
from urllib.error import HTTPError
import pytest

spec = importlib.util.spec_from_file_location('fetch_data', Path(__file__).resolve().parents[1]/'scripts/fetch_data.py')
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


class Reply:
    def __init__(self, payload): self.payload=payload
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return self.payload


def test_failed_response_is_not_cached_and_successful_retry_is(monkeypatch, tmp_path):
    attempts = []
    def fetch(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1: raise HTTPError('https://test',503,'busy',{},None)
        return Reply(b'[{"generation": 100}]')
    monkeypatch.setattr(fetcher,'urlopen',fetch)
    monkeypatch.setattr(fetcher.time,'sleep',lambda n: None)
    path = tmp_path/'chunk.json'
    data, origin = fetcher.request_json('https://test',path,False)
    assert len(attempts) == 2 and origin == 'network'
    assert fetcher.request_json('https://test',path,False) == (data,'cache')
    assert len(attempts) == 2


def test_wrong_payload_is_rejected_and_not_cached(monkeypatch,tmp_path):
    monkeypatch.setattr(fetcher,'urlopen',lambda *a,**k: Reply(b'{"data": []}'))
    path=tmp_path/'chunk.json'
    with pytest.raises(ValueError,match='expected JSON array'):
        fetcher.request_json('https://test',path,False)
    assert not path.exists()


def test_exhausted_api_failure_is_explicit(monkeypatch,tmp_path):
    def fail(*args,**kwargs): raise HTTPError('https://test',429,'rate limit',{},None)
    monkeypatch.setattr(fetcher,'urlopen',fail)
    monkeypatch.setattr(fetcher.time,'sleep',lambda n:None)
    with pytest.raises(HTTPError): fetcher.request_json('https://test',tmp_path/'chunk.json',False)
