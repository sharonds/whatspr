from tests.utils.sim_client import WhatsSim
import pytest
from app import agent_endpoint
from app.agent_runtime import run_thread as original_run_thread

# Monkeypatch agent to avoid OpenAI call
from tests.mock_agent import fake_run_thread


@pytest.fixture(autouse=True)
def patch_agent(monkeypatch):
    # Patch the function in the agent_endpoint module where it's actually used
    monkeypatch.setattr(agent_endpoint, "run_thread", fake_run_thread)
    # Also patch it in the original module as backup
    monkeypatch.setattr("app.agent_runtime.run_thread", fake_run_thread)


def test_menu_flow():
    bot = WhatsSim()
    # Use reset command to trigger the menu
    response1 = bot.send("reset")
    assert "Pick the kind of announcement" in response1

    # Send option 1 and expect headline question
    response2 = bot.send("1")
    assert "headline" in response2.lower()
    assert len(response2) > 0
