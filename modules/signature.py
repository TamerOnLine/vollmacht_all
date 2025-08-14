import streamlit as st
import numpy as np
import io
from PIL import Image as PILImage
from streamlit_drawable_canvas import st_canvas

def set_signature(signature: bytes | None) -> None:
    st.session_state["signature_bytes"] = signature

def get_signature_bytes() -> bytes | None:
    return st.session_state.get("signature_bytes", None)

def draw_signature_ui(i18n: dict):
    if "signature_bytes" not in st.session_state:
        st.session_state["signature_bytes"] = None

    draw_label = i18n.get("signature.mode.draw", "Mouse drawing")
    upload_label = i18n.get("signature.mode.upload", "Upload image")

    st.subheader(i18n.get("signature.title", "Unterschrift"))
    sig_mode = st.radio("", [draw_label, upload_label], horizontal=True)

    if sig_mode == draw_label:
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 0)",
            stroke_width=2,
            stroke_color="black",
            background_color="white",
            height=120,
            width=400,
            drawing_mode="freedraw",
            key="signature_canvas",
            update_streamlit=True,
            display_toolbar=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button(i18n.get("btn.accept_drawn", "Accept drawn signature")):
                if canvas_result.image_data is not None:
                    rgba = canvas_result.image_data.astype(np.uint8)
                    pil_img = PILImage.fromarray(rgba)
                    out = io.BytesIO()
                    pil_img.save(out, format="PNG")
                    set_signature(out.getvalue())
                    st.success("OK")
                else:
                    st.warning("No drawing.")
        with c2:
            if st.button(i18n.get("btn.clear", "Clear")):
                set_signature(None)
                st.info("Cleared.")
    else:
        uploaded = st.file_uploader(upload_label, type=["png", "jpg", "jpeg"])
        c1, c2 = st.columns(2)
        with c1:
            if uploaded:
                set_signature(uploaded.read())
                st.success("OK")
        with c2:
            if st.button(i18n.get("btn.clear", "Clear")):
                set_signature(None)
                st.info("Cleared.")

    if st.session_state["signature_bytes"]:
        st.image(st.session_state["signature_bytes"], caption="Signature preview", width=260)