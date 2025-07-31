from typing import Optional
from .llm import rephrase_question

# AI-powered dynamic question generation with fallback to static questions
def question_for(field: str, previous: Optional[str] = None) -> str:
    try:
        # Use AI to generate dynamic, contextual questions
        return rephrase_question(field, previous)
    except Exception as e:
        # Fallback to static questions if AI fails
        mapping = {
            "announcement_type": "What type of announcement is this? (e.g., funding, product launch, hire)",
            "headline": "Do you already have a headline in mind? (If not, reply 'skip')",
            "key_facts": "List the key facts (who, what, when, how much, investors)",
            "quotes": "Provide two short quotes (CEO and investor).",
            "boilerplate": "Share a one‑paragraph company boilerplate.",
            "media_contact": "Who is the media contact (name, e‑mail, phone)?",
        }
        return mapping.get(field, f"Please provide {field.replace('_', ' ')}:")