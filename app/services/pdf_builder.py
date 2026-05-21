from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import CalculationProject
from app.schemas import ProjectCalculation


def _build_base_pdf(title: str, project: CalculationProject, calc: ProjectCalculation, tier_index: int) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Проект: {project.name}", styles["Normal"]),
        Paragraph(f"Заказчик: {project.customer_name}", styles["Normal"]),
        Paragraph(f"Исполнитель: {project.contractor_name}", styles["Normal"]),
        Spacer(1, 12),
    ]

    header = ["КБ", "Продукция", "Тираж", "Цена за ед. с НДС", "Сумма с НДС"]
    rows = [header]
    grand_total = 0.0

    for assembly in calc.assemblies:
        tier = assembly.tiers[tier_index]
        rows.append(
            [
                assembly.code,
                assembly.product_name,
                tier.quantity,
                f"{tier.unit_price_with_vat:,.2f}",
                f"{tier.total_with_vat:,.2f}",
            ]
        )
        grand_total += tier.total_with_vat

    rows.append(["", "", "", "Итого", f"{grand_total:,.2f}"])
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9EDF5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"НДС: {project.vat_percent:.2f}%", styles["Normal"]))
    story.append(Paragraph("Документ сформирован автоматически.", styles["Italic"]))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def build_commercial_offer_pdf(project: CalculationProject, calc: ProjectCalculation, tier_index: int = 0) -> bytes:
    return _build_base_pdf("Коммерческое предложение (с НДС)", project, calc, tier_index)


def build_invoice_pdf(project: CalculationProject, calc: ProjectCalculation, tier_index: int = 0) -> bytes:
    return _build_base_pdf("Счет на оплату (с НДС)", project, calc, tier_index)
