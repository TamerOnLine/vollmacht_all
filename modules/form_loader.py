# modules/form_loader.py
import os, json, importlib.util
from pathlib import Path

FORMS_DIR = Path(__file__).resolve().parent.parent / "forms"

class LoadedForm:
    def __init__(self, key, name, schema, i18n, builder_module):
        self.key = key                # ex: "vollmacht"
        self.name = name              # display name
        self.schema = schema          # dict
        self.i18n = i18n              # dict
        self.builder = builder_module # module with build_pdf(...)

def _load_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default or {}

def _load_py_module(py_path: Path):
    spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

def discover_forms(preferred_lang="de") -> dict[str, LoadedForm]:
    forms: dict[str, LoadedForm] = {}
    if not FORMS_DIR.exists():
        return forms

    for d in sorted([p for p in FORMS_DIR.iterdir() if p.is_dir()]):
        key = d.name
        schema = _load_json(d / "schema.json", {})

        # pick i18n file: preferred -> en -> de -> ar -> first existing
        candidates = [f"i18n.{preferred_lang}.json", "i18n.en.json", "i18n.de.json", "i18n.ar.json"]
        i18n = {}
        for fname in candidates:
            path = d / fname
            if path.exists():
                i18n = _load_json(path, {})
                break

        builder_py = d / "builder.py"
        if not builder_py.exists():
            # skip invalid form folder
            continue
        builder_mod = _load_py_module(builder_py)

        display_name = i18n.get("app.title") or schema.get("title") or key
        forms[key] = LoadedForm(key, display_name, schema, i18n, builder_mod)
    return forms
