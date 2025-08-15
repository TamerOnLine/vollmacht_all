# forms/obdachlosigkeit/builder.py
from io import BytesIO
from PIL import Image as PILImage, ImageChops
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, KeepTogether, Indenter
)
from reportlab.lib.styles import getSampleStyleSheet


# -------------------------
# Helpers
# -------------------------
def _bool(v) -> bool:
    s = (str(v or "")).strip().lower()
    return s in {"1", "true", "ja", "yes", "y", "on", "x", "✓", "checked"}

def _trim(img: PILImage.Image) -> PILImage.Image:
    if img.mode in ("LA", "RGBA"):
        bbox = img.split()[-1].getbbox()
        return img.crop(bbox) if bbox else img
    rgb = img.convert("RGB")
    diff = ImageChops.difference(rgb, PILImage.new("RGB", rgb.size, (255, 255, 255)))
    bbox = diff.getbbox()
    return img.crop(bbox) if bbox else img

# مربع اختيار فقط (بدون نص)
def _checkbox_box(checked: bool, size=12) -> Table:
    box = Table([["X" if checked else ""]], colWidths=[size], rowHeights=[size])
    box.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 1, colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("FONTSIZE", (0,0), (-1,-1), size),     # X أكبر
        ("LEADING", (0,0), (-1,-1), size),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    return box

# صف (مربع + نص) في جدول صغير مستقل
def _checkbox_row(label: str, checked: bool, *, size=12, label_width=150) -> Table:
    row = Table([[ _checkbox_box(checked, size=size), label ]],
                colWidths=[size+2, label_width], rowHeights=[size])
    row.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    return row

# عنوان قسم = مربع + عنوان على عرض الصفحة
def section_header(title_text: str, checked: bool):
    tbl = Table([[ _checkbox_box(checked, size=12), f"  {title_text}" ]],
                colWidths=[12, 508])  # 520 إجمالي
    tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TEXTCOLOR", (1,0), (1,0), colors.black),
    ]))
    return tbl


