from io import BytesIO
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, Indenter, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet

def build_pdf(data: dict, i18n: dict, pdf_options: dict, signature_bytes: bytes | None = None) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=pdf_options.get("leftMargin", 40),
        rightMargin=pdf_options.get("rightMargin", 40),
        topMargin=pdf_options.get("topMargin", 36),
        bottomMargin=pdf_options.get("bottomMargin", 36),
    )
    styles = getSampleStyleSheet()
    elems = [
        Paragraph(f"<b>{i18n.get(pdf_options.get('title_i18n', 'app.title'), 'Vollmacht')}</b>", styles["Title"]),
        Paragraph("zur Abholung und Beantragung des Aufenthaltstitels/Reiseausweises", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Ich:", styles["Normal"]),
        Paragraph("Vollmachtgeber", styles["Normal"]),
    ]

    table_style = TableStyle([
        ("BOX", (0,0), (-1,-1), 1, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.black),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ])

    tbl1 = Table([
        ["Name:", data.get("vg_name","")],
        ["Vorname:", data.get("vg_vorname","")],
        ["Geburtsdatum:", data.get("vg_geb","")],
        ["Anschrift:", data.get("vg_addr","")],
    ], colWidths=[100, 350]); tbl1.setStyle(table_style)

    tbl2 = Table([
        ["Name:", data.get("b_name","")],
        ["Vorname:", data.get("b_vorname","")],
        ["Geburtsdatum:", data.get("b_geb","")],
        ["Anschrift:", data.get("b_addr","")],
    ], colWidths=[100, 350]); tbl2.setStyle(table_style)

    elems += [tbl1, Spacer(1,12), Paragraph("bevollmächtige", styles["Normal"]),
              Paragraph("Bevollmächtigter/-r", styles["Normal"]), tbl2, Spacer(1,12)]

    elems.append(Paragraph(
        "den Aufenthaltstitel und Reiseausweis zu beantragen/abzuholen, unter Vorlage <u>meines</u> Personaldokuments.",
        styles["Normal"]
    ))
    elems.append(Paragraph(
        "<b>Hinweis:</b> Der Bevollmächtigte muss sich bei Vorsprache zur Abholung durch Vorlage eines eigenen Personaldokuments ausweisen.",
        styles["Normal"]
    ))
    elems.append(Spacer(1, 24))
    elems.append(Paragraph(f"{data.get('stadt','')}, den {data.get('datum','')}", styles["Normal"]))
    elems.append(Spacer(1, 18))

    # توقيع اختياري
    target_w = float(pdf_options.get("signature_width_pt", 180))
    max_h = float(pdf_options.get("signature_max_height_pt", 80))
    sig_block = []
    if signature_bytes:
        try:
            pil = PILImage.open(BytesIO(signature_bytes)).convert("RGBA")
            w, h = pil.size
            aspect = h / w if w else 1.0
            out_w = target_w
            out_h = min(max_h, out_w * aspect)
            sig_img = RLImage(BytesIO(signature_bytes), width=out_w, height=out_h, hAlign="LEFT")
            sig_block += [sig_img, Spacer(1, -12)]
        except Exception:
            pass

    sig_block += [Paragraph("_________________________", styles["Normal"]),
                  Paragraph("Unterschrift des Vollmachtgebers", styles["Normal"])]

    elems += [Indenter(left=0), KeepTogether(sig_block), Indenter(left=0)]
    doc.build(elems)
    buf.seek(0)
    return buf.read()
