"""Read a reproducible historical source snapshot, checking integrity before analysis."""
import gzip
import hashlib
import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'


@lru_cache(maxsize=1)
def load_snapshot():
    manifest = json.loads((DATA_DIR / 'manifest.json').read_text(encoding='utf-8'))
    loaded = {}
    for kind in ('actuals', 'forecasts'):
        entry = manifest['files'][kind]
        raw = (DATA_DIR / entry['name']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError(f'{kind} snapshot integrity check failed')
        loaded[kind] = json.loads(gzip.decompress(raw))
        if len(loaded[kind]) != entry['records']:
            raise ValueError(f'{kind} snapshot count does not match manifest')
    return loaded['actuals'], loaded['forecasts'], manifest
