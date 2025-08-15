from io import BytesIO
from PIL import Image as PILImage, ImageChops
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, Indenter, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet


def _trim_whitespace(img: PILImage.Image) -> PILImage.Image:
    """
    Remove white or transparent margins from an image.

    If the image has an alpha channel, it uses it to determine the bounding box.
    Otherwise, it compares the image against a white background to detect margins.

    Args:
        img (PILImage.Image): The input image.

    Returns:
        PILImage.Image: The cropped image with margins removed if found.
    """
    if img.mode in ("LA", "RGBA"):
        alpha = img.split()[-1]
        bbox = alpha.getbbox()
        return img.crop(bbox) if bbox else img

    rgb = img.convert("RGB")
    bg = PILImage.new("RGB", rgb.size, (255, 255, 255))
    diff = ImageChops.difference(rgb, bg)
    bbox = diff.getbbox()
    return img.crop(bbox) if bbox else img


def build_pdf(
    data: dict,
    i18n: dict,
    pdf_options: dict,
    signature_bytes: bytes | None = None
) -> bytes:
    """
    Generate a PDF document for an authorization form.

    Args:
        data (dict): Dictionary containing form data fields such as names, addresses, and dates.
        i18n (dict): Internationalization dictionary for localized titles or labels.
        pdf_options (dict): PDF configuration including margins, signature box settings, and scaling.
        signature_bytes (bytes | None): Optional PNG/JPEG signature image in bytes.

    Returns:
        bytes: The generated PDF file content as bytes.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=pdf_options.get("leftMargin", 40),
        rightMargin=pdf_options.get("rightMargin", 40),
        topMargin=pdf_options.get("topMargin", 36),
        bottomMargin=pdf_options.get("bottomMargin", 36),
    )

    styles = getSampleStyleSheet()
    elems = [
        Paragraph(
            f"<b>{i18n.get(pdf_options.get('title_i18n', 'app.title'), 'Vollmacht')}</b>",
            styles["Title"]
        ),
        Paragraph(
            "zur Abholung und Beantragung des Aufenthaltstitels/Reiseausweises",
            styles["Normal"]
        ),
        Spacer(1, 12),
        Paragraph("Ich:", styles["Normal"]),
        Paragraph("Vollmachtgeber", styles["Normal"]),
    ]

    table_style = TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])

    tbl1 = Table([
        ["Name:", data.get("vg_name", "")],
        ["Vorname:", data.get("vg_vorname", "")],
        ["Geburtsdatum:", data.get("vg_geb", "")],
        ["Anschrift:", data.get("vg_addr", "")],
    ], colWidths=[100, 350])
    tbl1.setStyle(table_style)

    tbl2 = Table([
        ["Name:", data.get("b_name", "")],
        ["Vorname:", data.get("b_vorname", "")],
        ["Geburtsdatum:", data.get("b_geb", "")],
        ["Anschrift:", data.get("b_addr", "")],
    ], colWidths=[100, 350])
    tbl2.setStyle(table_style)

    elems += [
        tbl1,
        Spacer(1, 12),
        Paragraph("bevollmächtige", styles["Normal"]),
        Paragraph("Bevollmächtigter/-r", styles["Normal"]),
        tbl2,
        Spacer(1, 12),
    ]

    elems.append(Paragraph(
        "den Aufenthaltstitel und Reiseausweis zu beantragen/abzuholen, "
        "unter Vorlage <u>meines</u> Personaldokuments.",
        styles["Normal"]
    ))
    elems.append(Paragraph(
        "<b>Hinweis:</b> Der Bevollmächtigte muss sich bei Vorsprache zur "
        "Abholung durch Vorlage eines eigenen Personaldokuments ausweisen.",
        styles["Normal"]
    ))
    elems.append(Spacer(1, 24))
    elems.append(Paragraph(
        f"{data.get('stadt', '')}, den {data.get('datum', '')}",
        styles["Normal"]
    ))
    elems.append(Spacer(1, 18))

    # Signature block
    sig_block = []
    if signature_bytes:
        try:
            pil = PILImage.open(BytesIO(signature_bytes)).convert("RGBA")

            box_w = float(pdf_options.get(
                "signature_box_w_pt",
                pdf_options.get("signature_width_pt", 56.7)
            ))
            box_h = float(pdf_options.get(
                "signature_box_h_pt",
                pdf_options.get("signature_max_height_pt", 85.05)
            ))

            scale_mode = pdf_options.get("signature_scale_mode", "fit")
            align = pdf_options.get("signature_align", "LEFT")
            do_trim = bool(pdf_options.get("signature_trim", True))

            if do_trim:
                pil = _trim_whitespace(pil)

            if scale_mode == "stretch":
                out_w, out_h = box_w, box_h
            else:
                w, h = pil.size
                aspect = (h / w) if w else 1.0
                out_w = box_w
                out_h = out_w * aspect
                if out_h > box_h:
                    out_h = box_h
                    out_w = out_h / aspect

            temp = BytesIO()
            pil.save(temp, format="PNG")
            temp.seek(0)

            sig_img = RLImage(
                temp,
                width=out_w,
                height=out_h,
                hAlign=align if align in ("LEFT", "CENTER", "RIGHT") else "LEFT"
            )
            sig_block += [sig_img, Spacer(1, -12)]
        except Exception:
            pass

    sig_block += [
        Paragraph("_________________________", styles["Normal"]),
        Paragraph("Unterschrift des Vollmachtgebers", styles["Normal"])
    ]

    elems += [Indenter(left=0), KeepTogether(sig_block), Indenter(left=0)]

    doc.build(elems)
    buf.seek(0)
    return buf.read()
