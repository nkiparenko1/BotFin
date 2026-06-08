"""Pydantic schemas."""

import uuid
from datetime import date as date_type, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    avatar_url: str | None
    provider: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    code: str


class ProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    age: int | None
    region: str | None
    family_status: str | None
    monthly_income: Decimal | None
    fixed_expenses: Decimal | None
    variable_expenses: Decimal | None
    savings: Decimal | None
    has_mortgage: bool
    mortgage_payment: Decimal | None
    has_loans: bool
    loan_payment: Decimal | None
    investment_exp: str | None
    risk_level: str | None
    main_goal: str | None
    goal_years: int | None
    health_score: int | None
    onboarding_done: bool

    model_config = {"from_attributes": True}


class ProfileResponse(BaseModel):
    profile: ProfileOut | None
    health_score: int | None


class OnboardingRequest(BaseModel):
    step: int
    data: dict[str, Any]


class OnboardingResponse(BaseModel):
    profile: ProfileOut
    health_score: int
    plan: list[str] | None = None


class MeResponse(BaseModel):
    user: UserOut
    profile: ProfileOut | None


class ChatSessionOut(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageRequest(BaseModel):
    session_id: uuid.UUID
    message: str
    include_profile: bool = True


class TransactionOut(BaseModel):
    id: uuid.UUID
    amount: Decimal
    category: str | None
    description: str | None
    date: date_type
    source: str

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    amount: Decimal
    category: str
    date: date_type
    description: str | None = None


class TransactionUpdate(BaseModel):
    amount: Decimal | None = None
    category: str | None = None
    date: date_type | None = None
    description: str | None = None


class ImportConfirmRequest(BaseModel):
    transactions: list[dict[str, Any]]


class GoalCreate(BaseModel):
    name: str
    target_amount: Decimal
    deadline_months: int
    expected_return: Decimal = Decimal("10.0")
    current_amount: Decimal = Decimal("0")


class GoalUpdate(BaseModel):
    name: str | None = None
    target_amount: Decimal | None = None
    deadline_months: int | None = None
    expected_return: Decimal | None = None
    current_amount: Decimal | None = None
    status: str | None = None


class GoalOut(BaseModel):
    id: uuid.UUID
    name: str
    target_amount: Decimal
    current_amount: Decimal
    monthly_deposit: Decimal | None
    expected_return: Decimal
    deadline_months: int
    status: str

    model_config = {"from_attributes": True}


class TaxProfileOut(BaseModel):
    id: uuid.UUID
    employment_type: str | None
    bought_property: bool
    property_amount: Decimal | None
    has_mortgage: bool
    mortgage_interest_paid: Decimal | None
    paid_education: bool
    education_amount: Decimal | None
    paid_medical: bool
    medical_amount: Decimal | None
    has_iis: bool
    iis_amount: Decimal | None
    paid_fitness: bool
    fitness_amount: Decimal | None
    paid_insurance: bool
    insurance_amount: Decimal | None
    charity_amount: Decimal | None
    tax_year: int

    model_config = {"from_attributes": True}


class TaxAskRequest(BaseModel):
    question: str
    calculation_id: uuid.UUID | None = None


class BudgetAnalyzeRequest(BaseModel):
    month: str | None = None