# -------------------------
# PDF Builder
# -------------------------
def build_pdf(
    data: dict,
    i18n: dict,
    pdf_options: dict,
    signature_bytes: bytes | None = None
) -> bytes:
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
    normal = styles["Normal"]
    title = styles["Title"]

    elems = []

    # Title
    elems.append(Paragraph(
        f"<b>{i18n.get(pdf_options.get('title_i18n','app.title'), 'Anzeige von unfreiwilliger Obdachlosigkeit')}</b>",
        title))
    elems.append(Spacer(1, 8))

    # Table style عام
    tstyle = TableStyle([
        ("BOX", (0,0), (-1,-1), 1, colors.black),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.black),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ])

    # ---- الصف العلوي: Name / Geburtsdatum / Angehörige ----
    has_rel = _bool(data.get("person_has_relatives"))
    relatives_line = (data.get("person_relatives_text") or "").strip()

    # جدول عمودي داخل الخلية: الخياران تحت بعض
    rel_vertical = Table([
        [_checkbox_row("keine Angehörige", not has_rel, size=12, label_width=150)],
        [_checkbox_row(f"Angehörige: {relatives_line}", has_rel, size=12, label_width=150)],
    ], colWidths=[180], rowHeights=[42, 42])
    rel_vertical.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE")]))

    top = Table([
        [i18n.get("person.name","Name, Vorname"),
         i18n.get("person.geb","Geburtsdatum"),
         "Angehörige"],
        [data.get("person_name",""),
         data.get("person_geb",""),
         rel_vertical]
    ], colWidths=[220, 120, 180])
    top.setStyle(tstyle)
    elems += [top, Spacer(1, 14)]

    # ---- أقسام النموذج ----
    def box_line(label_text: str, height_pt=None):
        if height_pt:
            tbl = Table([[label_text]], colWidths=[520], rowHeights=[height_pt])
        else:
            tbl = Table([[label_text]], colWidths=[520])
        tbl.setStyle(tstyle)
        return tbl


    # Erstzuweisung
    elems += [
        section_header(i18n.get("section.erst","Erstzuweisung"), _bool(data.get("erst_checked"))),
        Spacer(1, 4),
        Paragraph("Ich/ Meine Familie benötigt einen Platz im Wohnheim, um nicht auf der Straße schlafen zu müssen.", normal),
        Spacer(1, 4),
        Paragraph(i18n.get("erst.gruende", "Gründe …"), normal),
        box_line(data.get("erst_gruende", "")),
        Spacer(1, 10),
    ]

    # Zuweisung nach Unterbrechung
    elems += [
        section_header(i18n.get("section.unterb","Zuweisung nach Unterbrechung"), _bool(data.get("unterb_checked"))),
        Spacer(1, 4),
        Paragraph(i18n.get("unterb.gruende", "Gründe …"), normal),
        box_line(data.get("unterb_gruende", "")),
        Spacer(1, 10),
    ]

    # Verlängerung der Zuweisung
    endet = (data.get("verl_endet_am","") or "").strip()
    elems += [
        section_header(i18n.get("section.verl","Verlängerung der Zuweisung"), _bool(data.get("verl_checked"))),
        Spacer(1, 4),
        Paragraph(f"Die Zuweisung für das Wohnheim endet/e am: {endet}", normal),
        Paragraph("Es ist mir nicht gelungen, eine Wohnung anzumieten oder woanders unterzukommen.", normal),
        Spacer(1, 10),
    ]

    # Wechsel des Wohnheimes
    elems += [
        section_header(i18n.get("section.wechsel","Wechsel des Wohnheimes"), _bool(data.get("wechsel_checked"))),
        Spacer(1, 4),
        Paragraph(i18n.get("wechsel.gruende","Ich/Wir benötige/n aus folgenden Gründen einen neuen Wohnheimplatz"), normal),
        box_line(data.get("wechsel_gruende",""), height_pt=170.08),
    ]

    # Footer: Ort/Datum
    ort = data.get("stadt","")
    datum = data.get("datum","")
    elems.append(Paragraph(f"{i18n.get('field.ort','Ort')}: {ort}    {i18n.get('field.datum','Datum')}: {datum}", normal))
    elems.append(Spacer(1, 12))

    # Signature block
    sig_block = []
    if signature_bytes:
        try:
            pil = PILImage.open(BytesIO(signature_bytes)).convert("RGBA")
            if pdf_options.get("signature_trim", True):
                pil = _trim(pil)

            box_w = float(pdf_options.get("signature_box_w_pt", pdf_options.get("signature_width_pt", 180)))
            box_h = float(pdf_options.get("signature_box_h_pt", pdf_options.get("signature_max_height_pt", 80)))
            mode = pdf_options.get("signature_scale_mode", "fit")
            align = pdf_options.get("signature_align", "LEFT")

            if mode == "stretch":
                out_w, out_h = box_w, box_h
            else:
                w, h = pil.size
                aspect = (h / w) if w else 1.0
                out_w = box_w
                out_h = out_w * aspect
                if out_h > box_h:
                    out_h = box_h
                    out_w = out_h / aspect

            tmp = BytesIO()
            pil.save(tmp, format="PNG")
            tmp.seek(0)
            sig_img = RLImage(tmp, width=out_w, height=out_h,
                              hAlign=align if align in ("LEFT","CENTER","RIGHT") else "LEFT")
            sig_block += [sig_img, Spacer(1, -12)]
        except Exception:
            pass

    sig_block += [
        Paragraph("_________________________", normal),
        Paragraph("Unterschrift der wohnungslosen Person", normal)
    ]
    elems += [Indenter(left=0), KeepTogether(sig_block), Indenter(left=0)]

    # Build
    doc.build(elems)
    buf.seek(0)
    return buf.read()
