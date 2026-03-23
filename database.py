import aiosqlite
import os
from datetime import datetime, timezone
from typing import Optional

from config import DATABASE_PATH


async def init_db():
    """Initialize database and create tables."""
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                starts_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                recurring_token TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_id TEXT UNIQUE,
                amount REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                prodamus_payment_id TEXT,
                recurring_token TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await db.commit()


async def upsert_user(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = COALESCE(excluded.username, users.username),
                first_name = COALESCE(excluded.first_name, users.first_name)
        """, (user_id, username, first_name))
        await db.commit()


async def get_active_subscription(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM subscriptions
            WHERE user_id = ? AND is_active = 1
              AND expires_at > datetime('now')
            ORDER BY expires_at DESC
            LIMIT 1
        """, (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def create_subscription(user_id: int, starts_at: str, expires_at: str, recurring_token: Optional[str] = None) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO subscriptions (user_id, starts_at, expires_at, recurring_token)
            VALUES (?, ?, ?, ?)
        """, (user_id, starts_at, expires_at, recurring_token))
        await db.commit()
        return cursor.lastrowid


async def deactivate_subscription(subscription_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE subscriptions SET is_active = 0 WHERE id = ?
        """, (subscription_id,))
        await db.commit()


async def get_expiring_subscriptions(days_before: int) -> list[dict]:
    """Get subscriptions expiring within N days that are still active."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM subscriptions
            WHERE is_active = 1
              AND expires_at <= datetime('now', '+' || ? || ' days')
              AND expires_at > datetime('now')
            ORDER BY expires_at ASC
        """, (days_before,))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_expired_subscriptions() -> list[dict]:
    """Get subscriptions that have expired but are still marked active."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM subscriptions
            WHERE is_active = 1
              AND expires_at <= datetime('now')
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def create_payment(user_id: int, order_id: str, amount: float) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO payments (user_id, order_id, amount, status)
            VALUES (?, ?, ?, 'pending')
        """, (user_id, order_id, amount))
        await db.commit()
        return cursor.lastrowid


async def update_payment_status(order_id: str, status: str, prodamus_payment_id: Optional[str] = None, recurring_token: Optional[str] = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE payments
            SET status = ?, prodamus_payment_id = COALESCE(?, prodamus_payment_id),
                recurring_token = COALESCE(?, recurring_token),
                updated_at = datetime('now')
            WHERE order_id = ?
        """, (status, prodamus_payment_id, recurring_token, order_id))
        await db.commit()


async def get_payment_by_order_id(order_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM payments WHERE order_id = ?", (order_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_bot_state(key: str) -> Optional[str]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM bot_state WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_bot_state(key: str, value: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO bot_state (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
        await db.commit()


async def update_subscription_recurring_token(subscription_id: int, token: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE subscriptions SET recurring_token = ? WHERE id = ?
        """, (token, subscription_id))
        await db.commit()
