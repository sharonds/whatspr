# PR 3 – Dynamic Knowledge & File Search

This patch externalises all slot definitions into **knowledge/press_release_requirements.txt**
and wires up OpenAI File Search so the assistant can query that file at runtime.

## Files

* `knowledge/press_release_requirements.txt` – single source of truth for required slots.
* `scripts/setup_assistant_file_search.py` – helper to (re)create the Assistant with File Search.
* `tests/test_knowledge_exists.py` – simple regression guard.
* `README_PR3.md` – this file.

## Steps to apply

```bash
cd ~/whatspr-staging
cp -R ~/downloads/PR3_file_search/* .

# Create / update assistant with File Search enabled
OPENAI_API_KEY=$STAGING_KEY python scripts/setup_assistant_file_search.py

# Quick test
pytest tests/test_knowledge_exists.py

# Commit & push
git checkout -b file-search
git add knowledge/ scripts/setup_assistant_file_search.py tests/ README_PR3.md
git commit -m "feat: File Search knowledge base for press‑release slots"
git push -u origin file-search
# open PR
```

## Deployment Notes
* Ensure runtime container mounts the `knowledge/` file so it stays in sync.
* Storage: OpenAI vector store costs are minimal (<50 c/month at current pricing).
* If knowledge changes, rerun the setup script or call `update_assistant.py` with new file_id.

---
After this PR the agent can answer **“What info do you still need?”** by quoting the knowledge file.
