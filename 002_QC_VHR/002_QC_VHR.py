"""
Sparker - PDF Report Generator
Streamlit web app для создания PDF-отчётов по обработанным сейсмическим линиям
(very high resolution seismic, sparker).
"""

import io
import os
from datetime import datetime

import streamlit as st
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ----------------------------- PDF generation ---------------------------------

PROJECT_NAME = "Sparker"


def build_pdf(
    output_path: str,
    line_name: str,
    date: str,
    processor: str,
    map_bytes: bytes,
    geometry_bytes: bytes,
    section_bytes: bytes,
) -> None:
    """Собирает PDF отчёт и сохраняет в output_path."""

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=f"{PROJECT_NAME} - {line_name}",
    )

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Title"],
        fontSize=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1f3a5f"),
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1f3a5f"),
        spaceBefore=10,
        spaceAfter=6,
    )

    story = []

    # Шапка проекта
    story.append(Paragraph(PROJECT_NAME, header_style))

    # Таблица с метаданными
    meta_data = [
        ["Line name:", line_name],
        ["Date:", date],
        ["Processor:", processor],
    ]
    meta_table = Table(meta_data, colWidths=[4 * cm, 12.4 * cm])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f4f6fa")),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # Картинки с подписями
    def add_image(img_bytes: bytes, caption: str, page_break_after: bool = True) -> None:
        story.append(Paragraph(caption, section_style))

        pil_img = PILImage.open(io.BytesIO(img_bytes))
        img_w, img_h = pil_img.size

        max_w = 17 * cm
        max_h = 22 * cm
        ratio = min(max_w / img_w, max_h / img_h)
        new_w = img_w * ratio
        new_h = img_h * ratio

        story.append(Image(io.BytesIO(img_bytes), width=new_w, height=new_h))

        if page_break_after:
            story.append(PageBreak())
        else:
            story.append(Spacer(1, 0.4 * cm))

    add_image(map_bytes, "Map", page_break_after=True)
    add_image(geometry_bytes, "Geometry check", page_break_after=True)
    add_image(section_bytes, "Section", page_break_after=False)

    doc.build(story)


# ----------------------------- Streamlit UI -----------------------------------

st.set_page_config(page_title=f"{PROJECT_NAME} - Report Generator", layout="centered")

st.markdown(
    f"""
    <div style="text-align:center; padding: 12px 0 4px 0;">
        <h1 style="color:#1f3a5f; margin-bottom:0;">{PROJECT_NAME}</h1>
        <p style="color:#666; margin-top:4px;">PDF report generator for processed seismic lines</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# Текстовые поля
line_name = st.text_input("Line name", placeholder="e.g. L-001")
date = st.text_input("Date", value=datetime.now().strftime("%Y-%m-%d"))
processor = st.text_input("Processor", placeholder="Name Surname")

st.markdown("#### Images")
map_file = st.file_uploader("Map", type=["png", "jpg", "jpeg"], key="map")
geometry_file = st.file_uploader("Geometry check", type=["png", "jpg", "jpeg"], key="geom")
section_file = st.file_uploader("Section", type=["png", "jpg", "jpeg"], key="sec")

st.markdown("#### Output")
output_folder = st.text_input("Output folder", value="./output")

# Кнопка генерации
generate = st.button("Generate PDF", type="primary", use_container_width=True)

if generate:
    missing_text = [n for n, v in [("Line name", line_name), ("Date", date), ("Processor", processor)] if not v.strip()]
    missing_img = [n for n, v in [("Map", map_file), ("Geometry check", geometry_file), ("Section", section_file)] if v is None]

    if missing_text:
        st.error(f"Заполни текстовые поля: {', '.join(missing_text)}")
    elif missing_img:
        st.error(f"Загрузи изображения: {', '.join(missing_img)}")
    else:
        try:
            os.makedirs(output_folder, exist_ok=True)
            safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in line_name)
            file_name = f"{PROJECT_NAME}_{safe_name}.pdf"
            output_path = os.path.join(output_folder, file_name)

            build_pdf(
                output_path=output_path,
                line_name=line_name,
                date=date,
                processor=processor,
                map_bytes=map_file.getvalue(),
                geometry_bytes=geometry_file.getvalue(),
                section_bytes=section_file.getvalue(),
            )

            st.success(f"PDF сохранён: `{os.path.abspath(output_path)}`")

            with open(output_path, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f.read(),
                    file_name=file_name,
                    mime="application/pdf",
                    use_container_width=True,
                )
        except Exception as e:
            st.error(f"Ошибка при создании PDF: {e}")
