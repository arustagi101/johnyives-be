# YCH FastAPI UX Auditor and Next.js Generator

## Setup

1. Python env
   - `python3 -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Playwright browsers (needed for screenshots)
   - `python -m playwright install chromium`
3. Optional: PageSpeed Insights API key
   - `export PAGESPEED_API_KEY=YOUR_KEY`

## Run API

- Start server (hot reload):
  ```bash
  source .venv/bin/activate
  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
  ```

- Health check:
  ```bash
  curl http://127.0.0.1:8000/health
  ```

- Stop server: Ctrl+C (or `pkill -f "uvicorn app.main:app"`)

## API Endpoints

- POST `/audit` → `{ url }` starts audit, returns `audit_id`
- GET `/audit/{id}` → audit status and results
- POST `/generate` → `{ audit_id, preferences? }` generates Next.js project
- GET `/generate/{id}` → generation status, zip path and optional deploy info

## Run tests (integration E2E)

- This repo has a networked end-to-end test that exercises the full flow (audit → generate).
- It will open a real page via Playwright and may take a few seconds.

Run the tests with live logging:
```bash
source .venv/bin/activate
pytest
# or verbose live logs
pytest -o log_cli=true --log-cli-level=INFO -s
```

You should see logs like `e2e.audit.done`, `e2e.generate.done`, and artifact paths.

## Notes
- Storage is in-memory and artifacts are written under `./runtime/`.
- DSPy is optional; if unavailable, rule-based suggestions are used.
- PSI is optional; if `PAGESPEED_API_KEY` is not set, PSI is skipped.

## Where to find results

All files are written under `./runtime/`:

- Audit (after POST `/audit` and polling GET `/audit/{id}`):
  - `runtime/audit/<audit_id>/screenshot_above_fold.png`
  - `runtime/audit/<audit_id>/screenshot_full.png` (best effort)
  - `runtime/audit/<audit_id>/dom.html`
  - Axe/PSI data included in the JSON response under `artifacts`

- Generation (after POST `/generate` and polling GET `/generate/{id}`):
  - `runtime/generate/<job_id>/next_project/` (generated Next.js project)
  - `runtime/generate/<job_id>/next_project.zip` (zipped project)
  - `runtime/generate/<job_id>/next_project/analysis.json` (traceability)

Server and test logs are printed to the console at INFO level by default.

## Render the generated website

After a successful generation, you can run the Next.js project directly:

```bash
source .venv/bin/activate
python scripts/render_generated.py --open
# Options:
#   --project-dir /absolute/path/to/next_project  # use a specific generated project
#   --prod                                        # build and start in production mode
#   --port 3000                                   # choose port (default 3000)
#   --install                                     # force reinstall dependencies
```

The script will pick the most recent `runtime/generate/<job_id>/next_project` if `--project-dir` is omitted
and will use `pnpm`/`yarn`/`npm` in that order if available.
