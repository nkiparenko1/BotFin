"""Unit tests for BotFin business logic."""

import uuid
from decimal import Decimal

import pytest

from models import Profile, TaxProfile
from services.auth_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from services.csv_parser import detect_and_parse, parse_sber_csv, parse_tinkoff_csv
from services.goals_service import calculate_monthly_deposit, goal_scenarios
from services.scoring import build_action_plan, calculate_health_score
from services.tax_calculator import calculate_deductions


class TestAuthUtils:
    def test_password_hash_and_verify(self):
        hashed = hash_password("secret123")
        assert hashed != "secret123"
        assert verify_password("secret123", hashed)
        assert not verify_password("wrong", hashed)

    def test_jwt_tokens(self):
        user_id = uuid.uuid4()
        access = create_access_token(user_id)
        refresh = create_refresh_token(user_id)
        assert decode_token(access, "access") == user_id
        assert decode_token(refresh, "refresh") == user_id

    def test_invalid_token_type(self):
        user_id = uuid.uuid4()
        access = create_access_token(user_id)
        with pytest.raises(ValueError):
            decode_token(access, "refresh")


class TestTaxCalculator:
    def _profile(self, **kwargs) -> TaxProfile:
        p = TaxProfile(user_id=uuid.uuid4())
        for k, v in kwargs.items():
            setattr(p, k, v)
        return p

    def test_property_deduction_capped(self):
        profile = self._profile(bought_property=True, property_amount=Decimal("3000000"))
        deductions, total, docs = calculate_deductions(profile)
        assert len(deductions) == 1
        assert deductions[0]["type"] == "property"
        assert deductions[0]["amount"] == 260000.0
        assert total == Decimal("260000.00")
        assert len(docs) == 1

    def test_mortgage_interest_capped(self):
        profile = self._profile(has_mortgage=True, mortgage_interest_paid=Decimal("5000000"))
        deductions, total, _ = calculate_deductions(profile)
        assert deductions[0]["amount"] == 390000.0
        assert total == Decimal("390000.00")

    def test_social_deduction_combined(self):
        profile = self._profile(
            paid_education=True,
            education_amount=Decimal("100000"),
            paid_medical=True,
            medical_amount=Decimal("80000"),
        )
        deductions, total, _ = calculate_deductions(profile)
        assert any(d["type"] == "social" for d in deductions)
        social = next(d for d in deductions if d["type"] == "social")
        assert social["amount"] == 19500.0  # min(180000, 150000 cap) * 0.13

    def test_iis_deduction_capped(self):
        profile = self._profile(has_iis=True, iis_amount=Decimal("500000"))
        deductions, _, _ = calculate_deductions(profile)
        assert deductions[0]["amount"] == 52000.0

    def test_empty_profile(self):
        deductions, total, docs = calculate_deductions(self._profile())
        assert deductions == []
        assert total == Decimal("0.00")
        assert docs == []


class TestGoalsService:
    def test_monthly_deposit_no_return(self):
        deposit = calculate_monthly_deposit(Decimal("120000"), Decimal("0"), 12, Decimal("0"))
        assert deposit == Decimal("10000.00")

    def test_monthly_deposit_with_return(self):
        deposit = calculate_monthly_deposit(Decimal("100000"), Decimal("10000"), 24, Decimal("10"))
        assert deposit > Decimal("0")
        assert deposit < Decimal("5000")

    def test_already_reached_target(self):
        deposit = calculate_monthly_deposit(Decimal("100000"), Decimal("100000"), 12, Decimal("10"))
        assert deposit == Decimal("0")

    def test_scenarios(self):
        deposit = Decimal("5000")
        scenarios = goal_scenarios(Decimal("200000"), Decimal("0"), 24, Decimal("10"), deposit)
        assert scenarios["deposit_plus_10_pct"] == 5500.0
        assert scenarios["months_plus_12"] == 36
        assert scenarios["deposit_with_extra_year"] < float(deposit)


class TestScoring:
    def _profile(self, **kwargs) -> Profile:
        p = Profile(user_id=uuid.uuid4())
        for k, v in kwargs.items():
            setattr(p, k, v)
        return p

    def test_high_score_profile(self):
        profile = self._profile(
            monthly_income=Decimal("100000"),
            fixed_expenses=Decimal("30000"),
            variable_expenses=Decimal("20000"),
            savings=Decimal("200000"),
            mortgage_payment=Decimal("10000"),
            main_goal="apartment",
            goal_years=5,
        )
        score = calculate_health_score(profile)
        assert score == 100

    def test_low_score_profile(self):
        profile = self._profile(
            monthly_income=Decimal("50000"),
            fixed_expenses=Decimal("40000"),
            variable_expenses=Decimal("10000"),
            savings=Decimal("10000"),
            mortgage_payment=Decimal("20000"),
        )
        score = calculate_health_score(profile)
        assert score < 50

    def test_action_plan_has_three_steps(self):
        profile = self._profile(
            monthly_income=Decimal("80000"),
            fixed_expenses=Decimal("30000"),
            variable_expenses=Decimal("20000"),
            savings=Decimal("50000"),
            main_goal="emergency",
            goal_years=2,
        )
        plan = build_action_plan(profile)
        assert len(plan) == 3
        assert all(isinstance(step, str) for step in plan)


class TestCsvParser:
    SBER_CSV = """Дата операции;Сумма;Описание
01.06.2025;1500,50;Магазин
02.06.2025;-500;Перевод
"""

    TINKOFF_CSV = """Дата операции;Сумма операции;Описание
2025-06-01;2500.00;Кафе
2025-06-02;0;Пропуск
"""

    def test_parse_sber(self):
        rows = parse_sber_csv(self.SBER_CSV)
        assert len(rows) == 2
        assert rows[0]["date"] == "2025-06-01"
        assert rows[0]["amount"] == 1500.5
        assert rows[1]["amount"] == 500.0

    def test_parse_tinkoff(self):
        rows = parse_tinkoff_csv(self.TINKOFF_CSV)
        assert len(rows) == 1
        assert rows[0]["amount"] == 2500.0

    def test_detect_tinkoff_by_filename(self):
        rows = detect_and_parse(self.TINKOFF_CSV, "tinkoff_export.csv")
        assert len(rows) == 1

    def test_detect_sber_default(self):
        rows = detect_and_parse(self.SBER_CSV, "export.csv")
        assert len(rows) == 2
