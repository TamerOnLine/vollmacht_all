import io
import numpy as np
import streamlit as st
from PIL import Image as PILImage
from streamlit_drawable_canvas import st_canvas


def set_signature_meta(
    source: str | None = None,
    size_px: tuple[int, int] | None = None
) -> None:
    """Set the metadata for the signature in Streamlit session state.

    Args:
        source (str | None): The source of the signature ("draw" or "upload").
        size_px (tuple[int, int] | None): The width and height of the signature in pixels.
    """
    st.session_state["signature_meta"] = {
        "source": (
            source if source is not None
            else st.session_state.get("signature_meta", {}).get("source")
        ),
        "size_px": (
            size_px if size_px is not None
            else st.session_state.get("signature_meta", {}).get("size_px")
        ),
    }


def get_signature_meta() -> dict:
    """Retrieve the signature metadata from session state.

    Returns:
        dict: Dictionary containing 'source' and 'size_px'.
    """
    return st.session_state.get(
        "signature_meta", {"source": None, "size_px": None}
    )


def set_signature(signature: bytes | None) -> None:
    """Store the signature image bytes in session state.

    Args:
        signature (bytes | None): Signature image data in bytes.
    """
    st.session_state["signature_bytes"] = signature


def get_signature_bytes() -> bytes | None:
    """Retrieve the signature image bytes from session state.

    Returns:
        bytes | None: The stored signature image bytes.
    """
    return st.session_state.get("signature_bytes", None)


def draw_signature_ui(i18n: dict) -> None:
    """Render the UI for drawing or uploading a signature.

    Args:
        i18n (dict): Dictionary containing localized strings for UI labels.
    """
    # Initialize state if not already present
    if "signature_bytes" not in st.session_state:
        st.session_state["signature_bytes"] = None
    if "signature_meta" not in st.session_state:
        st.session_state["signature_meta"] = {"source": None, "size_px": None}

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
                    set_signature_meta(source="draw", size_px=pil_img.size)
                    st.success("OK")
                else:
                    st.warning("No drawing.")
        with c2:
            if st.button(i18n.get("btn.clear", "Clear")):
                set_signature(None)
                set_signature_meta(source=None, size_px=None)
                st.info("Cleared.")

    else:
        uploaded = st.file_uploader(upload_label, type=["png", "jpg", "jpeg"])
        c1, c2 = st.columns(2)
        with c1:
            if uploaded:
                data = uploaded.read()
                set_signature(data)
                try:
                    w, h = PILImage.open(io.BytesIO(data)).size
                except Exception:
                    w, h = (None, None)
                set_signature_meta(source="upload", size_px=(w, h))
                st.success("OK")
        with c2:
            if st.button(i18n.get("btn.clear", "Clear")):
                set_signature(None)
                set_signature_meta(source=None, size_px=None)
                st.info("Cleared.")

    if st.session_state["signature_bytes"]:
        st.image(
            st.session_state["signature_bytes"],
            caption="Signature preview",
            width=260
        )
