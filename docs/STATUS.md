# Статус реализации BotFin MVP

**Версия:** 1.0 (код)  
**Дата обновления:** Июнь 2026  
**Статус:** Реализовано локально, не задеплоено на прод

---

## 1. Краткое описание продукта

**BotFin** — веб-приложение AI-финансового советника для физических лиц в РФ. Пользователь регистрируется, проходит онбординг, получает **Financial Health Score** и персональный план, после чего может:

- общаться с AI-ассистентом (DeepSeek) с учётом профиля;
- вести бюджет и получать AI-анализ расходов;
- ставить финансовую цель с расчётом ежемесячного взноса;
- рассчитывать налоговые вычеты по формулам и получать объяснение от AI.

**Тариф:** только Free (50 сообщений в чате/мес, 1 активная цель). Без email-рассылок и биллинга.

---

## 2. Общий прогресс

| Область | Прогресс | Комментарий |
|---------|----------|-------------|
| Backend (FastAPI) | **95%** | Все основные API реализованы |
| Frontend (Next.js) | **90%** | Все экраны MVP, UI без shadcn/ui |
| База данных | **90%** | Модели + auto-create при старте |
| AI (DeepSeek) | **95%** | 3 агента, SSE-стриминг |
| RAG (налоги) | **80%** | Документы + ingest; индексация вручную |
| Docker / деплой | **60%** | docker-compose есть, prod/nginx — нет |
| CI/CD, тесты | **0%** | Не начато |

**Итого MVP (функционал):** ~**85%** — happy path реализован в коде, требуется запуск и проверка в среде с PostgreSQL + Node.js.

---

## 3. Что сделано

### 3.1 Инфраструктура

| Компонент | Файл / путь | Статус |
|-----------|-------------|--------|
| Монорепо | `frontend/`, `backend/`, `rag/`, `docs/` | ✅ |
| Docker Compose | `docker-compose.yml` | ✅ postgres, redis, backend, frontend |
| Переменные окружения | `.env.example`, `.env` (local, gitignore) | ✅ |
| Backend Dockerfile | `backend/Dockerfile` | ✅ |
| Frontend Dockerfile | `frontend/Dockerfile` | ✅ |
| Git ignore | `.gitignore` | ✅ |

### 3.2 Backend — API

| Модуль | Эндпоинты | Файл |
|--------|-----------|------|
| Auth | register, login, google, refresh, logout, me, delete me | `backend/api/auth.py` |
| Profile | onboarding, get, patch | `backend/api/profile.py` |
| Chat | sessions CRUD, message (SSE) | `backend/api/chat.py` |
| Budget | transactions CRUD, import-csv, analyze (SSE) | `backend/api/budget.py` |
| Goals | CRUD + FV-расчёты, сценарии | `backend/api/goals.py` |
| Tax | profile, calculate, ask (SSE) | `backend/api/tax.py` |
| Health | `GET /health` | `backend/main.py` |

### 3.3 Backend — сервисы

| Сервис | Назначение | Файл |
|--------|------------|------|
| `auth_utils` | bcrypt, JWT access/refresh | `backend/services/auth_utils.py` |
| `scoring` | Financial Health Score, план 3 шагов | `backend/services/scoring.py` |
| `ai_service` | DeepSeek chat + embeddings | `backend/services/ai_service.py` |
| `tax_calculator` | Детерминированные формулы вычетов | `backend/services/tax_calculator.py` |
| `goals_service` | FV, monthly_deposit, сценарии | `backend/services/goals_service.py` |
| `csv_parser` | Парсеры Сбер / Тинькофф CSV | `backend/services/csv_parser.py` |
| `rag_service` | pgvector semantic search | `backend/services/rag_service.py` |

### 3.4 Backend — промпты

| Агент | Файл |
|-------|------|
| Finance Assistant | `backend/prompts/finance_assistant.txt` |
| Tax Agent | `backend/prompts/tax_agent.txt` |
| Budget Analysis | `backend/prompts/budget_agent.txt` |

### 3.5 База данных

Все таблицы описаны в `backend/models.py`:

- `users`, `profiles`
- `chat_sessions`, `messages`, `chat_usage`
- `transactions`, `goals`
- `tax_profiles`, `tax_calculations`
- `knowledge_chunks` (pgvector)

Таблицы создаются автоматически при старте backend (`CREATE EXTENSION vector` + `metadata.create_all`).

### 3.6 Frontend — страницы

| Маршрут | Описание | Файл |
|---------|----------|------|
| `/` | Лендинг, CTA «Начать бесплатно» | `frontend/app/page.tsx` |
| `/auth/login` | Вход email + пароль | `frontend/app/auth/login/page.tsx` |
| `/auth/register` | Регистрация + согласие ПДн | `frontend/app/auth/register/page.tsx` |
| `/onboarding` | Анкета 3 шага | `frontend/app/onboarding/page.tsx` |
| `/dashboard` | Health Score, быстрые действия | `frontend/app/dashboard/page.tsx` |
| `/chat` | AI-чат, SSE, быстрые вопросы | `frontend/app/chat/page.tsx` |
| `/budget` | Транзакции, CSV, AI-анализ | `frontend/app/budget/page.tsx` |
| `/goals` | Список и создание цели | `frontend/app/goals/page.tsx` |
| `/goals/[id]` | Детали цели, сценарии | `frontend/app/goals/[id]/page.tsx` |
| `/tax` | Анкета, расчёт, AI-объяснение | `frontend/app/tax/page.tsx` |
| `/profile` | Профиль, удаление аккаунта | `frontend/app/profile/page.tsx` |
| `/privacy` | Политика конфиденциальности | `frontend/app/privacy/page.tsx` |

