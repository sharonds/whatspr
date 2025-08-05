"""Flow specification loaders for conversation configuration.

Loads YAML flow specifications that define conversation structure,
field requirements, and validation rules for press release data collection.
"""

import yaml
import jsonschema
from pathlib import Path

SCHEMA = {
    "type": "object",
    "required": ["flow_id", "slots", "max_turns"],
    "properties": {
        "flow_id": {"type": "string"},
        "max_turns": {"type": "integer"},
        "slots": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "ask"],
                "properties": {"id": {"type": "string"}, "ask": {"type": "string"}},
            },
        },
    },
}


def load_flow(path: str):
    """Load conversation flow specification from YAML file.

    Args:
        path: File path to YAML flow specification.

    Returns:
        dict: Parsed flow specification with slots and validation rules.

    Raises:
        ValidationError: If flow specification doesn't match schema.
    """
    data = yaml.safe_load(Path(path).read_text())
    jsonschema.validate(data, SCHEMA)
    return data
