def question_for(field: str) -> str:
    mapping = {
        "announcement_type": "What type of announcement is this? (e.g., funding, product launch, hire)",
        "headline": "Do you have a headline in mind? (If not, say 'skip')",
        "key_facts": "List the key facts (who, what, when, how much, investors)",
        "quotes": "Provide two short quotes (CEO and investor).",
        "boilerplate": "Share a one‑paragraph company boilerplate.",
        "media_contact": "Who is the media contact (name, e‑mail, phone)?",
    }
    return mapping.get(field, f"Please provide {field.replace('_',' ')}:")