### 3.7 Frontend — инфраструктура

| Компонент | Файл |
|-----------|------|
| NextAuth → FastAPI JWT | `frontend/lib/auth.ts`, `frontend/app/api/auth/[...nextauth]/route.ts` |
| API-клиент + SSE | `frontend/lib/api-client.ts` |
| Route guard | `frontend/middleware.ts` |
| Layout + sidebar | `frontend/components/AppShell.tsx` |
| Health Score UI | `frontend/components/HealthScoreCard.tsx` |

### 3.8 RAG

| Компонент | Путь |
|-----------|------|
| Документы НК РФ / ФНС | `rag/documents/*.md` (5 файлов) |
| Скрипт индексации | `rag/ingest.py` |

---

## 4. Что не сделано / частично

| Задача | Статус | Примечание |
|--------|--------|------------|
| Google OAuth на фронте | ⚠️ Частично | Backend `POST /api/auth/google` есть; UI-кнопка Google не подключена |
| Auto-refresh JWT | ⚠️ Частично | Refresh endpoint есть; автоматическое обновление в NextAuth не реализовано |
| shadcn/ui | ❌ | Используется Tailwind + кастомные компоненты |
| Alembic миграции | ❌ | Вместо них `create_all` при старте |
| Redis для лимитов | ⚠️ | Redis в compose; счётчик чата в таблице `chat_usage` |
| Rate limiting | ❌ | Не реализован |
| Столбчатый график бюджета | ⚠️ | Сводка по категориям текстом, без chart library |
| CSV preview с редактированием | ⚠️ | Импорт без экрана preview — сразу confirm |
| Авто-анализ бюджета при ≥10 tx | ❌ | Только по кнопке |
| AI-подсказка «откуда взять деньги» для целей | ❌ | FV и сценарии есть, AI-подсказка нет |
| UI-предупреждение лимита 50 сообщений | ❌ | Лимит enforced на backend (429) |
| RAG ingest при деплое | ⚠️ | Запуск вручную: `python rag/ingest.py` |
| Production nginx + TLS | ❌ | |
| Деплой на VPS | ❌ | |
| GitHub Actions CI | ❌ | |
| E2E / smoke-тесты | ❌ | |
| AI logging (user_id, tokens) | ❌ | |
| S3 для файлов | ❌ | CSV обрабатывается in-memory |

---

## 5. Принятые решения (из PRD)

| Решение | Реализация |
|---------|------------|
| LLM | **DeepSeek API** (`deepseek-chat`) |
| Auth | **NextAuth.js** проксирует JWT к **FastAPI** |
| Налоги | **Формулы** на backend + **AI** только объясняет |
| Лендинг | `/` с CTA «Начать бесплатно» |
| Тариф | **Только Free** |
| Email | **Не используется** |

---

## 6. Как запустить

### Docker (рекомендуется)

```bash
cp .env.example .env
# DEEPSEEK_API_KEY, NEXTAUTH_SECRET, JWT_SECRET

docker compose up -d --build
```

- Frontend: http://localhost:3000  
- API docs: http://localhost:8000/docs  

### RAG (после первого запуска БД)

```bash
docker compose exec backend python rag/ingest.py --source rag/documents/
```

### Локально

1. PostgreSQL 16 + pgvector, Redis  
2. `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`  
3. `cd frontend && npm install && npm run dev` (Node.js 20+)

---

## 7. Happy path для проверки

1. `/` → «Начать бесплатно» → регистрация  
2. Онбординг 3 шага → Health Score + план  
3. `/chat` → задать вопрос → SSE-ответ с профилем  
4. `/budget` → добавить расход → «Проанализировать»  
5. `/tax` → заполнить анкету → «Рассчитать» → спросить AI  
6. `/goals` → создать цель (лимит 1)  
7. `/profile` → удаление аккаунта (опционально)

---

## 8. Структура репозитория

```
BotFin/
├── backend/
│   ├── api/              # auth, profile, chat, budget, goals, tax
│   ├── services/         # ai, scoring, tax, csv, rag, goals
│   ├── prompts/          # system prompts для DeepSeek
│   ├── models.py         # SQLAlchemy ORM
│   ├── schemas.py        # Pydantic
│   ├── main.py           # FastAPI entry
│   └── requirements.txt
├── frontend/
│   ├── app/              # страницы App Router
│   ├── components/       # AppShell, HealthScoreCard, Providers
│   ├── lib/              # auth, api-client
│   └── middleware.ts     # route guards
├── rag/
│   ├── documents/        # markdown для RAG
│   └── ingest.py
├── docs/                 # PRD, архитектура, задачи, статус
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 9. Связанные документы

- [PRD.md](./PRD.md) — требования к продукту  
- [TASKS.md](./TASKS.md) — эпики и задачи с отметками выполнения  
- [ARCHITECTURE.md](./ARCHITECTURE.md) — архитектура и API  
- [DATABASE.md](./DATABASE.md) — схема БД  
- [AI_AGENTS.md](./AI_AGENTS.md) — AI-агенты и промпты  
