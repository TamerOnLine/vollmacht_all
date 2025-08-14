import streamlit as st
from modules.i18n import LANGS, tr
from modules.config import load_schema_config
from modules.signature import draw_signature_ui, get_signature_bytes
from modules.pdf_builder import build_vollmacht_pdf_bytes

cfg, schema, I18N_PDF = load_schema_config()
lang_choice = st.sidebar.selectbox("Language / اللغة", list(LANGS.keys()), index=0)
i18n = LANGS[lang_choice]

st.title(tr("app.title", i18n, "Vollmacht – PDF Generator"))

# ========== Dynamic Form ==========
with st.form("vollmacht_form"):
    values = {}
    for section in schema.get("sections", []):
        st.subheader(tr(section.get("title_i18n", section.get("key", "")), i18n, section.get("key", "")))
        for fld in section.get("fields", []):
            label = tr(fld.get("label_i18n", fld.get("key", "")), i18n, fld.get("key", ""))
            placeholder = fld.get("placeholder", "")
            key = f'{section["key"]}_{fld["key"]}'
            values[key] = (
                st.text_area(label, placeholder=placeholder)
                if fld.get("type") == "textarea"
                else st.text_input(label, placeholder=placeholder)
            )

    cols = st.columns(2)
    with cols[0]:
        stadt = st.text_input(tr("field.ort", i18n, "Ort"), value=schema.get("misc", {}).get("stadt_default", "Berlin"))
    with cols[1]:
        datum = st.text_input(tr("field.datum", i18n, "Datum"), placeholder=schema.get("misc", {}).get("date_placeholder", ""))

    submitted = st.form_submit_button(tr("btn.create", i18n, "PDF erstellen"))

# ========== Signature UI ==========
draw_signature_ui(i18n)
signature_data = get_signature_bytes()

# ========== Validate and Generate PDF ==========
def validate_required(vals, sc, i18n_dict):
    errors = []
    for section in sc.get("sections", []):
        for fld in section.get("fields", []):
            if fld.get("required"):
                k = f'{section["key"]}_{fld["key"]}'
                label = tr(fld.get("label_i18n", fld.get("key", "")), i18n_dict, fld.get("key", ""))
                if not vals.get(k, "").strip():
                    errors.append(label)
    return errors

def v(sec, key): return (values.get(f"{sec}_{key}", "") or "").strip()

if submitted:
    errs = validate_required(values, schema, i18n)
    if errs:
        st.error(tr("validation.required", i18n, "Bitte Pflichtfelder ausfüllen.") + "\\n- " + "\\n- ".join(errs))
    else:
        form_data = {
            "vg_name": v("vg", "name"), "vg_vorname": v("vg", "vorname"),
            "vg_geb": v("vg", "geb"), "vg_addr": v("vg", "addr"),
            "b_name": v("b", "name"), "b_vorname": v("b", "vorname"),
            "b_geb": v("b", "geb"), "b_addr": v("b", "addr"),
            "stadt": stadt.strip(), "datum": datum.strip()
        }
        pdf_bytes = build_vollmacht_pdf_bytes(form_data, signature_bytes=signature_data, i18n=I18N_PDF, pdf_options=cfg.get("pdf_options", {}))
        st.success(tr("msg.created", I18N_PDF, "PDF created."))
        st.download_button(tr("btn.download", I18N_PDF, "Download Vollmacht.pdf"), data=pdf_bytes, file_name="vollmacht_formular.pdf", mime="application/pdf")

# ============ Safe auto-run Streamlit when executed directly ============
if __name__ == "__main__":
    import os, sys

    # امنع الحلقة: نفّذ execv مرة واحدة فقط
    if os.environ.get("APP_BOOTSTRAPPED") != "1":
        os.environ["APP_BOOTSTRAPPED"] = "1"
        port = os.environ.get("STREAMLIT_PORT", "8501")
        os.execv(sys.executable, [
            sys.executable, "-m", "streamlit", "run", __file__, "--server.port", port
        ])

