# Задачи MVP: AI Финансовый Советник

**Срок:** 6 недель  
**Команда:** 1 full-stack + Cursor AI  
**Приоритет:** работающий продукт, не идеальный код

> **Актуальный статус:** см. [STATUS.md](./STATUS.md). Код MVP реализован (~85%). Эпики E0–E8 — в основном готовы; E9 (деплой, CI, тесты) — не начат.

Легенда статусов: `[ ]` — не начато, `[~]` — частично, `[x]` — готово

## Сводка по эпикам

| Эпик | Название | Статус |
|------|----------|--------|
| E0 | Инфраструктура | [x] кроме CI |
| E1 | Auth | [~] email ✅, Google backend ✅, Google UI ❌ |
| E2 | Лендинг | [x] |
| E3 | Онбординг | [x] |
| E4 | Dashboard + profile | [x] |
| E5 | Чат DeepSeek | [~] без UI лимита 50 msg |
| E6 | Бюджет | [~] без графика и preview CSV |
| E7 | Цели | [~] без AI-подсказки |
| E8 | Налоги + RAG | [~] ingest вручную |
| E9 | Деплой | [ ] |

---

## Эпик 0: Инфраструктура и каркас

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| E0-01 | Инициализация монорепо: `frontend/`, `backend/`, `rag/`, `docker-compose.yml` | P0 | 4h | — |
| E0-02 | PostgreSQL 16 + pgvector + Redis в Docker Compose | P0 | 2h | E0-01 |
| E0-03 | FastAPI: структура `api/`, `services/`, `models/`, healthcheck | P0 | 3h | E0-01 |
| E0-04 | Next.js 14: App Router, Tailwind, shadcn/ui, базовый layout | P0 | 4h | E0-01 |
| E0-05 | CI: GitHub Actions — lint + build frontend/backend | P1 | 2h | E0-03, E0-04 |
| E0-06 | `.env.example` для всех сервисов, README с инструкцией запуска | P0 | 1h | E0-02 |

**DoD эпика:** `docker compose up` поднимает все сервисы; frontend и backend отвечают на healthcheck.

---

## Эпик 1: Аутентификация (NextAuth → FastAPI)

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| E1-01 | SQLAlchemy модели: `users` | P0 | 2h | E0-02 |
| E1-02 | FastAPI: `POST /api/auth/register`, `POST /api/auth/login` (bcrypt, JWT) | P0 | 4h | E1-01 |
| E1-03 | FastAPI: refresh token (httpOnly cookie), `POST /api/auth/logout`, `GET /api/auth/me` | P0 | 4h | E1-02 |
| E1-04 | FastAPI: Google OAuth — `POST /api/auth/google` (code → user + JWT) | P0 | 4h | E1-02 |
| E1-05 | Middleware FastAPI: JWT validation, user isolation | P0 | 3h | E1-03 |
| E1-06 | NextAuth: Credentials provider → прокси к FastAPI login/register | P0 | 4h | E1-02 |
| E1-07 | NextAuth: Google provider → прокси к FastAPI `/api/auth/google` | P0 | 3h | E1-04 |
| E1-08 | NextAuth: JWT callback — хранение access/refresh, auto-refresh | P0 | 4h | E1-03 |
| E1-09 | Frontend: страницы `/auth/login`, `/auth/register` | P0 | 4h | E1-06 |
| E1-10 | Frontend: route guard — редирект неавторизованных | P0 | 2h | E1-08 |
| E1-11 | Frontend: чекбокс согласия на обработку ПДн при регистрации | P0 | 1h | E1-09 |

**DoD эпика:** регистрация email + Google OAuth работает; защищённые роуты недоступны без сессии.

---

## Эпик 2: Лендинг

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| E2-01 | Страница `/`: hero, 5 фич MVP, social proof placeholder | P0 | 4h | E0-04 |
| E2-02 | CTA «Начать бесплатно» → `/auth/register` или `/dashboard` | P0 | 1h | E2-01, E1-10 |
| E2-03 | Адаптивная вёрстка лендинга (mobile-first) | P0 | 3h | E2-01 |
| E2-04 | Header: логин / личный кабинет в зависимости от сессии | P1 | 2h | E2-01, E1-08 |

**DoD эпика:** лендинг — точка входа; CTA корректно маршрутизирует пользователя.

---

