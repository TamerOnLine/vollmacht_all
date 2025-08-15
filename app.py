import json
import os
import sys
from pathlib import Path

import streamlit as st
from modules.form_loader import discover_forms
from modules.signature import (
    draw_signature_ui,
    get_signature_bytes,
    get_signature_meta,
)

def validate_required(vals, sc, i18n_dict):
    """Validate required fields in the form schema.

    Args:
        vals (dict): Dictionary of user-provided values.
        sc (dict): Schema defining required fields.
        i18n_dict (dict): Dictionary of localized labels.

    Returns:
        list: Labels of missing required fields.
    """
    errors = []
    for section in sc.get("sections", []):
        for fld in section.get("fields", []):
            if fld.get("required"):
                k = f'{section["key"]}_{fld["key"]}'
                label = i18n_dict.get(fld.get("label_i18n", fld.get("key", "")), fld.get("key", ""))
                if not (vals.get(k, "") or "").strip():
                    errors.append(label)
    return errors

def v(sec, key):
    """Retrieve trimmed value from values dict.

    Args:
        sec (str): Section key.
        key (str): Field key.

    Returns:
        str: Trimmed value or empty string.
    """
    return (values.get(f"{sec}_{key}", "") or "").strip()

def _json_read(path):
    """Read JSON file safely.

    Args:
        path (str): Path to JSON file.

    Returns:
        dict: Parsed JSON content or empty dict if file not found.
    """
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}

st.set_page_config(page_title="Dynamic PDF Forms", page_icon="🧾", layout="centered")

# Sidebar: Language
lang_ui = st.sidebar.selectbox("Language / اللغة", ["de", "ar", "en"], index=0)

# Discover forms
forms = discover_forms(preferred_lang=lang_ui)
if not forms:
    st.error("No forms found. Please add folders under ./forms/<form_key>/")
    st.stop()

# Sidebar: choose form
form_keys = list(forms.keys())
selected_key = st.sidebar.selectbox("Form / النموذج", form_keys, index=0)
current = forms[selected_key]

# Current form data
schema = current.schema
i18n = current.i18n
st.title(i18n.get("app.title", current.name))

# Dynamic form UI
with st.form("dynamic_form"):
    values: dict[str, str] = {}

    for section in schema.get("sections", []):
        st.subheader(i18n.get(section.get("title_i18n", section.get("key", "")), section.get("key", "")))
        for fld in section.get("fields", []):
            label = i18n.get(fld.get("label_i18n", fld.get("key", "")), fld.get("key", ""))
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

# Signature UI (optional)
sig_required = schema.get("misc", {}).get("signature_required", True)
signature_data = None
sig_opts = {}

if sig_required:
    draw_signature_ui(i18n)
    signature_data = get_signature_bytes()
    meta = get_signature_meta()

    if signature_data and meta.get("source") == "upload":
        st.markdown("### 📀 حجم صورة التوقيع (للصور المرفوعة)")
        CM_TO_PT = 28.3465
        w0, h0 = meta.get("size_px") or (None, None)

        keep_ratio = st.checkbox("حافظ على النسبة", True)

        col_a, col_b = st.columns(2)
        with col_a:
            width_cm = st.number_input("العرض (سم)", min_value=0.5, max_value=20.0, value=2.0, step=0.1)

        if keep_ratio and (w0 and h0 and w0 > 0):
            height_cm = width_cm * (h0 / w0)
            st.caption(f"الارتفاع المحسوب ≈ {height_cm:.2f} سم")
        else:
            with col_b:
                height_cm = st.number_input("الارتفاع (سم)", min_value=0.5, max_value=20.0, value=3.0, step=0.1)

        scale_mode = st.selectbox("طريقة الملاءمة", ["fit", "stretch"], index=0)
        align = st.selectbox("المحاذاة", ["LEFT", "CENTER", "RIGHT"], index=0)
        trim = st.checkbox("قصّ الحواف البيضاء", True)

        sig_opts = {
            "signature_box_w_pt": width_cm * CM_TO_PT,
            "signature_box_h_pt": height_cm * CM_TO_PT,
            "signature_scale_mode": scale_mode,
            "signature_align": align,
            "signature_trim": trim,
        }

# Generate PDF
if submitted:
    errs = validate_required(values, schema, i18n)
    if errs:
        st.error(i18n.get("validation.required", "Bitte Pflichtfelder ausfüllen.") + "\n- " + "\n- ".join(errs))
    else:
        form_data = {
            **{k: (values.get(k, "") or "").strip() for k in values.keys()},
            "stadt": stadt.strip(),
            "datum": datum.strip(),
        }
        form_data.update({
            "vg_name": v("vg", "name"), "vg_vorname": v("vg", "vorname"),
            "vg_geb": v("vg", "geb"), "vg_addr": v("vg", "addr"),
            "b_name": v("b", "name"), "b_vorname": v("b", "vorname"),
            "b_geb": v("b", "geb"), "b_addr": v("b", "addr"),
            "person_name": v("person", "name"),
            "person_email": v("person", "email"),
        })

        base_opts = _json_read("setup-config.json").get("pdf_options", {})
        pdf_options = {**base_opts, **sig_opts}

        pdf_bytes = current.builder.build_pdf(
            form_data,
            i18n=current.i18n,
            pdf_options=pdf_options,
            signature_bytes=signature_data
        )
        st.success(i18n.get("msg.created", "PDF created."))
        dl_name = i18n.get("btn.download", f"{current.key}.pdf")
        st.download_button(dl_name, data=pdf_bytes, file_name=f"{current.key}.pdf", mime="application/pdf")

# Safe auto-run with Streamlit
if __name__ == "__main__":
    if os.environ.get("APP_BOOTSTRAPPED") != "1":
        os.environ["APP_BOOTSTRAPPED"] = "1"
        port = os.environ.get("STREAMLIT_PORT", "8501")
        os.execv(sys.executable, [sys.executable, "-m", "streamlit", "run", __file__, "--server.port", port])
