# PR 2 – Goal‑Oriented Prompt

This patch replaces the rigid, step‑by‑step prompt with a concise mission‑style prompt (`prompts/assistant_v2.txt`)
that leverages the LLM’s own planning abilities.

## Files included
* `prompts/assistant_v2.txt` – new system prompt.
* `prompts/examples/sample_conversation.md` – illustrative dialogue.
* `README_PR2.md` – this file.

## How to test

1. Copy the `prompts/assistant_v2.txt` into your repo’s `prompts/` directory (leaving `assistant_legacy.txt`
   in place for rollback).
2. Point `_get_or_create_assistant()` to read the new file:

   ```python
   PROMPT = Path("prompts/assistant_v2.txt").read_text().strip()
   ```

3. Run:

   ```bash
   OPENAI_API_KEY=$STAGING_KEY python start_agent.py
   ```

   Have a short conversation (or replay recorded messages) and ensure:
   * The assistant asks naturally without referencing `get_next_question`.
   * Tool calls use the new atomic `save_*` names.
   * It completes in ≤ 12 assistant turns.

4. Update or delete any tests that assert the old prompt contents.

## Git workflow

```bash
cd ~/whatspr-staging
cp -R ~/downloads/PR2_goal_prompt/* .
pytest -q                 # make sure nothing fails
git checkout -b goal-prompt
git add prompts/assistant_v2.txt prompts/examples/ README_PR2.md
git commit -m "feat: goal‑oriented prompt ⬆️"
git push -u origin goal-prompt
# open Pull Request
```

---
After merging, proceed to PR 3 to attach the knowledge file and enable File Search.
