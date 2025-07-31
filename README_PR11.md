
# PR 11 – Profile Cache & Robust Input

Adds:
* `Company`, `Founder` tables for persistent profile; skip boilerplate/contact on repeat sessions.
* `aggregator.py` – merges WhatsApp split messages within 3‑second window.
* `correction.py` – detects `*word` or “I meant …” and replaces last answer.
* `idle.py` – helper to mark session expired after 1 h silence.
* Corresponding unit tests.

Hook‑up notes:
* Call `aggregate(sender, body)` before processing; if it returns `None`, exit early.
* When `is_correction(msg)` is true, overwrite previous `Answer` record for current slot.
* Check `is_idle(founder.last_seen)` at start; if idle, mark session expired and send reminder.
