
# Real Estate Forecasting Service

Монорепозиторий ВКР на тему: «Разработка системы для прогнозирования цен на жилую недвижимость города Владивостока методами машинного обучения».

## Состав

1. auth-service — сервис аутентификации и авторизации;
2. main-backend — основной backend: API-шлюз, прогнозы пользователя, интеграция с auth-service и forecasting-service;
3. forecasting-service — парсинг объявлений c агрегаторов недвижимости, хранение данных в SQLite, обработка данных, ML-пайплайн, выдача прогнозов; 
4. react-2fa-auth — фронтенд-часть сервиса.

Инфраструктура поднимается через корневой docker-compose.yml.

## Технологический стек
Backend: Python 3.12, FastAPI, SQLAlchemy + asyncpg, XGBoost, scikit-learn, python-jose (JWT), Argon2 (хеширование паролей), pyotp (TOTP).

Frontend: React 18, TypeScript, Vite, Tailwind CSS, Zustand, React Hook Form, Zod, Axios.
Инфраструктура: PostgreSQL 16, Redis 7, Docker Compose.

Менеджеры пакетов: Poetry (auth-service), uv (main-backend, forecasting-service), npm (frontend).


## Требования
Docker и Docker Compose

Python 3.12

Node.js 20+

Poetry и uv

## Быстрый старт

### 1. Клонировать и подготовить .env
```
git clone https://github.com/DepartmentOfSoftwareEngineeringFEFU/B9122-09.03.04-Mikhailov_Konstantin.git
cd B9122-09.03.04-Mikhailov_Konstantin
cp .env.example .env
```
### 2. Поднять инфраструктуру
```
docker compose up -d
```
### 3. Установить зависимости сервисов
```
# auth-service
cd auth-service && poetry install && cd ..

# main-backend
cd main-backend && uv sync && cd ..

# forecasting-service
cd forecasting-service && uv sync && cd ..

# frontend
cd react-2fa-auth && npm install && cd ..
```
### 4. Применить миграции БД
```
cd auth-service && poetry run alembic upgrade head && cd ..
cd main-backend && uv run alembic upgrade head && cd ..
```
### 5. Запустить сервисы
```
# Терминал 1
cd auth-service
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Терминал 2
cd main-backend
uv run uvicorn src.main_backend.main:app --host 0.0.0.0 --port 8002 --reload

# Терминал 3
cd forecasting-service
uv run uvicorn src.forecasting_service.api.main:app --host 0.0.0.0 --port 8003 --reload

# Терминал 4
cd react-2fa-auth
npm run dev
```
## Переменные окружения
```В корневом .env.example перечислены основные переменные:
JWT_ACCESS_SECRET_KEY — общий секрет для подписи JWT (должен совпадать в auth-service и main-backend)
JWT_ALGORITHM, JWT_ISSUER, JWT_AUDIENCE — параметры JWT
INTERNAL_SERVICE_TOKEN — токен для internal API
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
AUTH_POSTGRES_DB, MAIN_POSTGRES_DB
REDIS_URL
VITE_API_AUTH_URL, VITE_API_MAIN_URL — URL для фронтенда```

