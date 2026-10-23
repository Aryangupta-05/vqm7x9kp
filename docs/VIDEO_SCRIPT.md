# Two-part video narration

Status: silent draft prepared; awaiting the author's real voice recordings before synchronization and unlisted YouTube upload. Each part is planned for 3:30, total 7:00; neither part may exceed 5:00. These are actual verified app views and source diagrams, not fabricated results.

## Part 1 · C1: A decision desk for national wind

Welcome to Windward, a pilot decision desk for a UK utility’s day-ahead procurement team. It answers two questions: what wind forecast was available when we had to decide, and how far was that forecast from actual generation? This view covers purchase decisions made from the first to the thirty-first of January 2026, for next-calendar-day delivery. Across 744 matched hourly comparisons, the typical absolute miss was about 2,039 megawatts.

## Part 1 · C2: See the outlook and the miss together

The delivery view puts the forecast and actual wind output on one chart. The gold dashed line is the forecast selected at the historical cutoff; the green line is actual output, averaged from both half-hours. Here, the fifteenth of January decision covers delivery on the sixteenth. The day’s mean absolute error was about 783 megawatts, with positive bias of about 352 megawatts. The brief highlights where the largest hourly miss occurred.

## Part 1 · C3: Focus attention on larger misses

Accuracy review shows the direction of each hourly error. Positive bars mean wind was overforecast, which is relevant when considering the risk of less wind arriving than expected. The twenty-seventh of January decision, for delivery on the twenty-eighth, had a daily mean absolute error of about 5,375 megawatts. Its largest hourly miss was about 6,271 megawatts at four a.m. The daily comparison helps the team identify these days for closer investigation.

## Part 1 · C4: Inspect the evidence behind a number

Every interval can be traced back to its source. For the first of January decision at nine a.m., the midnight delivery forecast was published at seven thirty. It predicted 18,781 megawatts. The two actual half-hours were 15,228 and 15,505 megawatts, giving an hourly mean of 15,366 point five. The signed error was therefore positive 3,414 point five megawatts. Thirteen later revisions were excluded from this historical comparison.

## Part 1 · C5: Change the decision time, not history

If the team’s decision time changes, the available forecast can change too. Moving this cutoff to ten a.m. makes the nine-thirty publication eligible. For the same delivery hour, the selected forecast becomes 18,699 megawatts; the actual output is unchanged. This is why using today’s latest revision would give the wrong historical evaluation. The controls support different January windows and decision times, and the full matched analysis can be exported as a CSV.

## Part 1 · C6: A useful pilot with explicit boundaries

The assumptions are visible in the product. Nine a.m. is a pilot briefing policy, not a universal market deadline. Delivery uses London calendar days, so the final January decision includes the first of February. This is a reproducible historical snapshot using only the two requested Elexon datasets. Windward quantifies observed wind forecast differences; it cannot calculate the utility’s exact additional purchase without demand and portfolio data. Historical errors are descriptive, rather than a calibrated future uncertainty band.

## Part 2 · T1: One clear request path

The architecture is deliberately small. React and TypeScript collect the decision window and time, then call the Python FastAPI analysis endpoint. The backend validates the query, loads a hash-checked source snapshot, selects eligible forecasts, aligns actuals, and calculates the metrics. Typed JSON drives the charts and source table. CSV export calls the same analysis function. Docker serves React and the API from one origin; Vercel serves static assets alongside the same Python application.

## Part 2 · T2: Preserve source records, not dashboard answers

The downloader makes 65 bounded requests to the assignment’s two public endpoints. Actuals are filtered to WIND; forecasts always have explicit publication-time filters. Successful raw responses are cached, failed requests are retried, and malformed responses are rejected. The relevant snapshot contains 1,488 actual rows and 17,864 forecast revisions. Gzip files, SHA-256 hashes, counts, retrieval times and request receipts make the data reproducible. No generation values are invented, and the dashboard is not a hardcoded result.

## Part 2 · T3: Make future-data leakage impossible by selection

The central analytical rule lives in backend slash analysis dot py. For each target hour, candidates are filtered to publications at or before the applicable historical cutoff. The maximum eligible publication time is then selected for that target. This allows different intervals to come from different source publications when necessary. Later revisions are counted but excluded. Business dates use Europe slash London, while internal timestamps are aware UTC values. January decisions map to the next calendar delivery day.

## Part 2 · T4: Align resolutions and define the error sign

The source resolutions differ: WINDFOR targets are hourly and FUELHH actuals are half-hourly average megawatts. The analysis requires both half-hours and averages them for the matching hour. Missing pairs stay missing and do not enter the score. Error is forecast minus actual; MAE measures absolute size, RMSE emphasizes larger misses, and bias preserves direction. Zero actual output is valid. Duplicate keys are removed, conflicting values are excluded, and actual revisions are treated as ex-post evaluation data.

## Part 2 · T5: Verify the analytical boundaries independently

Thirty-eight backend tests passed, covering future-publication exclusion, cutoff equality, per-target selection, date boundaries, time zones, missing data, duplicates, zero actuals, metrics, fetching failures and API behavior. A separate Decimal-based audit scans the original source responses without importing the analysis code. It agrees with the deployed monthly metrics and checks nine selected records. Browser checks cover real controls, provenance, CSV, mobile layout, and missing, empty, error and recovery states. The TypeScript check, production build and Docker startup also passed.

## Part 2 · T6: A reproducible deployment and maintainable handover

The public repository contains the source, tests, dependency locks, Docker configuration and a README with the directory guide and startup commands. The container runs as a non-root user and passes its health check. The Vercel production frontend and Python API are accessible without authentication and return the verified real-data results. The README explicitly discloses OpenAI Codex assistance. Sensible next steps are product-specific delivery windows, versioned refreshes and out-of-sample uncertainty calibration. The assignment form and evaluator communications remain entirely the author’s responsibility.

