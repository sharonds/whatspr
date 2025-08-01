from pathlib import Path

def test_prompt_v2_exists():
    assert Path("prompts/assistant_v2.txt").exists()
