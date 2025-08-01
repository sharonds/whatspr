
# PR14 – Agent default, legacy fallback

* `app/main.py` now mounts **agent endpoint** by default.
* Set `LEGACY_MODE=true` to fall back to old deterministic flow.
* Obsolete modules (`router.py`, old graph) can be deleted after this PR.
