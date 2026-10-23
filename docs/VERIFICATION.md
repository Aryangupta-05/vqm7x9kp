# Requirement-to-evidence checklist

This file is updated after actual checks. Pending is not passed. The source requirement PDF was read in full, all three pages extracted and visually inspected. The user's prohibition overrides its submission-form instruction.

| Requirement | Evidence | Status |
|---|---|---|
| Useful day-ahead wind decision pilot | Decision desk, accuracy review, provenance and methodology | Implemented; browser checks ongoing |
| Historical latest forecast | `backend/analysis.py`, leakage/equality/per-target tests; January 1 browser provenance | Verified |
| Quantitative accuracy | 744 matched hours; MAE/RMSE/bias; independent Decimal audit and nine source samples | Verified |
| Only Elexon FUELHH WIND and WINDFOR | `data/manifest.json` receipts/hashes; 65 bounded requests | Verified |
| January 2026 decisions | Date constraints, 744-hour window tests, delivery Jan 2–Feb 1 | Backend verified; boundary UI retest ongoing |
| React frontend | TypeScript and production build pass | Verified |
| Python backend | FastAPI endpoints; 38 tests pass with locked dependencies | Verified |
| Docker | Initial image build passed; final locked build/startup pending | In progress |
| Vercel or Heroku deployment | Vercel project created; Python API and public frontend pending | In progress |
| Public GitHub, anonymous random repo name | Intended repository vqm7x9kp | Pending publication |
| README file/directory explanation | README architecture/file guide | Written |
| README startup and deployment link | README local/Docker/Vercel commands; URL to be checked live | Written; live check pending |
| AI assistance disclosure | README explicit OpenAI Codex disclosure | Verified |
| <=16 hours | `docs/WORK_LOG.md` | In progress, well within limit |
| Unlisted YouTube <=10 min, customer <=5 min, technical <=5 min | User requested silent video + script, will supply two voice tracks | Blocked on future user audio and YouTube sign-in; silent draft preparation ongoing |
| Incognito/unauthenticated URL access | Fresh in-app browser and no-cookie HTTP checks | Local browser verified; public checks pending |
| Submission form | User will submit; never opened/filled/submitted by agent | Excluded by user |

## Actual checks completed so far

- Full isolated Python suite: 38 passed. `pip check`: no broken requirements. One upstream TestClient deprecation warning concerning its httpx backend; tests pass.
- TypeScript check and Vite 7.3.7 production build: passed.
- npm audit: zero vulnerabilities after applying the compatible Vite patch.
- Independent audit: full-month Decimal metrics agree within 1e-8 MW; nine source record checks pass. No application analysis imports used.
- Real source snapshot: SHA-256/count checks pass; 1,488 actual records and 17,864 forecast records.
- Initial Docker image build passed; final current source rebuild/startup pending.
- Local browser: real data renders; January 1 single-day query gives 24/24, publication 07:30 before 09:00; 10:00 cutoff selects 09:30 revision. Source table exposes both actual half-hours.

## Remaining browser/public checks

Month-end boundary; mobile viewport; source expansion and CSV; missing/empty/error/retry states in a temporary QA service outside the production repository; public app/API/repository without authentication; final screenshot evidence; live API independent audit.

## Not performed / not claimed

No YouTube upload or final voice synchronization exists yet. No assignment form, evaluator email, or evaluator delivery has occurred. No exact procurement quantity, future trading outcome, or universal market deadline is claimed.
