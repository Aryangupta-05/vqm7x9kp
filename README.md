# Windward

A historical decision desk for a UK utility’s day-ahead wind procurement team. Replay the national wind forecast available at a chosen decision time, then compare it with actual output. The pilot uses **only Elexon WINDFOR and FUELHH (WIND)** generation data.

**Application:** https://vqm7x9kp.vercel.app (deployment verification recorded in [the evidence checklist](docs/VERIFICATION.md)).

**Repository:** https://github.com/Aryangupta-05/vqm7x9kp

**Video:** [Unlisted customer presentation and technical review](https://youtu.be/xoeCAQSuw3M) — **7:00**, with two 3:30 parts. This is a **silent visual walkthrough**, published without voice-over at the author's explicit request. It uses verified app views and actual source/design panels, with scene headings and key points; optional narration text is in [the script](docs/VIDEO_SCRIPT.md). Unlisted visibility and anonymous availability were verified in [the video evidence](docs/youtube-verification.json). The author handles assignment submission.

## Run with Docker

Prerequisites: Docker Desktop/Engine with Compose. From this directory:

```sh
docker compose up --build -d
```

Open http://localhost:8000. React assets and the Python API share that origin. Health: http://localhost:8000/api/health. Stop with `docker compose down`.

The multi-stage Dockerfile builds React with Node 22, installs pinned Python dependencies on Python 3.12, copies the real historical snapshot, and runs Uvicorn as a non-root user. No API key or database is needed. Port 8000 must be available.

## Run locally

Prerequisites: Python 3.11+ and Node 22.12+ (Node 24 also tested).

```sh
python -m venv .venv
```

Activate on Windows PowerShell with `.\.venv\Scripts\Activate.ps1`, or on macOS/Linux with `source .venv/bin/activate`, then:

```sh
python -m pip install -r requirements-dev.txt
npm ci
npm run build
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. For frontend hot reload, run `npm run dev` in a second terminal and use the Vite URL (normally http://127.0.0.1:5173). Vite proxies `/api` to port 8000. Avoid setting `VITE_API_BASE` unless intentionally using a separate API origin; the default is same-origin.

## Customer workflow

1. Choose January decision dates and a historical decision time, then **Apply window**.
2. Read window MAE, RMSE, bias and the matched/expected coverage count.
3. Select a delivery date or a daily MAE tile to inspect the hourly forecast against actual generation. The daily tile is labeled by **decision date**; delivery is the following day.
4. Open **Accuracy review** for signed hourly errors.
5. Expand the interval table and **Inspect** a row to see the chosen publication, excluded future revisions, and both actual half-hours. Export the full analysis window as CSV.
6. Open **Data & methodology** for assumptions, units, formulas, source receipts and limitations.

The UI supports narrow/mobile layouts, labeled native controls, keyboard focus indicators, a skip link, reduced motion, and an accessible numeric table alongside the chart. Empty or partial data is explicit. API errors remove stale results and provide Retry.

## Architecture and file guide

```text
src/
  App.tsx                 React controls, views, charts and provenance inspection
  types.ts                API response types
  styles.css              Responsive visual design and accessibility styles
  main.tsx                React entrypoint
backend/
  analysis.py             Pure timestamp validation, deduplication, as-of selection, alignment, metrics
  data.py                 Gzip snapshot loader with SHA-256 and count checks
  main.py                 FastAPI validation, analysis/CSV/health/methodology routes; local static serving
api/index.py              Vercel Python ASGI entrypoint (same backend)
scripts/
  fetch_data.py           Bounded public API retrieval, retries, cached chunks, snapshot receipts
  audit_snapshot.py       Independent Decimal calculation using original responses and the running API
data/
  actuals.json.gz         Real FUELHH WIND rows for 2 Jan–1 Feb delivery
  forecasts.json.gz       All retrieved eligible candidate revisions for those target dates
  manifest.json           Retrieval URLs/counts, validation statistics, content hashes and timestamps
tests/                    Analytical edge cases, fetching failures, real-data/API integration tests
docs/                     Work log, requirement-to-evidence checklist, independent audit
Dockerfile                Multi-stage React/Python build and non-root application runtime
compose.yaml              One-command local container startup
vercel.json               React static build, Python function and /api routing
requirements*.txt         Python production/development dependency inputs
constraints.txt           Tested exact Python dependency resolution
.python-version           Requested Vercel Python 3.14 series (observed build: 3.14.8)
package*.json             Frontend dependency manifest and npm lockfile
.env.example              Optional configuration placeholders; no secrets needed
```

Request flow: React controls → `GET /api/analysis` → Pydantic query validation → hash-checked source snapshot → pure Python analysis → typed JSON → charts, coverage and table. `GET /api/export.csv` uses the same analysis function. No calculation is hardcoded into the frontend.

The fixed historical scope makes a small bundled snapshot simpler and more reliable than a database and a new live Elexon call on every page view. The snapshot is a cache of **source records**, not precomputed dashboard answers. Python computes each new query; bounded process caches avoid repeat work. Process memory is an optimization only and is not shared across Vercel instances. Every instance has the same bundled snapshot.

## January scope and decision-time policy

- **Decision dates:** 1–31 January 2026, inclusive, Europe/London.
- **Delivery dates:** 2 January–1 February 2026, inclusive; calendar-day `[00:00, next 00:00)` windows. A 31 January purchase decision therefore includes 1 February delivery. A 1 January delivery decision would have occurred in December and is outside scope.
- **Default decision time:** 09:00 Europe/London on D−1. January is GMT; internal timestamps are timezone-aware and normalized to UTC.
- This is a **documented pilot choice**, not a claim that every GB venue has a universal 09:00 cutoff. The [UK government’s 2023 market-arrangements response](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1179971/recoupling-gb-auctions-for-cross-border-trade-with-eu-consultation-government-response.pdf) documents separate historical 09:20 and 09:50 morning auctions. We choose an earlier briefing time and expose the control because the challenge does not specify a venue, product or deadline. We have not asserted those historical times are universal January 2026 rules.
- Exchange products may use a different delivery boundary, including a 23:00 power-day start. This pilot consistently uses London calendar days and does not attempt to reproduce exchange contract definitions or order books.

For each target timestamp **t**, select the maximum `publishTime` among WINDFOR records satisfying `publishTime <= decision_cutoff`. Selection is per target, not per entire publication file. Equal-to-cutoff publication timestamps are eligible. Later revisions are counted and excluded. Published timestamps are the available historical information proxy; source publication/transport latency is not modeled.

## Source data, retrieval and alignment

Official sources:

- [Assignment actual endpoint documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream)
- [Assignment forecast endpoint documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream)
- [Elexon’s official OpenAPI schema](https://data.elexon.co.uk/swagger/v1/swagger.json) — documents FUELHH as average MW over 30 minutes, query parameters and stream response shape; WINDFOR without publish filters defaults to the latest publication.
- [Elexon wind generation explanation](https://bmrs.elexon.co.uk/wind-generation) — describes the hourly forecast and telemetered wind outturn context.
- [Elexon developer portal](https://developer.data.elexon.co.uk/) — public APIs with no key, dataset/publication endpoint patterns and data-licence attribution.

Actual HTTP endpoints use the public base `https://data.elexon.co.uk/bmrs/api/v1/datasets/`:

```text
FUELHH/stream?settlementDateFrom=2026-01-02&settlementDateTo=2026-01-02&fuelType=WIND
WINDFOR/stream?publishDateTimeFrom=2026-01-01T00%3A00%3A00Z&publishDateTimeTo=2026-01-02T00%3A00%3A00Z
```

The downloader makes 65 daily requests, with at most three in parallel. WINDFOR publication dates span 29 December–31 January, covering a 72-hour leading window for the first decision; only targets in the relevant delivery window are retained. December records are fetched only as candidate publications for those decisions. The observed source forecast horizon is approximately 72 hours, so the preceding window covers it; unexpectedly absent candidates remain missing. Publication windows are explicit, avoiding today’s latest forecast. Actuals are requested for all 31 delivery dates. Request receipts are in `data/manifest.json`.

Observed targets in this snapshot: **FUELHH 30 minutes**, **WINDFOR 60 minutes**. We validate these alignments and do not round unexpected timestamps into place. For hourly target t, actual MW is derived as `(FUELHH[t] + FUELHH[t + 30 min]) / 2`, requiring both half-hours. The hourly forecast is compared with this hourly mean. This is an explicit evaluation convention, not proof that an hourly forecast point and an hourly average have identical measurement semantics.

Snapshots retain real source generation and publication timestamps. Exact target/publication duplicates are removed; conflicting values at the same key are excluded and counted. Actual revisions use the latest publication in the retrieved snapshot; actuals are **ex-post evaluation data**, not information available to a historical decision-maker. Different source coverage (for example, telemetered versus broader wind estimates), curtailment and averaging can contribute to the observed difference; we do not attribute every MW solely to forecast model skill.

The initial download contains 1,488 actuals and 17,864 relevant forecast revisions, with zero rejected rows and no duplicate/conflicting source keys. It is a reproducible historical snapshot, **not a live feed**. It contains no synthetic production data.

To reproduce or refresh:

```sh
python scripts/fetch_data.py
# Forces new requests instead of reusing cached successful source responses:
python scripts/fetch_data.py --refresh
```

Successful raw chunks are atomically cached under ignored `.cache/elexon/`. Failed requests are retried up to four attempts with bounded exponential backoff for transport/server/rate-limit errors; final failure aborts. Wrong stream shapes are rejected. JSON parsing rejects truncated responses; expected target coverage exposes semantically incomplete arrays. We cannot prove a provider has returned every historical revision from its own archive. No missing value is replaced by zero. Source record validation and matched coverage remain visible. Refreshing a snapshot requires an application restart (or new deployment), because integrity-checked immutable source data is cached by each process.

Attribution: **Contains BMRS data © Elexon Limited copyright and database right 2026.** Use is subject to the Elexon BMRS data licence and API terms linked from the developer portal.

## Accuracy definitions and initial findings

Use only matched, eligible hourly comparisons. `error = forecast_MW − actual_MW`. Positive bias means wind was overforecast; negative means underforecast.

| Metric | Definition | Unit |
|---|---|---|
| MAE | mean(abs(error)) | MW |
| RMSE | sqrt(mean(error²)) | MW |
| Bias | mean(error) | MW |
| Coverage | matched hourly comparisons / expected delivery hours | % |

All January delivery hours are one hour long; each matched hour has equal weight. No MAPE or percentage-error metric is used, avoiding zero-actual denominators. Valid zero output remains a valid actual. If no hours match, metrics are null and the UI displays “—”; coverage is zero.

For the bundled snapshot at the **09:00** default:

| Result | Value |
|---|---:|
| Matched / expected | 744 / 744 (100%) |
| MAE | 2,038.912634 MW |
| RMSE | 2,504.758653 MW |
| Bias | +1,747.887097 MW |
| Mean actual on matched hours | 11,283.557796 MW |
| Overforecast / underforecast hours | 632 / 112 |

For example, the 1 January 09:00 decision selects a forecast published at 07:30 for delivery at 00:00 on 2 January: 18,781 MW forecast, actual half-hours 15,228 and 15,505 MW, hourly mean 15,366.5 MW, error +3,414.5 MW. Changing that decision cutoff to 10:00 selects the 09:30 revision (18,699 MW). This demonstrates historical selection rather than current-latest retrieval.

These are descriptive results for this source/alignment convention and month, not a confidence band, trading recommendation, or a calibrated future forecast. Demand, prices, embedded wind and the utility’s full generation portfolio are not supplied. Windward cannot compute the utility’s exact additional power purchase requirement.

## Tests and verification

```sh
python -m pytest -q
npm run check
npm run build
npm audit
python -m pip check
```

38 backend tests have passed against the locked environment. They cover future-publication exclusion, latest eligible per-target selection, cutoff equality, offsets/naive timestamps, London/DST calendar boundaries, January/February limits, duplicates/conflicts, invalid values, missing halves/forecasts, zero actuals, metrics/signs, real snapshot/API/CSV behavior, retries, unexpected payloads and service failure.

An independent audit scans the **original cached Elexon responses** and uses Decimal arithmetic without importing the application analysis code. It checks the three full-month metrics and nine chosen records. Results agree within `1e-8 MW`; see [docs/independent-audit.json](docs/independent-audit.json).

```sh
# Run fetch_data.py first if raw cache is absent; start the local server, then:
python scripts/audit_snapshot.py --base-url http://127.0.0.1:8000
```

Final Docker, browser, public deployment and repository checks are recorded with their actual outcome in [docs/VERIFICATION.md](docs/VERIFICATION.md). This separates build success from live availability. No unperformed check should be interpreted as passed.

## Vercel deployment

The static React build and `api/index.py` Python function deploy together. `/api/:path*` rewrites to the ASGI app, retaining FastAPI routes. The function bundle includes `backend/` and `data/`; it reads immutable data without serverless filesystem writes. No secrets or environment variables are required. The pilot targets the existing free Hobby account, with no paid upgrade or external database.

From an authenticated Vercel CLI, link to the intended project first and verify its identity:

```sh
vercel link --project vqm7x9kp --scope aryans-projects-f0d5cb0d
vercel project inspect vqm7x9kp --scope aryans-projects-f0d5cb0d
vercel --prod --scope aryans-projects-f0d5cb0d
```

Use the linked project’s production alias for the public demo; generated preview/deployment URLs may require Vercel authentication. Public API and frontend access must both be verified. The project is stateless and has no user accounts or private data.

## Limitations and next steps

- One historical month, national datasets only; no price, demand, weather, portfolio or monetary-risk model.
- Hourly forecast versus hourly-mean actual is a documented approximation, with source-population differences potentially contributing to bias.
- Calendar delivery-day convention does not replicate every exchange power-day definition.
- Publication time is used as historical availability; archive completeness and transport delay are not independently provable.
- No runtime source refresh; deliberate pinned snapshot for reproducibility. Source refresh is a documented build/deploy operation.
- Error history is descriptive, not a calibrated probabilistic interval or procurement recommendation.
- Reasonable extensions: product-specific delivery windows, refresh/version comparison, venue-specific documented policy presets, additional months after scope approval, and empirically calibrated out-of-sample uncertainty. No additional dataset has been used in this pilot.

## AI assistance disclosure

**OpenAI Codex was used** for domain/documentation research, implementation, test creation/execution, interface work, deployment preparation and documentation. AI-assisted output is included in this repository. The performed automated checks, independent source calculations and browser evidence are listed explicitly; this disclosure does not imply a human review or check that did not occur.
