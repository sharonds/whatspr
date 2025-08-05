"""LLM utilities.

If `settings.llm_enabled` is False or we lack an OpenAI key,
`rephrase_question()` just returns the original prompt mapping.
Otherwise it calls OpenAI to re‑phrase follow‑up questions.
"""

from .prompts import question_for
from .config import settings


def rephrase_question(field: str) -> str:
    """Rephrase question using LLM or return static prompt.

    Args:
        field: Field name to generate question for.

    Returns:
        str: Rephrased question from LLM or static question mapping.
    """
    # Disabled or no key ➜ deterministic mapping
    if not settings.llm_enabled or not settings.openai_api_key:
        return question_for(field)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        user_msg = (
            "Rewrite the following prompt into a friendly, single-sentence question "
            "with at most 20 words: " + question_for(field)
        )
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.7,
            messages=[{"role": "user", "content": user_msg}],
            timeout=6,
        )
        return res.choices[0].message.content.strip()
    except Exception:
        # Fall back on any error
        return question_for(field)
