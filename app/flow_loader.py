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
    data = yaml.safe_load(Path(path).read_text())
    jsonschema.validate(data, SCHEMA)
    return data
