from tests.utils.sim_client import WhatsSim


def test_reset_menu():
    """Test that reset command returns the menu without making OpenAI calls"""
    bot = WhatsSim()
    response = bot.send("reset")

    # Should get the menu response without any agent interaction
    assert "Pick the kind of announcement" in response
    assert "Funding round" in response
    assert "Product launch" in response
    assert "Partnership" in response
