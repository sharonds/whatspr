"""Tests for message prefiltering functionality."""

from app.prefilter import clean_message


def test_emoji_removal():
    """Test that emojis are properly removed from messages."""
    assert clean_message("Hello 😀") == "Hello"
    assert clean_message("🚀 Great news!") == "Great news!"


def test_empty_message_handling():
    """Test that empty or whitespace-only messages return None."""
    assert clean_message("   ") is None
    assert clean_message("") is None
    assert clean_message("\n\t  \n") is None


def test_message_length_limit():
    """Test that overly long messages are rejected."""
    assert clean_message("x" * 1200) is None
    assert clean_message("x" * 1000) == "x" * 1000  # Should still work at limit


def test_normal_message():
    """Test that normal messages pass through correctly."""
    assert clean_message("Hello world") == "Hello world"
    assert clean_message("  This has spaces  ") == "This has spaces"
