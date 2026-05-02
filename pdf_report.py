from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from datetime import datetime

ORANGE = HexColor("#f5a623")
RED = HexColor("#e84545")
GREEN = HexColor("#3de888")
DARK = HexColor("#1a1a1a")
GRAY = HexColor("#666666")
WHITE = HexColor("#ffffff")
LIGHT_GRAY = HexColor("#f5f5f5")

def get_severity_color(severity):
    if severity == "HIGH": return RED
    if severity == "MEDIUM": return ORANGE
    return GREEN

def generate_pdf(machine_name, machine_type, machine_age, suara, getaran, suhu, performa, gejala_lain, jam_operasi, last_maintenance, beban, ai_result):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=22, textColor=DARK, spaceAfter=2*mm, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, textColor=GRAY, spaceAfter=6*mm, alignment=TA_CENTER)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=11, textColor=DARK, fontName='Helvetica-Bold', spaceBefore=6*mm, spaceAfter=3*mm, borderPadding=(0,0,2,0))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, textColor=DARK, leading=15, spaceAfter=3*mm)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=GRAY, alignment=TA_CENTER)

    elements = []
    severity = ai_result.get("severity", "MEDIUM")
    sev_color = get_severity_color(severity)
    now = datetime.now().strftime("%d %B %Y, %H:%M WIB")

    # Header
    elements.append(Paragraph("⚙️ MaintainAI", title_style))
    elements.append(Paragraph("Predictive Maintenance Diagnostic Report", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=ORANGE, spaceAfter=5*mm))

    # Severity
    sev_label = "🔴 KRITIS" if severity == "HIGH" else "🟡 PERHATIAN" if severity == "MEDIUM" else "🟢 AMAN"
    sev_style = ParagraphStyle('Sev', parent=styles['Normal'], fontSize=13, fontName='Helvetica-Bold', textColor=sev_color, alignment=TA_CENTER, spaceAfter=5*mm)
    elements.append(Paragraph(f"Severity: {sev_label} ({severity})", sev_style))

    # Machine info table
    elements.append(Paragraph("Informasi Mesin", section_style))
    info_data = [
        ["Nama Mesin", machine_name, "Tipe Mesin", machine_type],
        ["Usia Mesin", f"{machine_age} tahun", "Jam Operasi/Hari", f"{jam_operasi} jam"],
        ["Terakhir Maintenance", f"{last_maintenance} bulan lalu", "Beban Kerja", beban],
    ]
    t = Table(info_data, colWidths=[35*mm, 50*mm, 40*mm, 45*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY), ('BACKGROUND', (2, 0), (2, -1), LIGHT_GRAY),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9), ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)

    # Symptoms table
    elements.append(Paragraph("Gejala yang Diamati", section_style))
    sym_data = [
        ["Suara Abnormal", suara, "Getaran", getaran],
        ["Suhu", suhu, "Performa", performa],
    ]
    t2 = Table(sym_data, colWidths=[35*mm, 50*mm, 40*mm, 45*mm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY), ('BACKGROUND', (2, 0), (2, -1), LIGHT_GRAY),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9), ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t2)
    if gejala_lain:
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(f"<b>Observasi Tambahan:</b> {gejala_lain}", body_style))

    # AI results
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceBefore=4*mm, spaceAfter=2*mm))
    elements.append(Paragraph("Hasil Diagnosa AI", section_style))

    elements.append(Paragraph("<b>Kemungkinan Kerusakan:</b>", body_style))
    elements.append(Paragraph(ai_result.get("kemungkinan_kerusakan", "-"), body_style))

    elements.append(Paragraph("<b>Komponen Berisiko:</b>", body_style))
    komps = ai_result.get("komponen_berisiko", [])
    elements.append(Paragraph("• " + "  • ".join(komps) if komps else "-", body_style))

    elements.append(Paragraph("<b>Rekomendasi Aksi:</b>", body_style))
    elements.append(Paragraph(ai_result.get("rekomendasi_aksi", "-"), body_style))

    elements.append(Paragraph("<b>Status Operasional:</b>", body_style))
    elements.append(Paragraph(ai_result.get("prioritas", "-"), body_style))

    elements.append(Paragraph("<b>Estimasi Waktu Perbaikan:</b>", body_style))
    elements.append(Paragraph(ai_result.get("estimasi_waktu", "-"), body_style))

    elements.append(Paragraph("<b>Tips Pencegahan:</b>", body_style))
    elements.append(Paragraph(ai_result.get("tips_pencegahan", "-"), body_style))

    # Footer
    elements.append(Spacer(1, 10*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=3*mm))
    elements.append(Paragraph(f"MaintainAI v2.0 · Polman Bandung · Laporan dibuat pada {now}", footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
