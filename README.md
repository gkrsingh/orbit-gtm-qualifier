# Orbit GTM Lead Qualifier

FastAPI + SQLite lead qualification demo. Deterministic scoring, no external APIs.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Run locally

```bash
uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000

## Run in production

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
```

`gunicorn` requires a Unix-like OS (no Windows support) — use it on the deployment host, not for local Windows development.

The SQLite database is created automatically at `data/orbit.db` (path resolved relative to the app package, not the working directory), so both commands above work regardless of which directory they're launched from.
