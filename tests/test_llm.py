from app.llm import rephrase_question
from app.config import settings


def test_llm_disabled(monkeypatch):
    monkeypatch.setattr(settings, "llm_enabled", False)
    q1 = rephrase_question("headline")
    assert "headline" in q1.lower() or q1.lower().startswith("do you")


def test_llm_enabled_no_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_enabled", True)
    monkeypatch.setattr(settings, "openai_api_key", None)
    q2 = rephrase_question("headline")
    assert q2  # returns something non-empty
