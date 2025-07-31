# Iteration Roadmap

| Iteration | Focus | High‑level tasks |
|-----------|-------|------------------|
| 0 (today) | Local tunnel MVP | Bot asks 6 fixed questions, stores in SQLite file. |
| 1 | Autoscaled cloud | Dockerfile, GitHub Action, Cloud Run free tier + Secret Manager. |
| 2 | Persistence at scale | DSN flip to Cloud SQL Postgres; add Alembic migrations. |
| 3 | Draft generator | Background task calls GPT‑4o to craft press release, emails JSON + draft. |
| 4 | Security hardening | Twilio HMAC unit‑tests, PII redaction in logs, GDPR purge cron. |
| 5 | Agentic enhancements | LLM‑driven dialog planner, vector store for long‑term memory. |