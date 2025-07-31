# WhatsPR MVP (Day 0)

A lightning‑weight FastAPI WhatsApp bot that collects structured answers for a future press‑release generator.

## Quickstart (Local Tunnel)
```bash
python -m venv env && source env/bin/activate
pip install -r requirements.txt

cp .env.example .env  # fill your real keys
uvicorn app.main:app --reload --port 8000

# in another shell
ngrok http 8000
# paste the https URL into Twilio Sandbox -> Messaging -> Webhook URL
```

## Folder layout
```
app/
  main.py          # FastAPI entry
  config.py        # env & settings
  models.py        # SQLModel ORM + init_db()
  router.py        # tiny finite‑state engine
  logging_config.py
tests/
  test_router.py
```

## Roadmap
- **Day 1**: Add OpenAI-powered follow‑up phrasing, structlog JSON logs, HMAC signature unit‑test.
- **Day 2**: Containerise & deploy to Cloud Run (`gcloud run deploy --source .`).
- **Day 3**: Swap SQLite → Cloud SQL Postgres; enable `min-instances 1`.
- **Day 4+**: Background email task → Cloud Tasks; add simple admin UI.

See `ROADMAP.md` for details.