import os, json

def load_json(path: str, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default or {}

def load_schema_config():
    base = os.path.dirname(__file__)
    cfg = load_json(os.path.join(base, "..", "setup-config.json"), {})
    schema = load_json(os.path.join(base, "..", "form_schema.json"), {})
    i18n_de = load_json(os.path.join(base, "..", "i18n.de.json"), {})
    return cfg, schema, i18n_de