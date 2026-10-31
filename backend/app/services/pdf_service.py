"""
PDF Generation Service using ReportLab for Brightloop Nexus.
Generates audit-ready, pixel-perfect invoices matching enterprise standards.
"""
import io
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.invoice import Invoice


class PDFInvoiceService:
    @staticmethod
    def generate_invoice_pdf(invoice: Invoice) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        story = []
        styles = getSampleStyleSheet()

        # Custom typography styles
        brand_style = ParagraphStyle(
            "Brand",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#4F46E5"),  # Indigo
        )
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            alignment=2,  # Right aligned
            textColor=colors.HexColor("#1E293B"),
        )
        meta_label = ParagraphStyle(
            "MetaLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
        )
        meta_val = ParagraphStyle(
            "MetaVal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0F172A"),
        )
        section_heading = ParagraphStyle(
            "Heading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#334155"),
        )
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            alignment=1,  # Center
            textColor=colors.HexColor("#94A3B8"),
        )

        # 1. Header (Logo / Brand Name & Invoice Title)
        header_table = Table(
            [
                [
                    Paragraph("Brightloop Nexus", brand_style),
                    Paragraph("INVOICE", title_style),
                ],
                [
                    Paragraph("Intelligent Subscription & Revenue Platform<br/>billing@brightloop.io", meta_val),
                    Paragraph(f"<b>Invoice #:</b> {invoice.invoice_number}<br/><b>Status:</b> {invoice.status}", ParagraphStyle("Right", parent=meta_val, alignment=2)),
                ]
            ],
            colWidths=[300, 240],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=15))

        # 2. Billed To & Metadata
        cust = invoice.customer
        cust_name = cust.full_name if cust else "Valued Customer"
        company_name = cust.company_name or ""
        email = cust.email or ""
        phone = cust.phone or ""
        addr = cust.billing_address or "N/A"
        tax_id = cust.tax_id or "N/A"

        billed_to_content = (
            f"<b>{cust_name}</b><br/>"
            f"{company_name + '<br/>' if company_name else ''}"
            f"Email: {email}<br/>"
            f"Phone: {phone}<br/>"
            f"Tax ID / VAT: {tax_id}<br/>"
            f"Address: {addr}"
        )

        invoice_details_content = (
            f"<b>Invoice Date:</b> {invoice.invoice_date.strftime('%Y-%m-%d')}<br/>"
            f"<b>Due Date:</b> {invoice.due_date.strftime('%Y-%m-%d')}<br/>"
            f"<b>Payment Terms:</b> {invoice.payment_terms}<br/>"
            f"<b>Subscription Ref:</b> {invoice.subscription.subscription_number if invoice.subscription else 'Ad-hoc'}<br/>"
        )

        meta_table = Table(
            [
                [Paragraph("BILLED TO", section_heading), Paragraph("INVOICE DETAILS", section_heading)],
                [Paragraph(billed_to_content, meta_val), Paragraph(invoice_details_content, meta_val)],
            ],
            colWidths=[300, 240],
        )
        meta_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))

        # 3. Line Items Table
        items_data = [
            [
                Paragraph("<b>Description</b>", meta_label),
                Paragraph("<b>Qty</b>", ParagraphStyle("Right", parent=meta_label, alignment=2)),
                Paragraph("<b>Unit Price ($)</b>", ParagraphStyle("Right", parent=meta_label, alignment=2)),
                Paragraph("<b>Amount ($)</b>", ParagraphStyle("Right", parent=meta_label, alignment=2)),
            ]
        ]

        for item in invoice.items:
            items_data.append([
                Paragraph(item.item_description, meta_val),
                Paragraph(str(item.quantity), ParagraphStyle("Right", parent=meta_val, alignment=2)),
                Paragraph(f"{item.unit_price:.2f}", ParagraphStyle("Right", parent=meta_val, alignment=2)),
                Paragraph(f"{item.subtotal:.2f}", ParagraphStyle("Right", parent=meta_val, alignment=2)),
            ])

        items_table = Table(items_data, colWidths=[280, 50, 100, 110])
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor("#CBD5E1")),
            ("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 15))

        # 4. Summary Totals Table
        summary_rows = [
            [Paragraph("Subtotal:", meta_label), Paragraph(f"${invoice.subtotal:.2f}", ParagraphStyle("Right", parent=meta_val, alignment=2))],
        ]

        if invoice.discount_amount > 0:
            summary_rows.append([
                Paragraph(f"Discount Applied:", meta_label),
                Paragraph(f"-${invoice.discount_amount:.2f}", ParagraphStyle("Right", parent=meta_val, alignment=2)),
            ])

        if invoice.tax_amount > 0:
            summary_rows.append([
                Paragraph("Taxes:", meta_label),
                Paragraph(f"+${invoice.tax_amount:.2f}", ParagraphStyle("Right", parent=meta_val, alignment=2)),
            ])

        summary_rows.extend([
            [Paragraph("<b>Total Amount:</b>", section_heading), Paragraph(f"<b>${invoice.total_amount:.2f}</b>", ParagraphStyle("Right", parent=section_heading, alignment=2))],
            [Paragraph("Amount Paid:", meta_label), Paragraph(f"${invoice.amount_paid:.2f}", ParagraphStyle("Right", parent=meta_val, alignment=2))],
            [Paragraph("<b>Balance Due:</b>", ParagraphStyle("Due", parent=section_heading, textColor=colors.HexColor("#DC2626"))),
             Paragraph(f"<b>${invoice.amount_due:.2f}</b>", ParagraphStyle("RightDue", parent=section_heading, alignment=2, textColor=colors.HexColor("#DC2626")))],
        ])

        summary_table = Table(summary_rows, colWidths=[140, 100])
        summary_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE", (0, 3), (-1, 3), 1, colors.HexColor("#CBD5E1")),
        ]))

        # Place summary on right side
        container_table = Table(
            [[Paragraph(f"<b>Notes & Payment Instructions:</b><br/>{invoice.notes or 'Thank you for your business. Please settle via bank transfer or credit card before the due date.'}", meta_val), summary_table]],
            colWidths=[300, 240],
        )
        container_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(container_table)
        story.append(Spacer(1, 40))

        # 5. Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=10))
        story.append(Paragraph("Brightloop Nexus Automated Revenue Engine — Official Tax Invoice", footer_style))

        doc.build(story)
        buffer.seek(0)
        return buffer

