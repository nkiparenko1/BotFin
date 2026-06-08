"""SQLAlchemy ORM models."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    """Registered user."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(50), default="email")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    profile: Mapped["Profile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tax_profile: Mapped["TaxProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    tax_calculations: Mapped[list["TaxCalculation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    chat_usage: Mapped[list["ChatUsage"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    """Financial profile from onboarding."""

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    age: Mapped[int | None] = mapped_column(Integer)
    region: Mapped[str | None] = mapped_column(String(100))
    family_status: Mapped[str | None] = mapped_column(String(50))
    monthly_income: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    fixed_expenses: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    variable_expenses: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    savings: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    has_mortgage: Mapped[bool] = mapped_column(Boolean, default=False)
    mortgage_payment: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    has_loans: Mapped[bool] = mapped_column(Boolean, default=False)
    loan_payment: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    investment_exp: Mapped[str | None] = mapped_column(String(50))
    risk_level: Mapped[str | None] = mapped_column(String(50))
    main_goal: Mapped[str | None] = mapped_column(String(100))
    goal_years: Mapped[int | None] = mapped_column(Integer)
    health_score: Mapped[int | None] = mapped_column(Integer)
    onboarding_done: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="profile")


class ChatSession(Base):
    """Chat conversation session."""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """Chat message."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    __table_args__ = (Index("idx_messages_session", "session_id", "created_at"),)


class ChatUsage(Base):
    """Monthly chat message counter for Free tier."""

    __tablename__ = "chat_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    year_month: Mapped[str] = mapped_column(String(7), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="chat_usage")

    __table_args__ = (UniqueConstraint("user_id", "year_month"),)


class Transaction(Base):
    """Budget transaction."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="manual")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="transactions")

    __table_args__ = (Index("idx_transactions_user_date", "user_id", "date"),)


class Goal(Base):
    """Financial goal."""

    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0)
    monthly_deposit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    expected_return: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10.0"))
    deadline_months: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="goals")

    __table_args__ = (Index("idx_goals_user_status", "user_id", "status"),)


class TaxProfile(Base):
    """Tax questionnaire profile."""

    __tablename__ = "tax_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    employment_type: Mapped[str | None] = mapped_column(String(50))
    bought_property: Mapped[bool] = mapped_column(Boolean, default=False)
    property_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    has_mortgage: Mapped[bool] = mapped_column(Boolean, default=False)
    mortgage_interest_paid: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    paid_education: Mapped[bool] = mapped_column(Boolean, default=False)
    education_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    paid_medical: Mapped[bool] = mapped_column(Boolean, default=False)
    medical_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    has_iis: Mapped[bool] = mapped_column(Boolean, default=False)
    iis_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    paid_fitness: Mapped[bool] = mapped_column(Boolean, default=False)
    fitness_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    paid_insurance: Mapped[bool] = mapped_column(Boolean, default=False)
    insurance_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    charity_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), default=0)
    tax_year: Mapped[int] = mapped_column(Integer, default=2025)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="tax_profile")


class TaxCalculation(Base):
    """Stored tax calculation for AI explanations."""

    __tablename__ = "tax_calculations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    deductions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    total_return: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    documents: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="tax_calculations")

    __table_args__ = (Index("idx_tax_calc_user", "user_id", "created_at"),)


class KnowledgeChunk(Base):
    """RAG knowledge chunk with embedding."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str | None] = mapped_column(String(255))
    topic: Mapped[str | None] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
