
# PR16 – Conversation Simulator & Log Capture

## What's new
* **tests/utils/sim_client.py** – FastAPI TestClient wrapper that simulates WhatsApp form posts including unique MessageSid.
* **tests/mock_agent.py** – Minimal stub for `agent_runtime.run_thread` to avoid OpenAI calls in unit tests.
* **tests/test_sim_flow.py** – Example smoke test that walks through menu + first reply.
* **tests/utils/log_capture.py** – Context manager to capture structlog output for assertions or manual inspection.

## Usage
```bash
pip install pytest
pytest -k sim_flow          # runs simulator test in <1 s
pytest -s                   # show captured logs
```

Extend `mock_agent.fake_run_thread` to yield sequential scripted replies and tool calls for larger scenario tests.
