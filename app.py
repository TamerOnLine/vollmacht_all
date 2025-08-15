import streamlit as st
from modules.signature import draw_signature_ui, get_signature_bytes
from modules.form_loader import discover_forms
from pathlib import Path
import json

st.set_page_config(page_title="Dynamic PDF Forms", page_icon="🧾", layout="centered")

# لغة ملفات i18n داخل كل نموذج
lang_ui = st.sidebar.selectbox("Language / اللغة", ["de", "ar", "en"], index=0)

forms = discover_forms(preferred_lang=lang_ui)
if not forms:
    st.error("No forms found. Please add folders under ./forms/<form_key>/")
    st.stop()

# اختيار النموذج المتاح
form_keys = list(forms.keys())
selected_key = st.sidebar.selectbox("Form / النموذج", form_keys, index=0)
current = forms[selected_key]

st.title(current.i18n.get("app.title", current.name))
schema = current.schema
i18n = current.i18n

# ========== Dynamic Form ==========
with st.form("dynamic_form"):
    values = {}
    for section in schema.get("sections", []):
        st.subheader(i18n.get(section.get("title_i18n", section.get("key","")), section.get("key","")))
        for fld in section.get("fields", []):
            label = i18n.get(fld.get("label_i18n", fld.get("key","")), fld.get("key",""))
            placeholder = fld.get("placeholder", "")
            key = f'{section["key"]}_{fld["key"]}'
            if fld.get("type") == "textarea":
                values[key] = st.text_area(label, placeholder=placeholder)
            else:
                values[key] = st.text_input(label, placeholder=placeholder)

    cols = st.columns(2)
    with cols[0]:
        stadt = st.text_input(i18n.get("field.ort", "Ort"), value=schema.get("misc", {}).get("stadt_default", "Berlin"))
    with cols[1]:
        datum = st.text_input(i18n.get("field.datum", "Datum"), placeholder=schema.get("misc", {}).get("date_placeholder", ""))

    submitted = st.form_submit_button(i18n.get("btn.create", "PDF erstellen"))

# ========== Signature (optional) ==========
sig_required = schema.get("misc", {}).get("signature_required", True)
signature_data = None
if sig_required:
    draw_signature_ui(i18n)
    signature_data = get_signature_bytes()

# ========== Validation & Generate ==========
def validate_required(vals, sc, i18n_dict):
    errors = []
    for section in sc.get("sections", []):
        for fld in section.get("fields", []):
            if fld.get("required"):
                k = f'{section["key"]}_{fld["key"]}'
                label = i18n_dict.get(fld.get("label_i18n", fld.get("key","")), fld.get("key",""))
                if not (vals.get(k,"") or "").strip():
                    errors.append(label)
    return errors

def v(sec, key): return (values.get(f"{sec}_{key}", "") or "").strip()

def _json_read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}

if submitted:
    errs = validate_required(values, schema, i18n)
    if errs:
        st.error(i18n.get("validation.required","Bitte Pflichtfelder ausfüllen.") + "\n- " + "\n- ".join(errs))
    else:
        form_data = { **{k: (values.get(k,"") or "").strip() for k in values.keys()},
                      "stadt": stadt.strip(), "datum": datum.strip() }

        # اختياري: aliases شائعة لدعم قوالبك الحالية (لن تؤذي النماذج الأخرى)
        form_data.update({
            "vg_name": v("vg","name"),
            "vg_vorname": v("vg","vorname"),
            "vg_geb": v("vg","geb"),
            "vg_addr": v("vg","addr"),
            "b_name": v("b","name"),
            "b_vorname": v("b","vorname"),
            "b_geb": v("b","geb"),
            "b_addr": v("b","addr"),
            "person_name": v("person","name"),
            "person_email": v("person","email"),
        })

        pdf_bytes = current.builder.build_pdf(
            form_data,
            i18n=current.i18n,
            pdf_options=_json_read("setup-config.json").get("pdf_options", {}),
            signature_bytes=signature_data
        )
        st.success(i18n.get("msg.created", "PDF created."))
        dl_name = current.i18n.get("btn.download", f"{current.key}.pdf")
        st.download_button(dl_name, data=pdf_bytes, file_name=f"{current.key}.pdf", mime="application/pdf")

# ============ Safe auto-run Streamlit when executed directly ============
if __name__ == "__main__":
    import os, sys
    if os.environ.get("APP_BOOTSTRAPPED") != "1":
        os.environ["APP_BOOTSTRAPPED"] = "1"
        port = os.environ.get("STREAMLIT_PORT", "8501")
        os.execv(sys.executable, [sys.executable, "-m", "streamlit", "run", __file__, "--server.port", port])
