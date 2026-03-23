import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Telegram Channel
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))  # e.g. -1001234567890

# Admin user IDs (comma-separated)
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Prodamus
PRODAMUS_API_KEY = os.getenv("PRODAMUS_API_KEY", "")
PRODAMUS_DOMAIN = os.getenv("PRODAMUS_DOMAIN", "")  # e.g. yourshop.prodamus.link
PRODAMUS_SECRET_KEY = os.getenv("PRODAMUS_SECRET_KEY", "")  # for webhook signature verification

# Subscription
SUBSCRIPTION_PRICE = int(os.getenv("SUBSCRIPTION_PRICE", "990"))  # price in rubles
SUBSCRIPTION_DAYS = int(os.getenv("SUBSCRIPTION_DAYS", "30"))

# Recurring payment: try to charge N days before expiry
RECURRING_DAYS_BEFORE = int(os.getenv("RECURRING_DAYS_BEFORE", "3"))

# Webhook server (for Prodamus callbacks)
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/prodamus/webhook")

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/bot.db")

# Support
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@support")
