FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    aiogram==3.* \
    aiogram-dialog==2.* \
    aiohttp \
    sqlalchemy[asyncio] \
    asyncpg \
    alembic \
    redis \
    pydantic-settings \
    dishka

COPY . .

CMD ["python", "main.py"]
