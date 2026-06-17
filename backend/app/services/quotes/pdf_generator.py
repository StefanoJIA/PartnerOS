"""ReportLab PDF generation for customer quotes (D6.4)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ApiError, VALIDATION_ERROR
from app.models import User
from app.models.customer_quotes import QuotePdfExport
from app.services.quotes.pdf_data_builder import PDF_SAFETY, build_quote_pdf_data
from app.services.quotes.quote_service import get_quote

BACKEND_ROOT = Path(__file__).resolve().parents[3]
MARGIN = 0.65 * inch
RESERVED_EXPORT_TYPES = {"partner_pdf", "summary_pdf", "internal_pdf"}


def quote_pdf_storage_dir(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    raw = (settings.LOCAL_STORAGE_PATH or "").strip()
    base = Path(raw) if raw else BACKEND_ROOT / "storage"
    path = base / "quote_pdfs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _money(currency: str, value: str) -> str:
    if str(value or "").upper() == "N/A":
        return "N/A"
    try:
        num = float(value)
        return f"{currency} {num:,.2f}"
    except (TypeError, ValueError):
        return f"{currency} {value}"


def _pdf_filename(quote_number: str, version_number: int | None) -> str:
    safe_num = quote_number.replace("/", "-").replace(" ", "_")
    v = version_number if version_number is not None else 1
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"Quote_{safe_num}_v{v}_{stamp}.pdf"


def _render_pdf_file(data: dict[str, Any], output_path: Path) -> None:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=14, spaceAfter=6)
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=normal, fontSize=9, leading=11)
    right = ParagraphStyle("Right", parent=small, alignment=TA_RIGHT)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    story: list[Any] = []

    company = data["company_profile"]
    quote = data["quote"]
    header_left = Paragraph(
        f"<b>{company['brand']}</b><br/>{company['address_line']}"
        + (f"<br/>{company['website']}" if company.get("website") else "")
        + (f"<br/>{company['phone']}" if company.get("phone") else ""),
        small,
    )
    header_right = Paragraph(
        f"<b>Quote #:</b> {quote['quote_number']}<br/>"
        f"<b>Date:</b> {quote['quote_date']}<br/>"
        f"<b>Valid Until:</b> {quote['valid_until']}",
        right,
    )
    story.append(Table([[header_left, header_right]], colWidths=[3.5 * inch, 3.5 * inch]))
    story.append(Spacer(1, 12))

    bill = data["bill_to"]
    ship = data["ship_to"]
    addr_table = Table(
        [
            [Paragraph("<b>Bill To</b>", small), Paragraph("<b>Ship To</b>", small)],
            [
                Paragraph(
                    f"{bill.get('company', '')}<br/>{bill.get('contact', '')}<br/>{bill.get('address', '')}",
                    small,
                ),
                Paragraph(
                    f"{ship.get('company', '')}<br/>{ship.get('contact', '')}<br/>{ship.get('address', '')}",
                    small,
                ),
            ],
        ],
        colWidths=[3.5 * inch, 3.5 * inch],
    )
    addr_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(addr_table)
    story.append(Spacer(1, 12))

    meta_rows = [
        ["Payment Terms", data["terms"].get("payment_terms") or "Subject to confirmation"],
        ["Shipping Terms", data["terms"].get("shipping_terms") or "Subject to confirmation"],
    ]
    if quote.get("default_incoterm"):
        meta_rows.append(["Incoterm", quote["default_incoterm"]])
    meta = Table(meta_rows, colWidths=[1.5 * inch, 5.5 * inch])
    meta.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(meta)
    story.append(Spacer(1, 12))

    currency = data["totals"].get("currency") or quote.get("currency") or "USD"
    has_interval_pricing = any(li.get("interval_quote_table") for li in data["line_items"])
    if has_interval_pricing:
        table_header = ["#", "Partner", "Product", "Description", "Reference Qty", "Reference Incoterm"]
    else:
        table_header = ["#", "Partner", "Product", "Description", "Qty", "Incoterm", "Unit Price", "Total"]
    table_data: list[list[Any]] = [table_header]
    for li in data["line_items"]:
        base_cells: list[Any] = [
            str(li.get("line_number") or ""),
            li.get("partner") or "",
            Paragraph(str(li.get("product_name") or ""), small),
            Paragraph(str(li.get("description") or ""), small),
            str(li.get("quantity") or ""),
            li.get("incoterm") or "",
        ]
        if not has_interval_pricing:
            base_cells.extend(
                [
                    _money(currency, str(li.get("unit_price") or "0")),
                    _money(currency, str(li.get("total_price") or "0")),
                ]
            )
        table_data.append(base_cells)
    col_widths = (
        [0.35 * inch, 0.85 * inch, 1.7 * inch, 2.0 * inch, 0.8 * inch, 1.3 * inch]
        if has_interval_pricing
        else [0.3 * inch, 0.75 * inch, 1.2 * inch, 1.35 * inch, 0.4 * inch, 0.65 * inch, 0.95 * inch, 0.95 * inch]
    )
    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    item_style_commands: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (4, 1), (5, -1), "CENTER"),
    ]
    if not has_interval_pricing:
        item_style_commands.append(("ALIGN", (6, 1), (-1, -1), "RIGHT"))
    items_table.setStyle(TableStyle(item_style_commands))
    story.append(items_table)
    story.append(Spacer(1, 16))

    range_rows: list[list[Any]] = [["Product", "Quantity Range", "FOB Unit Price", "DDP Unit Price"]]
    for li in data["line_items"]:
        for row in li.get("interval_quote_table") or []:
            range_rows.append(
                [
                    Paragraph(str(li.get("product_name") or ""), small),
                    str(row.get("quantity_label") or ""),
                    _money(row.get("currency") or currency, str(row.get("fob_unit_price") or "N/A")),
                    _money(row.get("currency") or currency, str(row.get("ddp_unit_price") or "N/A")),
                ]
            )
    if len(range_rows) > 1:
        story.append(Paragraph("<b>Customer Quantity Range Pricing</b>", title_style))
        range_table = Table(range_rows, colWidths=[2.8 * inch, 1.2 * inch, 1.5 * inch, 1.5 * inch], repeatRows=1)
        range_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ]
            )
        )
        story.append(range_table)
        story.append(Spacer(1, 16))

    totals = data["totals"]
    if has_interval_pricing:
        story.append(
            Paragraph(
                "Final order total depends on the confirmed quantity range, selected Incoterm, and any manually approved adjustments.",
                small,
            )
        )
        story.append(Spacer(1, 16))
    else:
        totals_rows = [
            ["Subtotal", _money(currency, totals.get("subtotal", "0"))],
            ["Discount", _money(currency, totals.get("discount", "0"))],
            ["Shipping", _money(currency, totals.get("shipping", "0"))],
            ["Sample Fee", _money(currency, totals.get("sample_fee", "0"))],
            ["Tax", _money(currency, totals.get("tax", "0"))],
            ["Grand Total", _money(currency, totals.get("grand_total", "0"))],
        ]
        totals_table = Table(totals_rows, colWidths=[1.5 * inch, 1.2 * inch], hAlign="RIGHT")
        totals_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F5F5F5")),
                ]
            )
        )
        story.append(totals_table)
        story.append(Spacer(1, 16))

    terms = data["terms"]
    story.append(Paragraph("<b>Terms &amp; Notes</b>", title_style))
    story.append(Paragraph(f"Payment: {terms.get('payment_terms', '')}", small))
    story.append(Paragraph(f"Shipping: {terms.get('shipping_terms', '')}", small))
    story.append(Paragraph(f"Validity: {terms.get('validity_terms', '')}", small))
    if terms.get("notes"):
        story.append(Paragraph(f"Notes: {terms['notes']}", small))
    story.append(Spacer(1, 12))
    story.append(Paragraph(data.get("footer_safety", ""), small))

    doc.build(story)


def generate_quote_pdf(
    db: Session,
    quote_id: UUID,
    *,
    version_id: UUID | None = None,
    export_type: str = "customer_pdf",
    output_dir: Path | None = None,
    user: User | None = None,
) -> dict[str, Any]:
    if export_type in RESERVED_EXPORT_TYPES:
        raise ApiError(VALIDATION_ERROR, f"export_type {export_type} is reserved for a future phase", status_code=400)
    if export_type != "customer_pdf":
        raise ApiError(VALIDATION_ERROR, "only customer_pdf is supported in D6.4 MVP", status_code=400)

    quote = get_quote(db, quote_id)
    status_before = quote.status
    manual_sent_before = quote.manual_sent

    export_id = uuid4()
    data = build_quote_pdf_data(db, quote_id, version_id=version_id, export_type=export_type)
    version_number = None
    version_uuid = None
    if data.get("version"):
        version_number = data["version"].get("version_number")
        version_uuid = UUID(data["version"]["id"]) if data["version"].get("id") else version_id
    elif version_id:
        version_uuid = version_id

    file_name = _pdf_filename(data["quote"]["quote_number"], version_number)
    storage_dir = output_dir or quote_pdf_storage_dir()
    file_path = storage_dir / file_name

    record = QuotePdfExport(
        id=export_id,
        quote_id=quote_id,
        quote_version_id=version_uuid,
        export_type=export_type,
        file_name=file_name,
        status="failed",
        content_type="application/pdf",
        exported_by_id=user.id if user else None,
        snapshot_json=data,
    )
    db.add(record)

    try:
        _render_pdf_file(data, file_path)
        size = file_path.stat().st_size
        record.file_path = str(file_path)
        record.file_size_bytes = size
        record.status = "generated"
        record.exported_at = datetime.now(timezone.utc)
    except Exception as exc:
        record.notes = str(exc)[:500]
        db.commit()
        raise ApiError(VALIDATION_ERROR, f"PDF generation failed: {exc}", status_code=500) from exc

    db.commit()
    db.refresh(record)

    quote_after = get_quote(db, quote_id)
    if quote_after.status != status_before or quote_after.manual_sent != manual_sent_before:
        raise ApiError(VALIDATION_ERROR, "PDF export must not change quote status", status_code=500)

    return {
        "export_id": str(record.id),
        "quote_id": str(quote_id),
        "quote_version_id": str(version_uuid) if version_uuid else None,
        "file_name": record.file_name,
        "file_path": record.file_path,
        "file_size_bytes": record.file_size_bytes,
        "content_type": record.content_type,
        "status": record.status,
        "safety": dict(PDF_SAFETY),
    }


def export_record_to_dict(record: QuotePdfExport, *, quote_id: UUID) -> dict[str, Any]:
    return {
        "export_id": str(record.id),
        "quote_id": str(record.quote_id),
        "quote_version_id": str(record.quote_version_id) if record.quote_version_id else None,
        "export_type": record.export_type,
        "file_name": record.file_name,
        "file_size_bytes": record.file_size_bytes,
        "content_type": record.content_type,
        "status": record.status,
        "exported_at": record.exported_at.isoformat() if record.exported_at else None,
        "download_url": f"/api/v1/quotes/{quote_id}/pdf-exports/{record.id}/download",
    }


def pdf_text_for_audit(data: dict[str, Any]) -> str:
    """Flatten PDF payload for forbidden-phrase checks in tests."""
    return json.dumps(data, default=str).lower()