## Эпик 3: Онбординг и профиль

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| E3-01 | SQLAlchemy модель: `profiles` | P0 | 2h | E1-01 |
| E3-02 | FastAPI: `POST /api/profile/onboarding` (step + data) | P0 | 4h | E3-01 |
| E3-03 | FastAPI: `GET /api/profile`, `PATCH /api/profile` | P0 | 3h | E3-01 |
| E3-04 | Service `scoring.py`: Financial Health Score (4 компонента) | P0 | 3h | E3-01 |
| E3-05 | Генерация персонального плана из 3 шагов (rule-based + шаблоны) | P0 | 3h | E3-04 |
| E3-06 | Frontend: `/onboarding` — 3 шага, прогресс-бар, валидация | P0 | 8h | E3-02 |
| E3-07 | Frontend: экран результата — Health Score + план | P0 | 4h | E3-04, E3-06 |
| E3-08 | Редирект: незавершённый онбординг → `/onboarding` | P0 | 1h | E3-06, E1-10 |
| E3-09 | Компонент `HealthScoreCard` | P0 | 3h | E3-04 |
| E3-10 | Компонент `OnboardingStep` | P0 | 2h | E3-06 |

**DoD эпика:** онбординг ≤ 7 мин; Health Score пересчитывается при изменении профиля.

---

## Эпик 4: Dashboard и layout

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| E4-01 | Layout: sidebar + header, навигация по разделам | P0 | 4h | E0-04 |
| E4-02 | `/dashboard`: HealthScoreCard, быстрые действия, последние события | P0 | 4h | E3-09, E4-01 |
| E4-03 | `/profile`: редактирование профиля, Health Score, удаление аккаунта | P0 | 6h | E3-03 |
| E4-04 | FastAPI: `DELETE /api/auth/me` — каскадное удаление ПДн | P0 | 3h | E1-05 |
| E4-05 | Страница политики конфиденциальности (статическая) | P0 | 2h | E2-01 |

**DoD эпика:** навигация между разделами; профиль редактируется; аккаунт удаляется.

---

## Эпик 5: Чат-ассистент (DeepSeek)

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| E5-01 | SQLAlchemy: `chat_sessions`, `messages` | P0 | 2h | E1-01 |
| E5-02 | Service `ai_service.py`: клиент DeepSeek API | P0 | 4h | E0-03 |
| E5-03 | Prompt `finance_assistant.txt` — system prompt с профилем | P0 | 2h | E5-02 |
| E5-04 | FastAPI: CRUD сессий, `GET messages` | P0 | 3h | E5-01 |
| E5-05 | FastAPI: `POST /api/chat/message` — SSE стриминг | P0 | 6h | E5-02, E5-03 |
| E5-06 | Счётчик сообщений Free: 50/мес (Redis или БД) | P0 | 3h | E5-05 |
| E5-07 | Frontend: `/chat` — список сессий, окно чата | P0 | 6h | E5-05 |
| E5-08 | Frontend: `ChatMessage` — Markdown рендеринг | P0 | 3h | E5-07 |
| E5-09 | Frontend: `QuickPrompt`, кнопка «Новый чат» | P0 | 2h | E5-07 |
| E5-10 | UI: предупреждение при приближении к лимиту 50 сообщений | P1 | 2h | E5-06 |

**DoD эпика:** чат стримит ответы DeepSeek с профилем; история сохраняется; лимит 50/мес enforced.

---

## Эпик 6: Бюджет

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| E6-01 | SQLAlchemy: `transactions` | P0 | 2h | E1-01 |
| E6-02 | FastAPI: CRUD `/api/budget/transactions` | P0 | 4h | E6-01 |
| E6-03 | Service `csv_parser.py`: парсеры Сбер + Тинькофф | P0 | 6h | E6-01 |
| E6-04 | FastAPI: `POST /api/budget/import-csv` → preview | P0 | 4h | E6-03 |
| E6-05 | AI-категоризация транзакций (DeepSeek) | P0 | 4h | E5-02, E6-04 |
| E6-06 | FastAPI: `POST /api/budget/import-csv/confirm` | P0 | 2h | E6-04 |
| E6-07 | Prompt `budget_agent.txt` + `POST /api/budget/analyze` (SSE) | P0 | 4h | E5-02, E6-02 |
| E6-08 | Frontend: `/budget` — форма, таблица, фильтр по месяцу | P0 | 6h | E6-02 |
| E6-09 | Frontend: `TransactionRow`, столбчатый график по категориям | P0 | 4h | E6-08 |
| E6-10 | Frontend: загрузка CSV, preview, редактирование категорий | P0 | 6h | E6-04 |
| E6-11 | Авто-анализ при ≥ 10 транзакций | P1 | 2h | E6-07 |

