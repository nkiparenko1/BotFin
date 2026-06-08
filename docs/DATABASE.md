# Схема базы данных

**СУБД:** PostgreSQL 16  
**Расширения:** `pgvector`, `pgcrypto` (UUID)  
**Конвенции:** UUID primary keys, `timestamptz` для дат

> **Реализация:** все модели в `backend/models.py`. Таблицы создаются при старте приложения (`main.py` → `Base.metadata.create_all`). Alembic-миграции не используются.

---

## ER-диаграмма (упрощённая)

```
users ──1:1── profiles
  │
  ├──1:N── chat_sessions ──1:N── messages
  ├──1:N── transactions
  ├──1:N── goals
  └──1:1── tax_profiles

knowledge_chunks (RAG, без FK)
```

---

## Таблицы

### users

```sql
CREATE TABLE users (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email       VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),          -- NULL для Google OAuth
  name        VARCHAR(255),
  avatar_url  TEXT,
  provider    VARCHAR(50) DEFAULT 'email',  -- email | google
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### profiles

```sql
CREATE TABLE profiles (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  age               INT,
  region            VARCHAR(100),
  family_status     VARCHAR(50),   -- single | couple | with_children
  monthly_income    DECIMAL(15,2),
  fixed_expenses    DECIMAL(15,2),
  variable_expenses DECIMAL(15,2),
  savings           DECIMAL(15,2),
  has_mortgage      BOOLEAN DEFAULT false,
  mortgage_payment  DECIMAL(15,2),
  has_loans         BOOLEAN DEFAULT false,
  loan_payment      DECIMAL(15,2),
  investment_exp    VARCHAR(50),   -- none | read | trading
  risk_level        VARCHAR(50),   -- conservative | moderate | aggressive
  main_goal         VARCHAR(100),
  goal_years        INT,
  health_score      INT,           -- 0-100, пересчитывается
  onboarding_done   BOOLEAN DEFAULT false,
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);
```

### chat_sessions

```sql
CREATE TABLE chat_sessions (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
  title      VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### messages

```sql
CREATE TABLE messages (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role       VARCHAR(20) NOT NULL,  -- user | assistant
  content    TEXT NOT NULL,
  tokens     INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_session ON messages(session_id, created_at);
```

### chat_usage (лимит Free: 50/мес)

```sql
CREATE TABLE chat_usage (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
  year_month VARCHAR(7) NOT NULL,   -- '2026-06'
  count      INT DEFAULT 0,
  UNIQUE(user_id, year_month)
);
```

### transactions

```sql
CREATE TABLE transactions (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  amount      DECIMAL(15,2) NOT NULL,
  category    VARCHAR(100),
  description TEXT,
  date        DATE NOT NULL,
  source      VARCHAR(50) DEFAULT 'manual',  -- manual | csv_import
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_date ON transactions(user_id, date DESC);
```

**Категории:** `food`, `transport`, `housing`, `subscriptions`, `entertainment`, `health`, `other`

### goals

```sql
CREATE TABLE goals (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
  name            VARCHAR(255) NOT NULL,
  target_amount   DECIMAL(15,2) NOT NULL,
  current_amount  DECIMAL(15,2) DEFAULT 0,
  monthly_deposit DECIMAL(15,2),
  expected_return DECIMAL(5,2) DEFAULT 10.0,
  deadline_months INT NOT NULL,
  status          VARCHAR(50) DEFAULT 'active',  -- active | achieved | paused
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_goals_user_status ON goals(user_id, status);
```

### tax_profiles

```sql
CREATE TABLE tax_profiles (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  employment_type        VARCHAR(50),  -- employee | self_employed | entrepreneur
  bought_property        BOOLEAN DEFAULT false,
  property_amount        DECIMAL(15,2),
  has_mortgage           BOOLEAN DEFAULT false,
  mortgage_interest_paid DECIMAL(15,2),
  paid_education         BOOLEAN DEFAULT false,
  education_amount       DECIMAL(15,2),
  paid_medical           BOOLEAN DEFAULT false,
  medical_amount         DECIMAL(15,2),
  has_iis                BOOLEAN DEFAULT false,
  iis_amount             DECIMAL(15,2),
  paid_fitness           BOOLEAN DEFAULT false,
  fitness_amount         DECIMAL(15,2),
  paid_insurance         BOOLEAN DEFAULT false,
  insurance_amount       DECIMAL(15,2),
  charity_amount         DECIMAL(15,2) DEFAULT 0,
  tax_year               INT DEFAULT 2025,
  updated_at             TIMESTAMPTZ DEFAULT NOW()
);
```

### tax_calculations (история расчётов для AI-объяснений)

```sql
CREATE TABLE tax_calculations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
  deductions    JSONB NOT NULL,       -- [{ type, amount, article }]
  total_return  DECIMAL(15,2) NOT NULL,
  documents     JSONB,                -- [{ deduction_type, docs[] }]
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tax_calc_user ON tax_calculations(user_id, created_at DESC);
```

### knowledge_chunks (RAG)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_chunks (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source     VARCHAR(255),   -- nk_rf | fns | minfin
  topic      VARCHAR(100),   -- tax_deduction | iis | mortgage | ...
  content    TEXT NOT NULL,
  embedding  vector(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_knowledge_embedding
  ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

---

## Каскадное удаление (152-ФЗ)

`DELETE /api/auth/me` удаляет `users` → CASCADE:
- profiles, chat_sessions → messages, transactions, goals, tax_profiles, tax_calculations, chat_usage

---

## Миграции

**Текущая реализация:** таблицы создаются автоматически при запуске backend:

```python
# backend/main.py (lifespan)
await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
await conn.run_sync(Base.metadata.create_all)
```

**План (опционально):** перейти на Alembic для prod:

```bash
cd backend
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```
