
# Real Estate Forecasting Service

Монорепозиторий ВКР на тему: «Разработка системы для прогнозирования цен на жилую недвижимость города Владивостока методами машинного обучения».

## Сервисы

1. auth-service — сервис аутентификации и авторизации;
2. main-backend — основной backend: API-шлюз, прогнозы пользователя, интеграция с auth-service и forecasting-service;
3. forecasting-service — парсинг объявлений c агрегаторов недвижимости, хранение данных в SQLite, обработка данных, ML-пайплайн, выдача прогнозов; 
4. react-2fa-auth — фронтенд-часть сервиса.

## Технологический стек
Backend: Python 3.12, FastAPI, SQLAlchemy + asyncpg, XGBoost, scikit-learn, python-jose (JWT), Argon2 (хеширование паролей), pyotp (TOTP).

Frontend: React 18, TypeScript, Vite, Tailwind CSS, Zustand, React Hook Form, Zod, Axios.
Инфраструктура: PostgreSQL 16, Redis 7, Docker Compose.

Менеджеры пакетов:  uv, npm


## Требования
Docker и Docker Compose

Python 3.12

Node.js 20+

uv

## Быстрый старт

### 1. Клонировать репо
```
git clone https://github.com/DepartmentOfSoftwareEngineeringFEFU/B9122-09.03.04-Mikhailov_Konstantin.git
cd B9122-09.03.04-Mikhailov_Konstantin
```
### 2. Генерация переменных окружения
```
cd auth-service
cp .env.example .env
cd ..

cd main-backend
cp .env.example .env
cd ..

cd main-frontend
cd react-2fa-auth
cp .env.example .env
cd ..
cd ..
```
### 3. Установить зависимости сервисов
```
#backend
uv sync
# frontend
cd react-2fa-auth
npm install
```
### 4. Поднять БД и применить миграции
```
cd auth-service
docker compose up -d
uv run alembic upgrade head
cd ..

cd main-backend
docker compose up -d
uv run alembic upgrade head
cd ..
```
### 5. Запуск сервисов
```
# Терминал 1
cd auth-service
uv run uvicorn src.auth_service.main:app --reload --port 8001

# Терминал 2
cd main-backend
uv run uvicorn src.main_backend.main:app --reload --port 8002

# Терминал 3
cd forecasting-service
uv run uvicorn src.forecasting_service.api.main:app --reload --port 8003

# Терминал 4
cd main-frontend
cd react-2fa-auth
npm run dev
```
## Переменные окружения
```
В корневых папках сервисов auth, main-backend и main-frontend есть .env.example, где перечислены основные переменные:
JWT_ACCESS_SECRET_KEY — общий секрет для подписи JWT (должен совпадать в auth-service и main-backend)
JWT_ALGORITHM, JWT_ISSUER, JWT_AUDIENCE — параметры JWT
INTERNAL_SERVICE_TOKEN — токен для internal API
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
AUTH_POSTGRES_DB, MAIN_POSTGRES_DB
VITE_API_AUTH_URL, VITE_API_MAIN_URL — URL для фронтенда

```

## 6 Регистрация и авторизация
При запуске всех сервисов по адресу ``` localhost:3000 ``` откроется пользовательский интерфейс.

Для быстрой демонстрации функция подтвеждения email временно отлючена, поэтому для регистрации можно использовать произвольный email адрес.

После регистрации по адресу ```localhost:3000/login``` пройдите этап авторизации для входа в систему.

