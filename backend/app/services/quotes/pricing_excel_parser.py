"""Excel pricing workbook parser utilities (D6.2.1)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

_PUNCT_RE = re.compile(r"[\s\-_·•:：/\\|（）()\[\]{}【】<>《》\"'`,.;!?~@#$%^&*+=]+")
_FULLWIDTH = str.maketrans(
    "０１２３４５６７８９％－～",
    "0123456789%-~",
)


def cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def normalize_header(value: Any) -> str:
    text = cell_text(value).strip()
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).translate(_FULLWIDTH)
    text = text.replace("\n", " ").replace("\r", " ")
    text = _PUNCT_RE.sub(" ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def alias_matches(header_norm: str, alias: str) -> bool:
    alias_norm = normalize_header(alias)
    if not header_norm or not alias_norm:
        return False
    if header_norm == alias_norm:
        return True
    if len(alias_norm) >= 2 and alias_norm in header_norm:
        return True
    return False


# ---------------------------------------------------------------------------
# Alias maps
# ---------------------------------------------------------------------------

COST_ALIASES: dict[str, tuple[str, ...]] = {
    "product": (
        "product", "product name", "产品", "产品名称", "型号", "品名", "名称", "item", "model", "model no", "sku",
    ),
    "partner": ("partner", "brand", "品牌", "厂家", "供应商", "partner name"),
    "material_cost": (
        "rmb cost", "material cost", "材料成本", "成本", "rmb成本", "人民币成本", "单位成本", "unit cost",
        "factory cost", "ex factory cost", "成本rmb",
    ),
    "weight": ("weight", "kg", "重量", "单重", "unit weight", "gross weight", "net weight"),
    "ocean_freight": (
        "ocean freight", "freight", "sea freight", "海运", "海运单价", "运费单价", "shipping unit price",
    ),
    "exchange_rate": ("exchange rate", "fx", "fx rate", "汇率"),
    "domestic_profit": ("profit rate", "domestic profit", "国内利润", "利润率", "国内利润%"),
    "domestic_transport": (
        "domestic transport", "transportation", "国内运输", "内陆运输", "运输成本", "运输",
    ),
    "fob_cost": ("fob cost", "fob成本", "fob cost usd", "fob美元成本", "fob成本美金"),
    "ddp_cost": ("ddp cost", "ddp成本", "ddp cost usd", "ddp美元成本", "ddp成本美金"),
    "freight_cost_usd": ("freight cost usd", "运费成本美金", "运费成本", "freight cost"),
}

PRICE_ALIASES: dict[str, tuple[str, ...]] = {
    "product": ("product", "product name", "products", "产品", "产品名称", "型号", "sku", "item"),
    "min_qty": ("min qty", "min quantity", "minimum quantity", "min", "minqty", "起订量", "最小数量", "最低数量", "数量下限"),
    "max_qty": ("max qty", "max quantity", "maximum quantity", "max", "maxqty", "最大数量", "数量上限"),
    "qty_range": ("qty range", "quantity range", "数量段", "数量区间", "range", "quantity"),
    "fob": ("fob", "fob price", "fob unit price", "fob单价", "fob价格"),
    "ddp": ("ddp", "ddp price", "ddp unit price", "ddp单价", "ddp价格"),
    "fob_adjustment": ("fob adjustment", "fob调整", "fob加价", "fob adjustment value", "fob微调", "fob adj"),
    "ddp_adjustment": ("ddp adjustment", "ddp调整", "ddp加价", "ddp adjustment value", "ddp微调", "ddp adj"),
    "strategy": ("strategy", "pricing strategy", "策略", "利润策略", "类型"),
}

MARGIN_ALIASES: dict[str, tuple[str, ...]] = {
    "strategy": ("strategy", "strategy code", "策略", "类型", "利润类型", "引流", "销量", "利润"),
    "min_qty": ("min qty", "起订量", "数量下限", "min quantity", "min"),
    "max_qty": ("max qty", "数量上限", "max quantity", "max"),
    "multiplier": ("multiplier", "倍率", "系数", "利润倍率", "markup", "margin multiplier"),
    "qty_range": ("qty range", "quantity range", "数量段", "数量区间", "range"),
    "traffic": ("引流", "traffic"),
    "volume": ("销量", "volume"),
    "profit": ("利润", "profit"),
}

SHEET_TYPE_BY_NAME: tuple[tuple[str, str], ...] = (
    ("成本", "cost_model"),
    ("cost", "cost_model"),
    ("价目", "price_tier"),
    ("price", "price_tier"),
    ("利润倍率", "margin_strategy"),
    ("multiplier", "margin_strategy"),
    ("quote", "quote_template"),
    ("计算器", "calculator"),
    ("calculator", "calculator"),
)

PARTNER_HINTS: dict[str, str] = {
    "恒升": "HOSUN",
    "hosun": "HOSUN",
    "汇聚": "JOOBOO",
    "jooboo": "JOOBOO",
    "重庆": "CHONGQING_HUIJU",
    "huiju": "CHONGQING_HUIJU",
}

STRATEGY_CODE_MAP = {
    "引流": "traffic",
    "traffic": "traffic",
    "销量": "volume",
    "volume": "volume",
    "利润": "profit",
    "profit": "profit",
}

OPEN_ENDED_MAX = 999_999


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_decimal_cell(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    text = cell_text(value).strip()
    if not text or text in {"-", "—", "n/a", "na", "none", "#value!", "#n/a"}:
        return None
    text = unicodedata.normalize("NFKC", text).translate(_FULLWIDTH)
    text = text.replace(",", "")
    for token in ("rmb", "usd", "cny", "¥", "$", "元", "美元", "人民币"):
        text = re.sub(re.escape(token), "", text, flags=re.I)
    text = text.strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_percent_cell(value: Any, *, assume_whole_number_is_percent: bool = True) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        dec = Decimal(str(value))
        if assume_whole_number_is_percent and dec > 1:
            return (dec / Decimal("100")).quantize(Decimal("0.0001"))
        return dec
    text = cell_text(value).strip()
    if not text:
        return None
    text = unicodedata.normalize("NFKC", text).replace(" ", "")
    if text.endswith("%"):
        base = parse_decimal_cell(text[:-1])
        return (base / Decimal("100")).quantize(Decimal("0.0001")) if base is not None else None
    dec = parse_decimal_cell(text)
    if dec is None:
        return None
    if assume_whole_number_is_percent and dec > 1:
        return (dec / Decimal("100")).quantize(Decimal("0.0001"))
    return dec


_QTY_RANGE_RE = re.compile(
    r"(?P<min>\d+)\s*(?:[-–—~至到]\s*(?P<max>\d+)|\+|以上|above|and\s*above)?|"
    r"(?:≥|>=|>\s*)(?P<ge>\d+)",
    re.I,
)


def parse_quantity_range(value: Any) -> dict[str, int | None] | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        n = int(value)
        return {"min_qty": n, "max_qty": n}
    text = cell_text(value).strip()
    if not text:
        return None
    text = unicodedata.normalize("NFKC", text).replace(" ", "")
    if text.lower() in {"≥500", ">=500", ">500", "500+", "500以上", "500andabove"}:
        return {"min_qty": 500, "max_qty": None}
    m = _QTY_RANGE_RE.search(text)
    if not m:
        dec = parse_decimal_cell(text)
        if dec is not None:
            n = int(dec)
            return {"min_qty": n, "max_qty": n}
        return None
    if m.group("ge"):
        return {"min_qty": int(m.group("ge")), "max_qty": None}
    min_q = int(m.group("min"))
    max_q = m.group("max")
    if max_q:
        return {"min_qty": min_q, "max_qty": int(max_q)}
    if "+" in text or "以上" in text or "above" in text.lower():
        return {"min_qty": min_q, "max_qty": None}
    return {"min_qty": min_q, "max_qty": min_q}


def normalize_max_qty(max_qty: int | None) -> int | None:
    if max_qty is None:
        return None
    if max_qty >= OPEN_ENDED_MAX:
        return None
    return max_qty


def generate_internal_sku(
    product_name: str,
    *,
    partner_code: str = "OTHER",
    explicit_sku: str | None = None,
    used: set[str] | None = None,
) -> str:
    if used is None:
        used = set()
    if explicit_sku:
        base = re.sub(r"[^A-Z0-9]+", "-", explicit_sku.upper()).strip("-")[:48]
    else:
        slug = re.sub(r"[^A-Z0-9]+", "-", product_name.upper()).strip("-")[:40]
        base = f"{partner_code}-{slug}"[:48].strip("-")
    if not base:
        base = f"{partner_code}-IMPORT"
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base[:44]}-{suffix:03d}"
        suffix += 1
    used.add(candidate)
    return candidate


def detect_partner_code(value: Any, *, sheet_name: str = "") -> str | None:
    text = normalize_header(value)
    if not text:
        sheet_norm = normalize_header(sheet_name)
        if "jooboo" in sheet_norm:
            return "JOOBOO"
        if "hosun" in sheet_norm:
            return "HOSUN"
        return None
    for hint, code in PARTNER_HINTS.items():
        if hint in text:
            return code
    return None


def is_dispimg_or_formula(value: Any) -> bool:
    text = cell_text(value)
    return text.startswith("=DISPIMG") or text.startswith("=")


def row_has_data(row: tuple[Any, ...] | list[Any]) -> bool:
    return any(cell_text(v).strip() for v in row if v is not None)


# ---------------------------------------------------------------------------
# Header detection
# ---------------------------------------------------------------------------

@dataclass
class HeaderDetection:
    row_index: int
    score: int
    columns: dict[str, int]
    labels: dict[str, str]


def detect_header_row(
    rows: list[tuple[Any, ...]],
    alias_map: dict[str, tuple[str, ...]],
    *,
    max_scan: int = 30,
    min_score: int = 2,
) -> HeaderDetection | None:
    best: HeaderDetection | None = None
    for idx, row in enumerate(rows[:max_scan]):
        columns: dict[str, int] = {}
        labels: dict[str, str] = {}
        score = 0
        for col_idx, cell in enumerate(row):
            header_norm = normalize_header(cell)
            if not header_norm:
                continue
            for field, aliases in alias_map.items():
                if field in columns:
                    continue
                if any(alias_matches(header_norm, alias) for alias in aliases):
                    columns[field] = col_idx
                    labels[field] = cell_text(cell).strip()
                    score += 1
                    break
        if score >= min_score and (best is None or score > best.score):
            best = HeaderDetection(row_index=idx, score=score, columns=columns, labels=labels)
    return best


def classify_sheet(sheet_name: str, sample_rows: list[tuple[Any, ...]]) -> str:
    name_norm = normalize_header(sheet_name)
    for token, sheet_type in SHEET_TYPE_BY_NAME:
        if token in name_norm:
            return sheet_type
    scores: dict[str, int] = {}
    for alias_map, sheet_type, min_score in (
        (COST_ALIASES, "cost_model", 3),
        (PRICE_ALIASES, "price_tier", 3),
        (MARGIN_ALIASES, "margin_strategy", 2),
    ):
        det = detect_header_row(sample_rows, alias_map, min_score=min_score)
        if det:
            scores[sheet_type] = det.score
    if scores:
        return max(scores, key=scores.get)
    if "products" in name_norm and "quantity" in name_norm:
        return "quote_template"
    return "unknown"


def row_value(row: tuple[Any, ...], index: int | None) -> Any:
    if index is None or index >= len(row):
        return None
    return row[index]


# ---------------------------------------------------------------------------
# Sheet parse results
# ---------------------------------------------------------------------------

@dataclass
class ParsedCostRow:
    partner_code: str
    product_name: str
    partner_product_code: str | None
    internal_sku: str | None
    material_cost: Decimal | None
    weight: Decimal | None
    domestic_transport: Decimal | None
    freight_cost_usd: Decimal | None
    fob_cost_usd: Decimal | None
    ddp_cost_usd: Decimal | None


@dataclass
class ParsedPriceRow:
    partner_code: str | None
    product_name: str
    min_qty: int
    max_qty: int | None
    fob: Decimal | None
    ddp: Decimal | None
    fob_adjustment: Decimal | None
    ddp_adjustment: Decimal | None
    pricing_strategy: str


@dataclass
class ParsedMarginRow:
    strategy_code: str
    strategy_name: str
    min_qty: int
    max_qty: int | None
    multiplier: Decimal


@dataclass
class SheetMeta:
    fx_rate: Decimal | None = None
    ocean_freight_unit: Decimal | None = None
    domestic_profit_rate: Decimal | None = None


@dataclass
class SheetParseReport:
    sheet_name: str
    detected_type: str
    header_row: int | None = None
    matched_columns: dict[str, str] = field(default_factory=dict)
    candidate_rows: int = 0
    skipped_rows: int = 0
    warnings: list[str] = field(default_factory=list)
    cost_rows: list[ParsedCostRow] = field(default_factory=list)
    price_rows: list[ParsedPriceRow] = field(default_factory=list)
    margin_rows: list[ParsedMarginRow] = field(default_factory=list)
    meta: SheetMeta = field(default_factory=SheetMeta)


def _extract_cost_meta(rows: list[tuple[Any, ...]]) -> SheetMeta:
    meta = SheetMeta()
    for row_idx, row in enumerate(rows[:6]):
        value_row = rows[row_idx + 1] if row_idx + 1 < len(rows) else row
        for idx, cell in enumerate(row):
            norm = normalize_header(cell)
            val = row_value(value_row, idx)
            if alias_matches(norm, "exchange rate") or alias_matches(norm, "汇率"):
                meta.fx_rate = parse_decimal_cell(val)
            elif alias_matches(norm, "ocean freight") or alias_matches(norm, "海运"):
                meta.ocean_freight_unit = parse_decimal_cell(val)
            elif alias_matches(norm, "domestic profit") or alias_matches(norm, "国内利润"):
                meta.domestic_profit_rate = parse_percent_cell(val)
    return meta


def parse_cost_sheet(sheet_name: str, rows: list[tuple[Any, ...]]) -> SheetParseReport:
    report = SheetParseReport(sheet_name=sheet_name, detected_type="cost_model")
    report.meta = _extract_cost_meta(rows)
    header = detect_header_row(rows, COST_ALIASES, min_score=3)
    if not header:
        report.warnings.append("cost header row not detected")
        return report
    report.header_row = header.row_index + 1
    report.matched_columns = header.labels
    cols = header.columns
    used_skus: set[str] = set()
    current_partner = detect_partner_code("", sheet_name=sheet_name) or "OTHER"
    partner_col = cols.get("partner")
    if partner_col is None:
        partner_col = 0 if any(detect_partner_code(row_value(r, 0)) for r in rows[header.row_index + 1 : header.row_index + 6]) else None

    for row in rows[header.row_index + 1 :]:
        if not row_has_data(row):
            report.skipped_rows += 1
            continue
        partner_hint = detect_partner_code(row_value(row, partner_col), sheet_name=sheet_name) if partner_col is not None else None
        if partner_hint:
            current_partner = partner_hint
        product_raw = row_value(row, cols.get("product"))
        if is_dispimg_or_formula(product_raw):
            report.skipped_rows += 1
            report.warnings.append("skipped DISPIMG/formula product cell")
            continue
        product_name = cell_text(product_raw).strip()
        if not product_name:
            report.skipped_rows += 1
            continue
        fob_cost = parse_decimal_cell(row_value(row, cols.get("fob_cost")))
        ddp_cost = parse_decimal_cell(row_value(row, cols.get("ddp_cost")))
        if fob_cost is None and ddp_cost is None:
            report.skipped_rows += 1
            report.warnings.append("skipped cost input row without FOB/DDP cost result")
            continue
        explicit_code = None
        if re.fullmatch(r"[A-Z0-9]{3,12}", product_name.upper()):
            explicit_code = product_name.upper()
        sku = generate_internal_sku(
            product_name,
            partner_code=current_partner,
            explicit_sku=explicit_code,
            used=used_skus,
        )
        report.cost_rows.append(
            ParsedCostRow(
                partner_code=current_partner,
                product_name=product_name,
                partner_product_code=explicit_code,
                internal_sku=sku,
                material_cost=parse_decimal_cell(row_value(row, cols.get("material_cost"))),
                weight=parse_decimal_cell(row_value(row, cols.get("weight"))),
                domestic_transport=parse_decimal_cell(row_value(row, cols.get("domestic_transport"))),
                freight_cost_usd=parse_decimal_cell(row_value(row, cols.get("freight_cost_usd"))),
                fob_cost_usd=fob_cost,
                ddp_cost_usd=ddp_cost,
            )
        )
        report.candidate_rows += 1
    return report


def _parse_embedded_margin_block(rows: list[tuple[Any, ...]]) -> list[ParsedMarginRow]:
    margin_rows: list[ParsedMarginRow] = []
    strategy_cols: dict[str, int] = {}
    header_idx: int | None = None

    for idx, row in enumerate(rows[:30]):
        for col_idx, cell in enumerate(row):
            norm = normalize_header(cell)
            if alias_matches(norm, "引流") or norm == "traffic":
                strategy_cols["traffic"] = col_idx
            elif alias_matches(norm, "销量") or norm == "volume":
                strategy_cols["volume"] = col_idx
            elif alias_matches(norm, "利润") or norm == "profit":
                strategy_cols["profit"] = col_idx
        if len(strategy_cols) >= 2:
            header_idx = idx
            break

    if header_idx is None or not strategy_cols:
        return margin_rows

    qty_col: int | None = None
    start_idx = header_idx + 1
    for idx in range(start_idx, min(start_idx + 12, len(rows))):
        row = rows[idx]
        for col_idx, cell in enumerate(row):
            if parse_quantity_range(cell):
                qty_col = col_idx
                start_idx = idx
                break
        if qty_col is not None:
            break

    if qty_col is None:
        return margin_rows

    for row in rows[start_idx : start_idx + 10]:
        qty_raw = row_value(row, qty_col)
        if not qty_raw:
            continue
        qty = parse_quantity_range(qty_raw)
        if not qty:
            continue
        for code, col_idx in strategy_cols.items():
            mult = parse_decimal_cell(row_value(row, col_idx))
            if mult is None:
                continue
            margin_rows.append(
                ParsedMarginRow(
                    strategy_code=code,
                    strategy_name={"traffic": "引流", "volume": "销量", "profit": "利润"}.get(code, code),
                    min_qty=qty["min_qty"],
                    max_qty=normalize_max_qty(qty["max_qty"]),
                    multiplier=mult,
                )
            )
    return margin_rows


def parse_price_sheet(sheet_name: str, rows: list[tuple[Any, ...]]) -> SheetParseReport:
    report = SheetParseReport(sheet_name=sheet_name, detected_type="price_tier")
    report.margin_rows = _parse_embedded_margin_block(rows)
    header = detect_header_row(rows, PRICE_ALIASES, min_score=3)
    if not header:
        report.warnings.append("price tier header row not detected")
        return report
    report.header_row = header.row_index + 1
    report.matched_columns = header.labels
    cols = header.columns
    current_product = ""
    partner_code = detect_partner_code("", sheet_name=sheet_name)

    for row in rows[header.row_index + 1 :]:
        if not row_has_data(row):
            report.skipped_rows += 1
            continue
        product_raw = row_value(row, cols.get("product"))
        if is_dispimg_or_formula(product_raw):
            report.skipped_rows += 1
            continue
        product_name = cell_text(product_raw).strip()
        if product_name:
            current_product = product_name
        elif not current_product:
            report.skipped_rows += 1
            continue
        min_q = _int_cell(row_value(row, cols.get("min_qty")))
        max_q = _int_cell(row_value(row, cols.get("max_qty")))
        qty_range = row_value(row, cols.get("qty_range"))
        if min_q is None and qty_range:
            parsed = parse_quantity_range(qty_range)
            if parsed:
                min_q = parsed["min_qty"]
                max_q = parsed["max_qty"]
        if min_q is None:
            report.skipped_rows += 1
            continue
        max_q = normalize_max_qty(max_q)
        fob = parse_decimal_cell(row_value(row, cols.get("fob")))
        ddp = parse_decimal_cell(row_value(row, cols.get("ddp")))
        fob_adj = parse_decimal_cell(row_value(row, cols.get("fob_adjustment")))
        ddp_adj = parse_decimal_cell(row_value(row, cols.get("ddp_adjustment")))
        if fob is None and ddp is None:
            report.skipped_rows += 1
            continue
        report.price_rows.append(
            ParsedPriceRow(
                partner_code=partner_code,
                product_name=current_product,
                min_qty=min_q,
                max_qty=max_q,
                fob=fob,
                ddp=ddp,
                fob_adjustment=fob_adj,
                ddp_adjustment=ddp_adj,
                pricing_strategy="volume",
            )
        )
        report.candidate_rows += 1
    if report.margin_rows:
        report.candidate_rows += len(report.margin_rows)
    return report


def parse_margin_sheet(sheet_name: str, rows: list[tuple[Any, ...]]) -> SheetParseReport:
    report = SheetParseReport(sheet_name=sheet_name, detected_type="margin_strategy")
    header = detect_header_row(rows, MARGIN_ALIASES, min_score=2)
    if header and "multiplier" in header.columns:
        report.header_row = header.row_index + 1
        report.matched_columns = header.labels
        cols = header.columns
        for row in rows[header.row_index + 1 :]:
            if not row_has_data(row):
                report.skipped_rows += 1
                continue
            raw_strategy = cell_text(row_value(row, cols.get("strategy"))).strip()
            mult = parse_decimal_cell(row_value(row, cols.get("multiplier")))
            if not raw_strategy or mult is None:
                report.skipped_rows += 1
                continue
            code = STRATEGY_CODE_MAP.get(raw_strategy, STRATEGY_CODE_MAP.get(normalize_header(raw_strategy), raw_strategy.lower()))
            min_q = _int_cell(row_value(row, cols.get("min_qty")))
            max_q = _int_cell(row_value(row, cols.get("max_qty")))
            qty = parse_quantity_range(row_value(row, cols.get("qty_range")))
            if min_q is None and qty:
                min_q, max_q = qty["min_qty"], qty["max_qty"]
            if min_q is None:
                report.skipped_rows += 1
                continue
            report.margin_rows.append(
                ParsedMarginRow(
                    strategy_code=code,
                    strategy_name=raw_strategy,
                    min_qty=min_q,
                    max_qty=normalize_max_qty(max_q),
                    multiplier=mult,
                )
            )
            report.candidate_rows += 1
        return report

    embedded = _parse_embedded_margin_block(rows)
    if embedded:
        report.margin_rows = embedded
        report.candidate_rows = len(embedded)
        report.warnings.append("margin table parsed from embedded block")
    else:
        report.warnings.append("margin strategy header not detected")
    return report


def _int_cell(value: Any) -> int | None:
    dec = parse_decimal_cell(value)
    if dec is None:
        return None
    return int(dec)


def parse_workbook_sheet(sheet_name: str, rows: list[tuple[Any, ...]]) -> SheetParseReport:
    sheet_type = classify_sheet(sheet_name, rows)
    if sheet_type == "cost_model":
        return parse_cost_sheet(sheet_name, rows)
    if sheet_type == "price_tier":
        return parse_price_sheet(sheet_name, rows)
    if sheet_type == "margin_strategy":
        return parse_margin_sheet(sheet_name, rows)
    return SheetParseReport(
        sheet_name=sheet_name,
        detected_type=sheet_type,
        warnings=["sheet skipped for import"] if sheet_type in {"quote_template", "calculator", "unknown"} else [],
    )


def load_sheet_rows(ws, *, max_row: int | None = None) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = []
    for row in ws.iter_rows(values_only=True, max_row=max_row):
        rows.append(tuple(row) if row else tuple())
    return rows


def format_sheet_debug(report: SheetParseReport) -> str:
    lines = [
        f"Sheet: {report.sheet_name}",
        f"Detected type: {report.detected_type}",
        f"Header row: {report.header_row or 'n/a'}",
        "Matched columns:",
    ]
    if report.matched_columns:
        for field, label in report.matched_columns.items():
            lines.append(f"  - {field} -> {label}")
    else:
        lines.append("  (none)")
    lines.append(f"Data rows: {report.candidate_rows}")
    lines.append(f"Skipped rows: {report.skipped_rows}")
    if report.warnings:
        lines.append(f"Warnings: {', '.join(report.warnings[:5])}")
    return "\n".join(lines)
