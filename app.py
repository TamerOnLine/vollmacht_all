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
    errors = []
    for section in sc.get("sections", []):
        for fld in section.get("fields", []):
            if not fld.get("required"):
                continue
            k = f'{section["key"]}_{fld["key"]}'
            label = i18n_dict.get(fld.get("label_i18n", fld.get("key", "")), fld.get("key", ""))
            if fld.get("type") == "checkbox":
                if not bool(vals.get(k, False)):
                    errors.append(label)
            else:
                if not (str(vals.get(k, "") or "").strip()):
                    errors.append(label)
    return errors


def v(sec, key, vals):
    """Retrieve trimmed value from values dict."""
    return (vals.get(f"{sec}_{key}", "") or "").strip()

def _json_read(path):
    """Read JSON file safely."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}

st.set_page_config(page_title="Dynamic PDF Forms", page_icon="🧾", layout="centered")

# Sidebar: Language (UI language only)
lang_ui = st.sidebar.selectbox("Language / اللغة", ["de", "ar", "en"], index=0)

# Discover forms with preferred UI language
forms = discover_forms(preferred_lang=lang_ui)
if not forms:
    st.error("No forms found. Please add folders under ./forms/<form_key>/")
    st.stop()

# Sidebar: choose form
form_keys = list(forms.keys())
selected_key = st.sidebar.selectbox("Form / النموذج", form_keys, index=0)
current = forms[selected_key]

# UI i18n = user's chosen language
ui_i18n = current.i18n

# PDF i18n = ALWAYS German (fallback to UI if missing)
try:
    pdf_i18n = json.loads(Path(f"forms/{current.key}/i18n.de.json").read_text(encoding="utf-8"))
except FileNotFoundError:
    pdf_i18n = ui_i18n  # safe fallback

# Current form data
schema = current.schema
i18n = ui_i18n  # use UI language for all Streamlit text
st.title(i18n.get("app.title", current.name))

# Dynamic form UI
with st.form("dynamic_form"):
    values: dict[str, object] = {}

    for section in schema.get("sections", []):
        st.subheader(i18n.get(section.get("title_i18n", section.get("key", "")), section.get("key", "")))
        for fld in section.get("fields", []):
            label = i18n.get(fld.get("label_i18n", fld.get("key", "")), fld.get("key", ""))
            placeholder = fld.get("placeholder", "")
            key = f'{section["key"]}_{fld["key"]}'
            ftype = fld.get("type", "text")

            if ftype == "textarea":
                values[key] = st.text_area(label, placeholder=placeholder, key=key)
            elif ftype == "checkbox":
                values[key] = st.checkbox(label, value=False, key=key)
            else:
                values[key] = st.text_input(label, placeholder=placeholder, key=key)

    cols = st.columns(2)
    with cols[0]:
        stadt = st.text_input(
            i18n.get("field.ort", "Ort"),
            value=schema.get("misc", {}).get("stadt_default", "Berlin"),
            key="stadt"
        )
    with cols[1]:
        datum = st.text_input(
            i18n.get("field.datum", "Datum"),
            placeholder=schema.get("misc", {}).get("date_placeholder", ""),
            key="datum"
        )

    submitted = st.form_submit_button(i18n.get("btn.create", "PDF erstellen"))

# Signature UI (optional)
sig_required = schema.get("misc", {}).get("signature_required", True)
signature_data = None
sig_opts = {}

if sig_required:
    # Draw/upload UI text also uses the UI language
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
    errs = validate_required(values, schema, i18n)  # validate with UI labels
    if errs:
        st.error(i18n.get("validation.required", "Bitte Pflichtfelder ausfüllen.") + "\n- " + "\n- ".join(errs))
    else:
        form_data = {
            **{k: (values.get(k, "") if isinstance(values.get(k), bool) else (str(values.get(k, "") or "").strip()))
            for k in values.keys()},
            "stadt": (stadt or "").strip(),
            "datum": (datum or "").strip(),
        }

        # convenience mapped fields (some builders expect these)
        form_data.update({
            "vg_name": v("vg", "name", values),
            "vg_vorname": v("vg", "vorname", values),
            "vg_geb": v("vg", "geb", values),
            "vg_addr": v("vg", "addr", values),
            "b_name": v("b", "name", values),
            "b_vorname": v("b", "vorname", values),
            "b_geb": v("b", "geb", values),
            "b_addr": v("b", "addr", values),
            "person_name": v("person", "name", values),
            "person_email": v("person", "email", values),
        })

        base_opts = _json_read("setup-config.json").get("pdf_options", {})
        pdf_options = {**base_opts, **sig_opts}

        # IMPORTANT: PDF always in German
        pdf_bytes = current.builder.build_pdf(
            form_data,
            i18n=pdf_i18n,
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