**DoD эпика:** ручной ввод и CSV импорт работают; AI-анализ выдаёт топ-3 и рекомендации.

---

## Эпик 7: Финансовые цели

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| E7-01 | SQLAlchemy: `goals` | P0 | 2h | E1-01 |
| E7-02 | Service: расчёт FV, monthly_deposit, сценарии (+10%, +1 год) | P0 | 4h | E7-01 |
| E7-03 | FastAPI: CRUD `/api/goals`, `GET /api/goals/{id}` с расчётами | P0 | 4h | E7-02 |
| E7-04 | Лимит Free: max 1 active goal | P0 | 1h | E7-03 |
| E7-05 | Frontend: `/goals` — список, форма создания | P0 | 4h | E7-03 |
| E7-06 | Frontend: `/goals/[id]` — прогресс, сценарии | P0 | 4h | E7-02 |
| E7-07 | Frontend: `GoalCard`, `GoalForm` | P0 | 3h | E7-05 |
| E7-08 | AI-подсказка: откуда взять деньги (из budget analyze) | P1 | 3h | E6-07, E7-06 |

**DoD эпика:** цель создаётся, FV рассчитывается, сценарии отображаются; лимит 1 цель enforced.

---

## Эпик 8: Налоговый советник (формулы + AI)

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| E8-01 | SQLAlchemy: `tax_profiles` | P0 | 2h | E1-01 |
| E8-02 | Service `tax_calculator.py`: детерминированные формулы вычетов | P0 | 6h | E8-01 |
| E8-03 | FastAPI: `GET/POST /api/tax/profile` | P0 | 3h | E8-01 |
| E8-04 | FastAPI: `POST /api/tax/calculate` → `{ deductions[], total_return }` | P0 | 3h | E8-02 |
| E8-05 | RAG: `knowledge_chunks` + `rag/ingest.py` | P0 | 6h | E0-02 |
| E8-06 | Подготовка документов: `nk_rf_excerpts.md`, `tax_deductions.md`, и др. | P0 | 4h | E8-05 |
| E8-07 | Service `rag_service.py`: поиск по pgvector | P0 | 4h | E8-05 |
| E8-08 | Prompt `tax_agent.txt` + `POST /api/tax/ask` (SSE) | P0 | 4h | E8-07, E5-02 |
| E8-09 | Frontend: `/tax` — анкета, результаты расчёта | P0 | 6h | E8-04 |
| E8-10 | Frontend: `TaxResultCard`, список документов, инструкция | P0 | 4h | E8-09 |
| E8-11 | AI объясняет результат `/api/tax/calculate`, не пересчитывает суммы | P0 | 2h | E8-04, E8-08 |

**DoD эпика:** суммы вычетов считаются формулами; AI объясняет с опорой на RAG и НК РФ.

---

## Эпик 9: Деплой и финализация

| ID | Задача | Приоритет | Оценка | Зависимости |
|----|--------|-----------|--------|-------------|
| E9-01 | Production Docker Compose + nginx reverse proxy + TLS | P0 | 4h | E0-02 |
| E9-02 | Деплой на VPS в РФ | P0 | 4h | E9-01 |
| E9-03 | E2E smoke-тест happy path | P0 | 4h | все эпики |
| E9-04 | Багфикс, полировка UI | P1 | 8h | E9-03 |
| E9-05 | Мониторинг: логи AI (user_id, tokens, cost estimate) | P1 | 3h | E5-05 |

**DoD эпика:** продукт доступен по HTTPS; happy path проходится без ошибок.

---

## Сводка по неделям

| Недели | Эпики | Фокус |
|--------|-------|-------|
| 1 | E0, E1, E2 | Инфра, auth, лендинг |
| 2 | E3, E4 | Онбординг, dashboard, profile |
| 3 | E5 | Чат DeepSeek |
| 4 | E6 | Бюджет + CSV |
| 5 | E7, E8 | Цели + налоги |
| 6 | E9 | Деплой, тесты, баги |

---

## Критический путь

```
E0 → E1 → E3 → E5 → E6 → E9
         ↘ E2
         ↘ E4
              E7 → E9
              E8 → E9
```

**Блокеры:** без E1 (auth) не начать защищённые модули; без E3 (профиль) не персонализировать чат; без E8-02 (формулы) Tax Agent может галлюцинировать суммы.

---

## Backlog (v1, не MVP)

- Premium + ЮKassa
- Email D3/D7
- Инвестиционный портфель
- Интеграция брокеров
- 3-НДФЛ автозаполнение
- Мобильное приложение
