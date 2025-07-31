# WhatsPR Day‑1 Stable Baseline

Minimal, deterministic question flow **plus**:
* Twilio HMAC verification
* Duplicate‑Message guard
* `RESET / new / start` keyword
* SQLite persistence
* Structured JSON logging with `structlog`
* Request‑level middleware (start/end/error, latency)

## 1. Setup

```bash
cd <your repo root>
unzip -o whatspr_day1_stable.zip           # overwrite / add files
python -m venv env && source env/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # fill TWILIO_AUTH_TOKEN
pytest -q                                  # 2 tests should pass
uvicorn app.main:app --reload --port 8000
ngrok http 8000                            # paste URL into Twilio sandbox webhook
```

## 2. Git flow

```bash
git checkout -b day1-stable-baseline
git add .
git commit -m "Day 1 stable baseline with logging & tests"
git push -u origin day1-stable-baseline
# Open PR → reviewers → merge
```

After merge, deploy to Cloud Run with `--min-instances 1` and point Twilio webhook to the Cloud Run URL.