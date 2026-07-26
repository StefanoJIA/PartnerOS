"""ReportLab PDF generation for customer quotes (D6.4)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ApiError, VALIDATION_ERROR
from app.models import User
from app.models.customer_quotes import QuotePdfExport
from app.services.quotes.pdf_data_builder import PDF_SAFETY, build_quote_pdf_data
from app.services.quotes.quote_service import get_quote

BACKEND_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = BACKEND_ROOT.parent
MARGIN = 0.58 * inch
RESERVED_EXPORT_TYPES = {"partner_pdf", "summary_pdf", "internal_pdf"}
THEME_BLUE = colors.HexColor("#3F7DD8")
THEME_NAVY = colors.HexColor("#163A5F")
THEME_DARK = colors.HexColor("#111827")
TEXT_MUTED = colors.HexColor("#5F6B7A")
GRID = colors.HexColor("#DDE4EF")
SOFT_GRID = colors.HexColor("#EEF2F7")
LIGHT_BG = colors.HexColor("#F7FAFE")
PANEL_BG = colors.HexColor("#FBFCFF")
QUOTE_ACCENT = colors.HexColor("#D9E7FF")


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


def _money_short(currency: str, value: Any) -> str:
    if str(value or "").upper() == "N/A":
        return "N/A"
    try:
        num = float(value)
        prefix = "$" if (currency or "").upper() == "USD" else f"{currency} "
        return f"{prefix}{num:,.2f}"
    except (TypeError, ValueError):
        return str(value or "")


def _safe_text(value: Any) -> str:
    text = str(value or "").strip()
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return escape(text)


def _plain_text(value: Any) -> str:
    text = str(value or "").strip()
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def _asset_path(value: str | None) -> Path | None:
    if not value:
        return None
    raw = str(value).strip()
    candidates: list[Path] = []
    if raw.startswith("http://") or raw.startswith("https://"):
        return None
    if raw.startswith("/"):
        rel = raw.lstrip("/")
        candidates.extend(
            [
                REPO_ROOT / "frontend" / "public" / rel,
                BACKEND_ROOT / rel,
            ]
        )
    else:
        candidates.extend(
            [
                Path(raw),
                BACKEND_ROOT / "app" / "assets" / raw,
                REPO_ROOT / "frontend" / "public" / raw,
                REPO_ROOT / raw,
            ]
        )
    for path in candidates:
        if path.is_file():
            return path
    return None


def _image_flowable(path: Path | None, *, width: float, height: float) -> Any:
    if not path:
        return Spacer(1, height)
    try:
        return Image(str(path), width=width, height=height, kind="proportional")
    except Exception:
        return Spacer(1, height)


def _paragraph(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_safe_text(text), style)


def _split_terms(notes: str, fallback_payment: str, fallback_shipping: str) -> dict[str, list[str] | str]:
    raw_lines = [line.strip() for line in (notes or "").replace("\r\n", "\n").split("\n")]
    lines = [line for line in raw_lines if line]
    sections: dict[str, list[str]] = {
        "payment": [],
        "manufacturing": [],
        "delivery": [],
        "shipping": [],
        "additional": [],
    }
    active: str | None = None
    thank_you = "Thank you for your business!"
    for line in lines:
        low = line.lower().rstrip(":")
        if "thank you" in low:
            thank_you = line
            continue
        if low in {"terms & instructions", "terms and instructions"}:
            continue
        if low.startswith("payment terms"):
            active = "payment"
            tail = re.sub(r"^payment terms:?", "", line, flags=re.I).strip()
            if tail:
                sections[active].append(tail)
            continue
        if low.startswith("manufacturing lead time"):
            active = "manufacturing"
            tail = re.sub(r"^manufacturing lead time:?", "", line, flags=re.I).strip()
            if tail:
                sections[active].append(tail)
            continue
        if low.startswith("ddp delivery time") or low.startswith("delivery time"):
            active = "delivery"
            tail = re.sub(r"^(ddp )?delivery time:?", "", line, flags=re.I).strip()
            if tail:
                sections[active].append(tail)
            continue
        if low.startswith("shipping information"):
            active = "shipping"
            tail = re.sub(r"^shipping information:?", "", line, flags=re.I).strip()
            if tail:
                sections[active].append(tail)
            continue
        if low.startswith("additional notes"):
            active = "additional"
            tail = re.sub(r"^additional notes:?", "", line, flags=re.I).strip()
            if tail:
                sections[active].append(tail)
            continue
        if active:
            sections[active].append(line)

    if not sections["payment"] and fallback_payment:
        sections["payment"] = [fallback_payment]
    if not sections["shipping"] and fallback_shipping:
        sections["shipping"] = [fallback_shipping]
    return {"thank_you": thank_you, **sections}


def _pdf_filename(quote_number: str, version_number: int | None) -> str:
    safe_num = quote_number.replace("/", "-").replace(" ", "_")
    v = version_number if version_number is not None else 1
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"Quote_{safe_num}_v{v}_{stamp}.pdf"


def _render_pdf_file(data: dict[str, Any], output_path: Path) -> None:
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    brand = ParagraphStyle("Brand", parent=normal, fontSize=20, leading=24, textColor=THEME_BLUE)
    small = ParagraphStyle("Small", parent=normal, fontSize=8.6, leading=10.8, textColor=THEME_DARK)
    tiny = ParagraphStyle("Tiny", parent=normal, fontSize=7.4, leading=9.0, textColor=TEXT_MUTED)
    right = ParagraphStyle("Right", parent=small, alignment=TA_RIGHT)
    center = ParagraphStyle("Center", parent=small, alignment=TA_CENTER)
    section = ParagraphStyle("Section", parent=normal, fontSize=9.4, leading=11.2, textColor=THEME_BLUE)
    product_style = ParagraphStyle("Product", parent=small, fontSize=7.8, leading=9.4, textColor=THEME_DARK)
    product_code = ParagraphStyle("ProductCode", parent=tiny, fontSize=6.8, leading=8.2, textColor=TEXT_MUTED)
    table_text = ParagraphStyle("TableText", parent=small, fontSize=8.0, leading=9.8)
    table_right = ParagraphStyle("TableRight", parent=table_text, alignment=TA_RIGHT)
    table_header = ParagraphStyle("TableHeader", parent=center, fontSize=8.2, leading=10, textColor=colors.white)
    term_title = ParagraphStyle("TermTitle", parent=normal, fontSize=10.8, leading=13, textColor=THEME_NAVY)
    term_body = ParagraphStyle("TermBody", parent=small, fontSize=8.2, leading=10.2)
    thanks = ParagraphStyle("Thanks", parent=normal, fontSize=14, leading=18, alignment=TA_CENTER, textColor=THEME_DARK)

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
    logo = _image_flowable(_asset_path("intelliopus-logo.png"), width=0.92 * inch, height=0.92 * inch)
    company_block = [
        Paragraph(f"<font color='#3F7DD8'>{_safe_text(company['brand'])}</font>", brand),
        _paragraph(company.get("address_line"), small),
        _paragraph(company.get("website"), small),
        _paragraph(company.get("phone"), small),
    ]
    quote_meta = Table(
        [
            [Paragraph("<b>QUOTE</b>", right)],
            [Paragraph(f"<font color='#3F7DD8'><b>{quote['quote_number']}</b></font>", right)],
            [Paragraph(f"<b>Quote Date</b><br/>{quote['quote_date']}", right)],
            [Paragraph(f"<b>Valid Till</b><br/>{quote['valid_until']}", right)],
        ],
        colWidths=[1.9 * inch],
    )
    quote_meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PANEL_BG),
                ("BOX", (0, 0), (-1, -1), 0.45, GRID),
                ("LINEBELOW", (0, 1), (0, 1), 0.45, QUOTE_ACCENT),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    header = Table(
        [[logo, company_block, quote_meta]],
        colWidths=[1.05 * inch, 4.05 * inch, 2.1 * inch],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, QUOTE_ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 10))

    bill = data["bill_to"]
    ship = data["ship_to"]
    addr_table = Table(
        [
            [Paragraph("<b>BILL TO</b>", section), Paragraph("<b>SHIP TO</b>", section)],
            [
                Paragraph(
                    f"<b>{_safe_text(bill.get('contact'))}</b><br/>{_safe_text(bill.get('company'))}<br/>{_safe_text(bill.get('address'))}",
                    small,
                ),
                Paragraph(
                    f"<b>{_safe_text(ship.get('contact'))}</b><br/>{_safe_text(ship.get('company'))}<br/>{_safe_text(ship.get('address'))}",
                    small,
                ),
            ],
        ],
        colWidths=[3.5 * inch, 3.5 * inch],
    )
    addr_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PANEL_BG),
                ("BOX", (0, 0), (-1, -1), 0.45, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.45, QUOTE_ACCENT),
                ("LINEBEFORE", (1, 0), (1, -1), 0.45, SOFT_GRID),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(addr_table)
    story.append(Spacer(1, 14))

    currency = data["totals"].get("currency") or quote.get("currency") or "USD"
    has_interval_pricing = any(li.get("interval_quote_table") for li in data["line_items"])
    product_rows: list[list[Any]] = [
            [
            Paragraph("<b>Products</b>", table_header),
            Paragraph("<b>Quantity</b>", table_header),
            Paragraph("<b>FOB Unit Price</b>", table_header),
            Paragraph("<b>DDP Unit Price</b>", table_header),
        ]
    ]
    table_styles: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), THEME_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, THEME_NAVY),
        ("INNERGRID", (0, 1), (-1, -1), 0.25, SOFT_GRID),
        ("BOX", (0, 0), (-1, -1), 0.45, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5.5),
    ]
    row_index = 1
    for li in data["line_items"]:
        intervals = li.get("interval_quote_table") or []
        if not intervals:
            intervals = [
                {
                    "quantity_label": str(li.get("quantity") or ""),
                    "currency": li.get("currency") or currency,
                    "fob_unit_price": li.get("unit_price") if (li.get("incoterm") or "").upper() == "FOB" else "N/A",
                    "ddp_unit_price": li.get("unit_price") if (li.get("incoterm") or "").upper() == "DDP" else "N/A",
                }
            ]
        image_path = _asset_path(li.get("image_url"))
        product_code_text = li.get("sku") or li.get("product_sku") or li.get("product_category") or ""
        product_cell = [
            Paragraph(f"<b>{_safe_text(li.get('product_name'))}</b>", product_style),
            Paragraph(_safe_text(product_code_text), product_code) if product_code_text else Spacer(1, 1),
            Spacer(1, 5),
            _image_flowable(image_path, width=1.6 * inch, height=0.92 * inch),
        ]
        group_start = row_index
        for idx, row in enumerate(intervals):
            row_currency = row.get("currency") or currency
            product_rows.append(
                [
                    product_cell if idx == 0 else "",
                    Paragraph(_plain_text(row.get("quantity_label")), center),
                    Paragraph(_money_short(row_currency, row.get("fob_unit_price")), table_right),
                    Paragraph(_money_short(row_currency, row.get("ddp_unit_price")), table_right),
                ]
            )
            row_index += 1
        group_end = row_index - 1
        if group_end > group_start:
            table_styles.append(("SPAN", (0, group_start), (0, group_end)))
        table_styles.extend(
            [
                ("LINEABOVE", (0, group_start), (-1, group_start), 0.75, colors.HexColor("#7A8290")),
                ("VALIGN", (0, group_start), (0, group_end), "TOP"),
                ("BACKGROUND", (0, group_start), (0, group_end), colors.white),
            ]
        )
        for stripe_row in range(group_start, group_end + 1):
            if (stripe_row - group_start) % 2 == 1:
                table_styles.append(("BACKGROUND", (1, stripe_row), (-1, stripe_row), LIGHT_BG))

    products_table = Table(
        product_rows,
        colWidths=[3.65 * inch, 1.05 * inch, 1.25 * inch, 1.25 * inch],
        repeatRows=1,
        splitByRow=1,
    )
    products_table.setStyle(TableStyle(table_styles))
    story.append(products_table)
    story.append(Spacer(1, 18))

    terms = data["terms"]
    parsed_terms = _split_terms(
        terms.get("notes") or "",
        terms.get("payment_terms") or "",
        terms.get("shipping_terms") or "",
    )
    term_flow: list[Any] = [
        Paragraph(f"<b>{_safe_text(parsed_terms['thank_you'])}</b>", thanks),
        Spacer(1, 8),
        Paragraph("<b>Terms &amp; Instructions</b>", term_title),
        Table([[""]], colWidths=[6.95 * inch], rowHeights=[1], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), QUOTE_ACCENT)])),
    ]

    def add_terms_section(title: str, rows: list[str]) -> None:
        if not rows:
            return
        term_flow.append(Spacer(1, 5))
        term_flow.append(Paragraph(f"<b>{_safe_text(title)}</b>", term_body))
        for line in rows:
            term_flow.append(_paragraph(line, term_body))

    add_terms_section("Payment Terms:", parsed_terms["payment"])  # type: ignore[arg-type]
    add_terms_section("Manufacturing Lead Time", parsed_terms["manufacturing"])  # type: ignore[arg-type]
    add_terms_section("DDP Delivery Time:", parsed_terms["delivery"])  # type: ignore[arg-type]
    add_terms_section("Shipping Information:", parsed_terms["shipping"])  # type: ignore[arg-type]
    add_terms_section("Additional Notes:", parsed_terms["additional"])  # type: ignore[arg-type]
    terms_box = Table([[term_flow]], colWidths=[7.2 * inch])
    terms_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PANEL_BG),
                ("BOX", (0, 0), (-1, -1), 0.45, GRID),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(terms_box)
    if not has_interval_pricing:
        story.append(Spacer(1, 6))
        story.append(_paragraph(data.get("footer_safety", ""), tiny))

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
