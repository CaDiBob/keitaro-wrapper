# Обёртка над Keitaro: создание кампаний и редактор офферов.

### Установка

```
git clone https://github.com/CaDiBob/keitaro-wrapper.git && cd keitaro-wrapper
```

[uv](https://docs.astral.sh/uv/#installation) и [Docker](https://docs.docker.com/get-docker/) должны быть установлены

```
uv sync
```

### Настройки

Скопируйте `.env.example` в `.env`:
```
cp .env.example .env
```

Впишите в `.env` свой ключ Admin API из админки Keitaro:
```
API_KEY=ваш ключ
```

Доступы к PostgreSQL для локальной разработки уже прописаны в `.env.example`, менять их не нужно: базу с такими доступами поднимет `docker compose up -d`.
```
DB_HOST=localhost
DB_PORT=5433
DB_USER=keitaro
DB_PASS=keitaro
DB_NAME=keitaro_wrapper
```

Необязательные настройки:
```
BASE_URL=адрес трекера, по умолчанию https://keitaro-for-tests.etolegko.com
DOMAIN_NAME=домен новых кампаний, по умолчанию первый из списка
GROUP_NAME=группа новых кампаний, по умолчанию FORTESTS
SOURCE_NAME=источник новых кампаний, по умолчанию FORTESTS
LOG_LEVEL=уровень логирования, по умолчанию INFO
```

### Запуск для разработки

Запустите PostgreSQL в Docker:
```
docker compose up -d
```

При первом запуске и после каждого обновления кода примените миграции, без них таблиц в базе не будет:
```
uv run alembic upgrade head
```

Запустите приложение с перезагрузкой при изменении кода:
```
uv run uvicorn app.main:app --reload
```

Интерфейс откроется на http://localhost:8000, документация API — на http://localhost:8000/docs.

Новая миграция после изменения моделей:
```
uv run alembic revision --autogenerate -m "описание"
```

### Запуск в проде

Приложение и PostgreSQL в Docker, миграции применяются при старте контейнера:
```
docker compose -f docker-compose.prod.yml up -d --build
```

Порт приложения по умолчанию 8000, другой задаётся переменной `APP_PORT`:
```
APP_PORT=80 docker compose -f docker-compose.prod.yml up -d --build
```

Остановка:
```
docker compose -f docker-compose.prod.yml down
```

### Тесты

```
uv run pytest
```
