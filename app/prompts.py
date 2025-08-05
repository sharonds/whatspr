"""Static prompt generation for press release data collection.

Provides question mapping for different press release fields with fallback
to flow specification or legacy prompt mapping.
"""


def question_for(field: str) -> str:
    """Generate question prompt for a specific field.

    Args:
        field: Field name to generate question for.

    Returns:
        str: Question prompt for the field.
    """
    # Try to get question from flow spec first
    from .config import settings

    if settings.flow and "slots" in settings.flow:
        for slot in settings.flow["slots"]:
            if slot["id"] == field:
                return slot["ask"]

    # Fallback to legacy mapping
    mapping = {
        "announcement_type": "What type of announcement is this? (e.g., funding, product launch, hire)",
        "headline": "Do you have a headline in mind? (If not, say 'skip')",
        "key_facts": "List the key facts (who, what, when, how much, investors)",
        "quotes": "Provide two short quotes (CEO and investor).",
        "boilerplate": "Share a one‑paragraph company boilerplate.",
        "media_contact": "Who is the media contact (name, e‑mail, phone)?",
    }
    return mapping.get(field, f"Please provide {field.replace('_', ' ')}:")
