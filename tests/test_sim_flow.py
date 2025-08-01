import pytest
from unittest.mock import patch
from tests.utils.sim_client import WhatsSim


def test_menu_flow():
    """Test conversation flow using mock agent to avoid API calls"""

    def mock_run_thread(thread_id, user_msg):
        """Mock agent that simulates the expected conversation flow"""
        print(
            f"[MOCK] Called with: thread_id={thread_id[:8] if thread_id else 'None'}..., user_msg='{user_msg}'"
        )

        if user_msg == "1":
            response = "Great! Let's collect details for your funding round. What's the headline?"
            print(f"[MOCK] Returning: '{response[:50]}...'")
            return response, []
        else:
            response = "Mock response to: " + user_msg
            print(f"[MOCK] Returning: '{response}'")
            return response, []

    # Use unittest.mock.patch to patch both potential import paths
    with (
        patch('app.agent_endpoint.run_thread', side_effect=mock_run_thread),
        patch('app.agent_runtime.run_thread', side_effect=mock_run_thread),
    ):

        bot = WhatsSim()
        # Use reset command to trigger the menu
        response1 = bot.send("reset")
        assert "Pick the kind of announcement" in response1

        # Send option 1 and expect headline question
        response2 = bot.send("1")
        assert "headline" in response2.lower()
        assert len(response2) > 0
