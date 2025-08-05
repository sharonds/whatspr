"""Basic unit tests for atomic tools.

Run with:  pytest -q
"""

import importlib

tools = importlib.import_module("app.tools_atomic")


def test_all_tools_present():
    required = [
        "save_announcement_type",
        "save_headline",
        "save_key_facts",
        "save_quotes",
        "save_boilerplate",
        "save_media_contact",
    ]
    for fn in required:
        assert hasattr(tools, fn), f"Missing {fn}"


def test_tool_returns_confirmation():
    fn = tools.save_headline
    msg = fn("Test headline")
    # Should return either "saved" or "updated" depending on if record exists
    assert any(word in msg.lower() for word in ["saved", "updated"])
