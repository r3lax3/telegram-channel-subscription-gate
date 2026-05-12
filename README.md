# Деплой

```bash
git clone <repo> && cd telegram-channel-subscription-gate
cp example.env .env  # заполнить bot_token, channel_id, owner_ids, prodamus_*, webhook_host
docker compose up -d --build
```

Вебхук Prodamus: `POST {webhook_host}/prodamus/webhook` (порт 8080, проксируй через nginx/caddy с HTTPS).

Бот должен быть **админом** в канале с правами «Пригласительные ссылки» и «Бан участников». Логи: `./logs`, инвайт-ссылка: `./data/invite_link.txt`.

Админ-панель в боте: `/admin` (доступна `owner_ids` из `.env`).
