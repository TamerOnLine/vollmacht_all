from .config import load_json
import os

base = os.path.dirname(__file__)
i18n_ar = load_json(os.path.join(base, "..", "i18n.ar.json"), {})
i18n_de = load_json(os.path.join(base, "..", "i18n.de.json"), {})
i18n_en = load_json(os.path.join(base, "..", "i18n.en.json"), {})

LANGS = {
    "Deutsch": i18n_de,
    "العربية": i18n_ar,
    "English": i18n_en,
}

def tr(key: str, i18n: dict, fallback: str = "") -> str:
    return i18n.get(key, fallback or key)