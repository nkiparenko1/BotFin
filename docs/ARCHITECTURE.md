# Архитектура: AI Финансовый Советник

> **Реализация:** код соответствует описанной архитектуре. Отличия — см. [STATUS.md](./STATUS.md#4-что-не-сделано--частично).

## 0. Фактическая реализация (кратко)

| Аспект | PRD | Факт |
|--------|-----|------|
| UI kit | shadcn/ui | Tailwind + кастомные компоненты |
| Миграции БД | Alembic | `create_all` при старте FastAPI |
| Лимит чата | Redis | Таблица `chat_usage` |
| Refresh JWT | httpOnly cookie | В NextAuth session (access + refresh) |
| Google OAuth | NextAuth + FastAPI | Backend готов; кнопка на UI — нет |

## 1. Обзор системы
```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────▼───────────────────────────────────┐
│  Next.js 14 (frontend)                                       │
│  ├── / (лендинг)                                             │
│  ├── NextAuth.js (session, OAuth, JWT proxy)                 │
│  └── App Router pages + shadcn/ui                            │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST + SSE
┌─────────────────────────▼───────────────────────────────────┐
│  FastAPI (backend)                                           │
│  ├── /api/auth/*     JWT issue & validate                    │
│  ├── /api/profile/*  onboarding, Health Score                │
│  ├── /api/chat/*     SSE streaming                           │
│  ├── /api/budget/*   transactions, CSV, analyze              │
│  ├── /api/goals/*    FV calculations                         │
│  └── /api/tax/*      formulas + AI explain                   │
└──────┬──────────────┬──────────────┬─────────────────────────┘
       │              │              │
       ▼              ▼              ▼
  PostgreSQL      Redis         DeepSeek API
  + pgvector                    (chat + embeddings)
```

## 2. Структура проекта

```
BotFin/
├── frontend/                    # Next.js приложение
│   ├── app/
│   │   ├── page.tsx             # Лендинг
│   │   ├── (auth)/login/
│   │   ├── (auth)/register/
│   │   ├── onboarding/
│   │   ├── dashboard/
│   │   ├── chat/
│   │   ├── budget/
│   │   ├── goals/
│   │   │   └── [id]/
│   │   ├── tax/
│   │   ├── profile/
│   │   └── privacy/             # Политика ПДн
│   ├── components/
│   │   ├── ui/                  # shadcn/ui
│   │   ├── chat/
│   │   ├── budget/
│   │   ├── goals/
│   │   └── tax/
│   ├── lib/
│   │   ├── api-client.ts        # Fetch wrapper с JWT
│   │   └── auth.ts              # NextAuth config
│   └── middleware.ts            # Route guards
│
├── backend/
│   ├── api/
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── chat.py              # SSE
│   │   ├── budget.py
│   │   ├── goals.py
│   │   └── tax.py
│   ├── services/
│   │   ├── ai_service.py        # DeepSeek client
│   │   ├── rag_service.py       # pgvector search
│   │   ├── scoring.py           # Health Score
│   │   ├── tax_calculator.py    # Детерминированные формулы
│   │   └── csv_parser.py
│   ├── models/                  # SQLAlchemy
│   ├── prompts/
│   │   ├── finance_assistant.txt
│   │   ├── tax_agent.txt
│   │   └── budget_agent.txt
│   └── main.py
│
├── rag/
│   ├── documents/
│   │   ├── nk_rf_excerpts.md
│   │   ├── tax_deductions.md
│   │   ├── fns_instructions.md
│   │   ├── iis_guide.md
│   │   └── mortgage_deduction.md
│   └── ingest.py
│
├── docs/                        # Документация
├── docker-compose.yml
└── .env.example
```

## 3. Аутентификация: NextAuth как прокси

### 3.1 Поток регистрации (email)

```
1. User → /auth/register (Next.js form)
2. NextAuth CredentialsProvider.authorize()
3.   → POST FastAPI /api/auth/register { email, password, name }
4.   ← { user, access_token, refresh_token }
5. NextAuth jwt callback сохраняет tokens в session
6. Redirect → /onboarding
```

### 3.2 Поток Google OAuth

```
1. User → NextAuth GoogleProvider.signIn()
2. NextAuth получает authorization code
3.   → POST FastAPI /api/auth/google { code }
4.   ← { user, access_token, refresh_token }
5. Session создан, redirect по onboarding_done
```

### 3.3 API-запросы с фронта

```typescript
// lib/api-client.ts
const session = await getSession();
fetch(`${API_URL}/api/profile`, {
  headers: { Authorization: `Bearer ${session.accessToken}` }
});
```

NextAuth `jwt` callback обновляет access token через `POST /api/auth/refresh` при истечении (15 мин).

### 3.4 JWT на бэкенде

| Token | TTL | Хранение |
|-------|-----|----------|
| Access | 15 мин | NextAuth session (client-readable) |
| Refresh | 30 дней | httpOnly cookie + Redis blacklist on logout |

## 4. AI-слой (DeepSeek)

### 4.1 Единый клиент

`ai_service.py` инкапсулирует:
- Chat completions (streaming)
- Embeddings для RAG
- Подсчёт tokens для лимитов и логов

### 4.2 Агенты

| Endpoint | Agent | RAG | Источник истины |
|----------|-------|-----|-----------------|
| `POST /api/chat/message` | Finance Assistant | Нет | — |
| `POST /api/budget/analyze` | Budget Analysis | Нет | Aggregated transactions |
| `POST /api/tax/ask` | Tax Agent | Да | **Формулы** + RAG для статей |

### 4.3 Принцип Tax Agent

```
User заполняет анкету
    → POST /api/tax/calculate (формулы, без AI)
    → UI показывает суммы
    → POST /api/tax/ask (AI объясняет готовый результат + RAG)
```

AI **не пересчитывает** суммы — получает их в контексте как факт.

## 5. SSE-стриминг

### 5.1 Формат событий

```
Content-Type: text/event-stream

data: {"type": "text", "content": "Подушка"}
data: {"type": "text", "content": " безопасности —"}
data: {"type": "done", "message_id": "uuid", "tokens": 412}
```

### 5.2 Endpoints со стримингом

- `POST /api/chat/message`
- `POST /api/budget/analyze`
- `POST /api/tax/ask`

Frontend использует `EventSource` или `fetch` + `ReadableStream`.

## 6. API-контракты

### 6.1 Auth

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/api/auth/register` | `{ email, password, name }` | `{ user, access_token, refresh_token }` |
| POST | `/api/auth/login` | `{ email, password }` | `{ user, access_token, refresh_token }` |
| POST | `/api/auth/google` | `{ code }` | `{ user, access_token, refresh_token }` |
| POST | `/api/auth/refresh` | cookie | `{ access_token }` |
| POST | `/api/auth/logout` | — | 204 |
| GET | `/api/auth/me` | — | `{ user, profile }` |
| DELETE | `/api/auth/me` | — | 204 |

### 6.2 Profile

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/api/profile/onboarding` | `{ step, data }` | `{ profile, health_score, plan? }` |
| GET | `/api/profile` | — | `{ profile, health_score }` |
| PATCH | `/api/profile` | partial profile | `{ profile, health_score }` |

### 6.3 Chat

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/api/chat/sessions` | — | `[{ id, title, created_at }]` |
| POST | `/api/chat/sessions` | — | `{ session_id }` |
| GET | `/api/chat/sessions/{id}/messages` | — | `[{ role, content, created_at }]` |
| POST | `/api/chat/message` | `{ session_id, message, include_profile }` | SSE stream |
| DELETE | `/api/chat/sessions/{id}` | — | 204 |

### 6.4 Budget

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/api/budget/transactions` | `?month=2024-12` | `[transactions]` |
| POST | `/api/budget/transactions` | `{ amount, category, date, description }` | `{ transaction }` |
| PATCH | `/api/budget/transactions/{id}` | partial | `{ transaction }` |
| DELETE | `/api/budget/transactions/{id}` | — | 204 |
| POST | `/api/budget/import-csv` | multipart file | `{ preview: [] }` |
| POST | `/api/budget/import-csv/confirm` | `{ transactions[] }` | `{ imported_count }` |
| POST | `/api/budget/analyze` | `{ month? }` | SSE stream |

### 6.5 Goals

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/api/goals` | — | `[goals]` |
| POST | `/api/goals` | `{ name, target_amount, deadline_months, expected_return? }` | `{ goal, calculations }` |
| GET | `/api/goals/{id}` | — | `{ goal, calculations, scenarios }` |
| PATCH | `/api/goals/{id}` | partial | `{ goal, calculations }` |
| DELETE | `/api/goals/{id}` | — | 204 |

### 6.6 Tax

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/api/tax/profile` | — | `{ tax_profile }` |
| POST | `/api/tax/profile` | tax questionnaire | `{ tax_profile }` |
| POST | `/api/tax/calculate` | — | `{ deductions[], total_return, documents[] }` |
| POST | `/api/tax/ask` | `{ question, calculation_id? }` | SSE stream |

## 7. Лимиты Free-тарифа

| Ресурс | Лимит | Enforcement |
|--------|-------|-------------|
| Chat messages | 50 / calendar month | Redis counter `chat:{user_id}:{YYYY-MM}` |
| Active goals | 1 | DB check on POST /api/goals |
| Budget | Unlimited | — |
| Tax advisor | Unlimited | — |

## 8. Безопасность

- Все `/api/*` (кроме auth register/login) требуют valid JWT
- Row-level isolation: `user_id` из JWT сравнивается с owner записи
- AI logs: `{ user_id, agent, tokens, timestamp }` — без content
- CORS: только origin frontend
- Rate limiting: 60 req/min per user (Redis)

## 9. Деплой

```yaml
# docker-compose.yml services
- frontend (Next.js, port 3000)
- backend (FastAPI + uvicorn, port 8000)
- postgres (16 + pgvector)
- redis
- nginx (TLS termination, reverse proxy)
```

Переменные окружения — см. `.env.example`.
