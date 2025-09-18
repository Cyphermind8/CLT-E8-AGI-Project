# FILE: tests/test_config_schema.py
from pathlib import Path
import json
import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("schemas/config.schema.json")
CONFIG_PATH = Path("config/default.yaml")

def test_config_conforms_to_schema():
    assert SCHEMA_PATH.exists(), "schemas/config.schema.json is missing"
    assert CONFIG_PATH.exists(), "config/default.yaml is missing"

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(cfg), key=lambda e: e.path)
    assert not errors, "config/default.yaml violates the schema: " + "; ".join(e.message for e in errors)

    # Invariants used by code
    assert isinstance(cfg["project"]["write_dirs"], list)
    assert "success" in cfg["metrics"]["tracked"]
