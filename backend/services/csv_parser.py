"""Bank CSV parsers."""

import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def _parse_date(value: str) -> date | None:
    """Try common date formats."""
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_sber_csv(content: str) -> list[dict]:
    """Parse Sberbank Online CSV export."""
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    rows = []
    for row in reader:
        date_str = row.get("Дата операции") or row.get("date") or ""
        amount_str = row.get("Сумма") or row.get("amount") or "0"
        desc = row.get("Описание") or row.get("description") or ""
        parsed_date = _parse_date(date_str)
        if not parsed_date:
            continue
        try:
            amount = abs(Decimal(amount_str.replace(",", ".").replace(" ", "")))
        except InvalidOperation:
            continue
        if amount == 0:
            continue
        rows.append({"date": parsed_date.isoformat(), "amount": float(amount), "description": desc})
    return rows


def parse_tinkoff_csv(content: str) -> list[dict]:
    """Parse Tinkoff CSV export."""
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    rows = []
    for row in reader:
        date_str = row.get("Дата операции") or row.get("Date") or ""
        amount_str = row.get("Сумма операции") or row.get("Amount") or "0"
        desc = row.get("Описание") or row.get("Description") or ""
        parsed_date = _parse_date(date_str)
        if not parsed_date:
            continue
        try:
            amount = abs(Decimal(amount_str.replace(",", ".").replace(" ", "")))
        except InvalidOperation:
            continue
        if amount == 0:
            continue
        rows.append({"date": parsed_date.isoformat(), "amount": float(amount), "description": desc})
    return rows


def detect_and_parse(content: str, filename: str) -> list[dict]:
    """Detect bank format and parse CSV."""
    lower = filename.lower()
    if "tinkoff" in lower or "t-bank" in lower:
        return parse_tinkoff_csv(content)
    return parse_sber_csv(content)
