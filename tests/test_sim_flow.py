
from tests.utils.sim_client import WhatsSim
import pytest
from app import agent_runtime

# Monkeypatch agent to avoid OpenAI call
from tests.mock_agent import fake_run_thread

@pytest.fixture(autouse=True)
def patch_agent(monkeypatch):
    monkeypatch.setattr(agent_runtime, "run_thread", fake_run_thread)

def test_menu_flow():
    """Test that the simulator can send messages and receive responses"""
    bot = WhatsSim()
    # Use reset command to trigger the menu (this part works without API calls)
    response1 = bot.send("reset")
    assert "Pick the kind of announcement" in response1
    assert response1.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    
    # Just test that we can send another message and get a response
    # The actual content will depend on the assistant, so we just check basic functionality
    response2 = bot.send("test message")
    assert response2.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert len(response2) > 0
