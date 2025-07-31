
"""Tests for command handling functionality."""

from app.commands import maybe_command


def test_alias_help():
    """Test that help command aliases work."""
    assert maybe_command('/h') is not None
    assert maybe_command('/help') is not None
    assert maybe_command('help') is not None


def test_alias_reset():
    """Test that reset command aliases work."""
    assert maybe_command('/reset') is not None
    assert maybe_command('reset') is not None
    assert maybe_command('/cancel') is not None
    assert maybe_command('stop') is not None


def test_alias_change():
    """Test that change command aliases work."""
    assert maybe_command('/change') is not None
    assert maybe_command('change') is not None


def test_non_command():
    """Test that non-commands return None."""
    assert maybe_command('hello') is None
    assert maybe_command('this is a regular message') is None
