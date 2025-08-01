
# PR 1 – Atomic Tools & Slot Persistence

This patch removes the brittle `save_slot`/`get_slot` pattern and introduces **one function per slot**.

## Files

* `tools_atomic.py` – new module with six `save_*` tools.
* `tests/test_tools_atomic.py` – basic pytest coverage.
* `migrations/backfill_generic_slots.py` – optional helper to migrate legacy data.

## How to apply

1. Copy `tools_atomic.py` into `app/` (or `app/tools/` if you prefer a package).
2. **Register tools** in `app/agent_runtime.py → _get_or_create_assistant()`:

   ```python
   ATOMIC_FUNCS = [
       "save_announcement_type",
       "save_headline",
       "save_key_facts",
       "save_quotes",
       "save_boilerplate",
       "save_media_contact",
   ]
   # inside tools=[ ... ] list comprehension
   *[
       {
           "type": "function",
           "function": {
               "name": fn,
               "parameters": {
                   "type": "object",
                   "properties": {"value": {"type": "string"}},
                   "required": ["value"],
               },
           },
       }
       for fn in ATOMIC_FUNCS
   ],
   ```
3. Update `app/agent_endpoint.py` dispatch table:

   ```python
   from app import tools_atomic as tools
   TOOL_DISPATCH = {
       "validate_local": validate_local,
       "finish": finish_fn,
       **{fn: getattr(tools, fn) for fn in ATOMIC_FUNCS},
   }
   ```
4. Run `pytest -q tests/` – all tests should pass.
5. Deploy → run `update_assistant.py` to push revised tool schema.

## Legacy data migration

The optional script in `migrations/` scans the `Answer` table and renames
generic `name` entries to their atomic counterparts.

---

*After merging PR 1, proceed to PR 2 to adopt the goal‑oriented prompt.*
