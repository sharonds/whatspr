from pathlib import Path


def test_knowledge_file_exists():
    assert Path("knowledge/press_release_requirements.txt").exists()
