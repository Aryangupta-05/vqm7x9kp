# Requirement-to-evidence checklist

The three-page requirement PDF was read from beginning to end, extracted and visually inspected before implementation. It was reread after implementation against this checklist. Its submission-form instruction is excluded by the user's strict no-submission instruction.

| Requirement | Implementation and evidence | Status |
|---|---|---|
| UK utility day-ahead wind pilot | Decision desk, outlook chart, accuracy review, daily comparison, provenance and methodology; real browser flow | Verified |
| Latest forecast available at decision time | Per-target publishTime <= cutoff, then latest eligible; equality/future/per-target tests; browser 09:00 to 10:00 selects 07:30 to 09:30 | Verified |
| Quantitative accuracy | MAE/RMSE/bias/signs in MW, 744/744 matched hours; independent Decimal audit from original responses, nine samples | Verified |
| Only FUELHH WIND and WINDFOR | 65 bounded public requests; manifest URLs/counts/hashes; 1,488 actuals + 17,864 relevant forecast revisions | Verified |
| January 2026 purchase decisions | Range validation; Jan 1-31 decisions map to Jan 2-Feb 1 delivery; tests and month-end browser check | Verified |
| React frontend | React/TypeScript/Vite; responsive interface and real API rendering | Verified |
| Python backend | FastAPI owns source access, selection, alignment, metrics and CSV; 38 tests passed | Verified |
| Docker | Final Compose build/start; healthy; frontend HTTP 200; API 744/744; non-root UID 10001 | Verified |
| Vercel deployment | https://vqm7x9kp.vercel.app; READY; Python API and frontend public | Verified |
| Public GitHub with anonymous random name | https://github.com/Aryangupta-05/vqm7x9kp; private=false, pushed, no-auth HTTP 200 | Verified |
| README file/directory guide | README architecture and file guide | Verified |
| README startup and deployed URL | Tested local/build commands, Compose command, public app link | Verified |
| AI assistance disclosure | README explicitly names OpenAI Codex and its role | Verified |
| At most 16 hours | Session work log; first preparation session well below limit; future narration work recorded separately | Within limit |
| Customer and technical video, each <=5 minutes | Two silent visual drafts, each 210.0 seconds; customer and technical scripts | Drafts duration-checked; real voice required |
| Unlisted YouTube <=10 minutes | Silent combined draft 420.0 seconds; user will supply two voice tracks, then sync/upload | PENDING USER AUDIO AND YOUTUBE SIGN-IN; no YouTube URL |
| Verify links incognito | Fresh isolated in-app browser, no Vercel sign-in, plus no-cookie frontend/API/repo requests | Public access verified; literal incognito controls unavailable |
| Submission form | Never opened, filled or submitted; no evaluator email or deliverable message sent | User action only |

## Checks actually performed

- python -m pytest -q: 38 passed in the isolated locked environment. One upstream Starlette TestClient/httpx deprecation warning; no failed tests.
- python -m pip check: No broken requirements found.
- npm run check: passed, strict TypeScript.
- npm run build: passed, including Docker and Vercel environments.
- npm audit: zero vulnerabilities after Vite 7.3.7; runtime and development packages included.
- Independent calculation: original cached responses + Decimal arithmetic, without importing backend.analysis; three monthly metrics agree with the deployed API within 1e-8 MW, nine source selections/means/errors agree. See independent-audit.json.
- Source integrity: both gzip SHA-256 hashes and counts match; all required half-hours present in the initial snapshot; zero invalid/conflicting source rows.
- Container: final docker compose up --build -d; healthy; frontend 200; Python analysis 744 matched hours; id returns UID/GID 10001.
- Git/source: git diff --check; staged path review and token/private-key pattern scan returned no credential matches. Environment secrets, .vercel, cache, venv, dependencies and build output are ignored. No secrets are required to run.
- Public checks: unauthenticated HTTP 200 for /, /api/health, /api/analysis and GitHub; public app rendered real results in a fresh browser.
- Browser CSV: downloaded and verified 744 rows; API CSV integration test also matches JSON.

## Browser evidence

| Flow | Observed result |
|---|---|
| Initial month | 744/744; displayed MAE 2,039 MW, RMSE 2,505 MW, bias +1,748 MW |
| One-day controls | Jan 1 decision to Jan 2 delivery, 24/24 |
| Historical provenance | 09:00 cutoff selects Jan 1 07:30 publication; 13 later revisions excluded for the sampled midnight target |
| Cutoff sensitivity | 10:00 selects 09:30; forecast 18,781 to 18,699 MW; actual unchanged |
| Source expansion | Both half-hour actuals and publication times; hourly mean/error independently checked |
| Month end | Jan 31 decision to Feb 1 delivery, 24/24 |
| Accuracy review | Signed-error bars, daily MAE/bias/maximum miss, correct dates and units |
| Mobile | About 390px requested / 375px content width with scrollbar; no horizontal page overflow; table scroll stays local |
| Missing data | QA service removes one real half-hour: 743/744 (99.9%), missing-pair warning, no zero filling |
| Empty data | Null scores, em dashes, zero coverage; bias says No matched hours to score |
| Failure/recovery | QA 503 removes analysis and offers Retry; retry reaches restored response; real data restored subsequently |
| Console | No error entries captured in tested local/public flows |

Fault injection used work/qa_server.py OUTSIDE this repository on port 8002. It is not a deployed query option, fixture or fabricated production source. Screenshots and CSV are under the local outputs/evidence folder, outside the public app source.

## Deployment identity

- Project vqm7x9kp, prj_0fIplPOvR0HHhoyRxqBGwArKft4U, existing Hobby account; no paid upgrade/database/domain.
- Production alias: https://vqm7x9kp.vercel.app
- Application commit: 1a44f94e3c77ecbd2fa0ba917863f9e81ccf71e6
- Deployment: dpl_DurUFTc8sqVrN1fN2arRwbC8U8dR, READY; function region lhr1.
- Vercel's final observed dependency/build environment uses CPython 3.14.8, confirmed from the successful build log. The .python-version request is aligned to 3.14; Docker uses Python 3.12 and local tests use Python 3.11. The public Python API is independently verified.
- Initial dependency-parser failure was fixed by flat pinned runtime requirements. Final public checks passed.
- Later repository commits add documentation/evidence only; deployed application logic is the commit above.

## Video evidence and remaining work

Silent 1080p/24fps MP4 drafts use verified production screenshots and actual source/design panels. Each part is 210.0 seconds / 5,040 frames; combined is 420.0 seconds / 10,080 frames. Scripts describe existing behavior and real results, with no generated narration.

The user chose their own voice. After two audio files arrive: retime scenes to natural speech, remove the silent-draft footer, sync/check audio, enforce each part <=5:00 and combined <=10:00, upload unlisted to the authorized YouTube channel, and verify its watch URL without login. These steps remain incomplete; scripts and silent MP4s do not replace them.

## Verification limits

- Historical Vercel runtime-log query was denied (connector 403). A clean historical error scan is not claimed. Installed CLI supports only a forward stream. Public response/browser checks succeeded.
- No literal incognito/profile creation is exposed. Fresh isolated browser plus independent no-cookie HTTP requests were used.
- No formal WCAG audit, calibrated uncertainty, order-book integration or exact procurement calculation is claimed.
- Provider archive completeness and publication transport latency cannot be independently proved. Resolution and source-population limitations are documented.
- No assignment form, evaluator email or evaluator delivery occurred.
