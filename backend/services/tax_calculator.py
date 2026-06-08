"""Deterministic tax deduction calculator."""

from decimal import Decimal

from models import TaxProfile

NDfl_RATE = Decimal("0.13")
PROPERTY_CAP = Decimal("260000")
MORTGAGE_CAP = Decimal("390000")
SOCIAL_BASE_CAP = Decimal("150000")
IIS_CAP = Decimal("52000")
INSURANCE_BASE_CAP = Decimal("120000")


def _return_from_base(base: Decimal, cap_base: Decimal | None = None) -> Decimal:
    """Calculate NDFL return from expense base."""
    if cap_base is not None:
        base = min(base, cap_base)
    return (base * NDfl_RATE).quantize(Decimal("0.01"))


def calculate_deductions(profile: TaxProfile) -> tuple[list[dict], Decimal, list[dict]]:
    """
    Calculate available tax deductions.

    Returns (deductions, total_return, documents).
    """
    deductions: list[dict] = []
    documents: list[dict] = []

    if profile.bought_property and profile.property_amount:
        amount = _return_from_base(profile.property_amount, PROPERTY_CAP / NDfl_RATE)
        deductions.append({
            "type": "property",
            "title": "Имущественный вычет",
            "amount": float(amount),
            "article": "ст. 220 НК РФ",
        })
        documents.append({
            "deduction_type": "property",
            "docs": ["Договор купли-продажи", "Акт приёма-передачи", "Платёжные документы", "Справка 2-НДФЛ"],
        })

    if profile.has_mortgage and profile.mortgage_interest_paid:
        amount = _return_from_base(profile.mortgage_interest_paid, MORTGAGE_CAP / NDfl_RATE)
        deductions.append({
            "type": "mortgage_interest",
            "title": "Вычет по ипотечным процентам",
            "amount": float(amount),
            "article": "ст. 220 НК РФ п. 4",
        })
        documents.append({
            "deduction_type": "mortgage_interest",
            "docs": ["Справка из банка об уплаченных процентах", "Кредитный договор", "Справка 2-НДФЛ"],
        })

    social_base = Decimal("0")
    if profile.paid_education and profile.education_amount:
        social_base += profile.education_amount
    if profile.paid_medical and profile.medical_amount:
        social_base += profile.medical_amount
    if profile.paid_fitness and profile.fitness_amount:
        social_base += profile.fitness_amount
    if profile.paid_insurance and profile.insurance_amount:
        insurance_return = _return_from_base(profile.insurance_amount, INSURANCE_BASE_CAP)
        deductions.append({
            "type": "insurance",
            "title": "Социальный вычет (страхование жизни)",
            "amount": float(insurance_return),
            "article": "ст. 219 НК РФ",
        })
        documents.append({
            "deduction_type": "insurance",
            "docs": ["Договор страхования", "Платёжные документы", "Справка 2-НДФЛ"],
        })

    if social_base > 0:
        amount = _return_from_base(social_base, SOCIAL_BASE_CAP)
        deductions.append({
            "type": "social",
            "title": "Социальный вычет (лечение, обучение, фитнес)",
            "amount": float(amount),
            "article": "ст. 219 НК РФ",
        })
        documents.append({
            "deduction_type": "social",
            "docs": ["Договор с мед. организацией / учебным заведением", "Платёжные документы", "Справка 2-НДФЛ"],
        })

    if profile.has_iis and profile.iis_amount:
        amount = min(_return_from_base(profile.iis_amount), IIS_CAP)
        deductions.append({
            "type": "iis",
            "title": "Инвестиционный вычет (ИИС тип А)",
            "amount": float(amount),
            "article": "ст. 219.1 НК РФ",
        })
        documents.append({
            "deduction_type": "iis",
            "docs": ["Договор с брокером на ИИС", "Справка о внесённых средствах", "Справка 2-НДФЛ"],
        })

    if profile.charity_amount and profile.charity_amount > 0:
        amount = _return_from_base(profile.charity_amount)
        deductions.append({
            "type": "charity",
            "title": "Вычет на благотворительность",
            "amount": float(amount),
            "article": "ст. 219 НК РФ п. 1",
        })
        documents.append({
            "deduction_type": "charity",
            "docs": ["Платёжные документы", "Договор пожертвования", "Справка 2-НДФЛ"],
        })

    total = Decimal(str(sum(d["amount"] for d in deductions))).quantize(Decimal("0.01"))
    return deductions, total, documents
