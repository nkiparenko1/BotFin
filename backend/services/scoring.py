"""Financial Health Score calculation."""

from decimal import Decimal

from models import Profile


def _to_float(value: Decimal | None) -> float:
    return float(value or 0)


def calculate_health_score(profile: Profile) -> int:
    """Calculate Financial Health Score (0-100)."""
    score = 0
    income = _to_float(profile.monthly_income)
    fixed = _to_float(profile.fixed_expenses)
    variable = _to_float(profile.variable_expenses)
    expenses = fixed + variable
    savings = _to_float(profile.savings)
    loan_payment = _to_float(profile.mortgage_payment) + _to_float(profile.loan_payment)

    if income > 0:
        savings_rate = (income - expenses) / income * 100
        if savings_rate > 20:
            score += 30
        debt_ratio = loan_payment / income * 100
        if debt_ratio < 30:
            score += 25

    if expenses > 0 and savings / expenses > 3:
        score += 25

    if profile.main_goal and profile.goal_years:
        score += 20

    return min(score, 100)


def build_action_plan(profile: Profile) -> list[str]:
    """Generate 3-step personal action plan."""
    steps: list[str] = []
    income = _to_float(profile.monthly_income)
    fixed = _to_float(profile.fixed_expenses)
    variable = _to_float(profile.variable_expenses)
    expenses = fixed + variable
    savings = _to_float(profile.savings)

    if expenses > 0 and savings / expenses < 3:
        target = expenses * 3
        steps.append(
            f"Создайте подушку безопасности: цель {target:,.0f} ₽ (3 месяца расходов). "
            f"Сейчас накоплено {savings:,.0f} ₽."
        )
    else:
        steps.append("Подушка безопасности в норме — рассмотрите инвестирование излишков.")

    if income > 0 and (income - expenses) / income < 0.2:
        steps.append(
            f"Оптимизируйте расходы: сейчас вы тратите {expenses/income*100:.0f}% дохода. "
            "Цель — оставлять минимум 20% на сбережения."
        )
    else:
        steps.append("Норма сбережений хорошая — направьте часть средств на финансовую цель.")

    goal_labels = {
        "emergency": "подушку безопасности",
        "apartment": "квартиру",
        "pension": "пенсию",
        "education": "образование",
    }
    goal_name = goal_labels.get(profile.main_goal or "", profile.main_goal or "финансовую цель")
    if profile.goal_years:
        steps.append(f"Поставьте цель «{goal_name}» на {profile.goal_years} лет и откройте раздел «Цели».")
    else:
        steps.append("Определите главную финансовую цель и срок в разделе «Цели».")

    return steps[:3]
