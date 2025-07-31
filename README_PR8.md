
## New in this PR (#8)

* **Feature flag `LLM_ENABLED`** (default `false`)
* `OPENAI_API_KEY` optional in `.env`
* `app/llm.py` – calls OpenAI to re‑phrase follow‑ups when enabled, with graceful fallback
* Responses now returned as **TwiML XML** (Twilio‑approved)
* Added pytest `test_llm.py`
