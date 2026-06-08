# AI Финансовый Советник (BotFin)

MVP веб-приложения: AI-ассистент для управления личными финансами, бюджета, целей и налоговых вычетов РФ.

**Статус:** код MVP реализован (~85%), локальный запуск через Docker. Прод-деплой и тесты — в backlog.

Подробнее: **[docs/STATUS.md](docs/STATUS.md)** — что сделано, что осталось, как проверить.

---

## Что реализовано

| Модуль | Backend | Frontend |
|--------|---------|----------|
| Лендинг + CTA | — | `/` |
| Auth (email, NextAuth → JWT) | `/api/auth/*` | login, register |
| Онбординг + Health Score | `/api/profile/onboarding` | `/onboarding` |
| Dashboard | `/api/profile` | `/dashboard` |
| AI-чат (DeepSeek, SSE) | `/api/chat/*` | `/chat` |
| Бюджет + CSV + AI-анализ | `/api/budget/*` | `/budget` |
| Цели (FV, 1 лимит) | `/api/goals/*` | `/goals` |
| Налоги (формулы + AI) | `/api/tax/*` | `/tax` |
| Профиль + удаление ПДн | `DELETE /api/auth/me` | `/profile` |
| Политика конфиденциальности | — | `/privacy` |

---

## Быстрый старт (Docker)

```bash
cp .env.example .env
# Заполнить DEEPSEEK_API_KEY, NEXTAUTH_SECRET, JWT_SECRET

docker compose up -d --build
```

- Frontend: http://localhost:3000  
- Backend API: http://localhost:8000/docs  

**RAG (налоговый советник):** после первого запуска:

```bash
docker compose exec backend python rag/ingest.py --source rag/documents/
```

---

## Локальный запуск без Docker

**Требования:** PostgreSQL 16 + pgvector, Redis, Python 3.11+, Node.js 20+

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Стек

| Слой | Технология | Примечание |
|------|------------|------------|
| Frontend | Next.js 14, TypeScript, Tailwind | UI без shadcn/ui |
| Auth | NextAuth.js → FastAPI JWT | Google OAuth — backend готов, UI нет |
| Backend | FastAPI, Python 3.11, SSE | |
| БД | PostgreSQL 16 + pgvector | auto-create при старте |
| Кэш | Redis | в compose, лимиты чата в БД |
| LLM | DeepSeek API | chat + embeddings |
| Деплой | Docker Compose | prod/nginx — не настроен |

---

## Документация

| Документ | Описание |
|----------|----------|
| [docs/STATUS.md](docs/STATUS.md) | **Статус реализации — что сделано** |
| [docs/PRD.md](docs/PRD.md) | Product Requirements Document |
| [docs/TASKS.md](docs/TASKS.md) | Эпики и задачи с прогрессом |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Архитектура, API, auth flow |
| [docs/DATABASE.md](docs/DATABASE.md) | Схема БД |
| [docs/AI_AGENTS.md](docs/AI_AGENTS.md) | AI-агенты и промпты |

---

## MVP Scope (продуктовый)

- Лендинг → «Начать бесплатно»
- Онбординг + Financial Health Score
- Чат-ассистент (DeepSeek, SSE, 50 msg/мес)
- Бюджет: ручной ввод + CSV (Сбер, Тинькофф)
- 1 финансовая цель с расчётом FV
- Налоговый советник: формулы + RAG + AI-объяснения
- Только Free-тариф, без email и биллинга

---

## Структура проекта

```
BotFin/
├── frontend/       # Next.js 14
├── backend/        # FastAPI
├── rag/            # RAG-документы и ingest.py
├── docs/           # PRD, STATUS, архитектура
└── docker-compose.yml
```

---

## Лицензия

Proprietary. All rights reserved.
