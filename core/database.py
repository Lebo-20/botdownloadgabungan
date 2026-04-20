import aiosqlite
import os
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Optimize for high concurrency (Anti-Lock)
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA busy_timeout=5000")
            await db.execute("PRAGMA synchronous=NORMAL")
            
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_admin BOOLEAN DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0,
                    expiry_at TIMESTAMP
                )
            """)

            # Migration: Add expiry_at if it doesn't exist
            try:
                await db.execute("ALTER TABLE users ADD COLUMN expiry_at TIMESTAMP")
            except: pass
            # Settings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            # FSub channels
            await db.execute("""
                CREATE TABLE IF NOT EXISTS fsub_channels (
                    channel_id INTEGER PRIMARY KEY,
                    channel_name TEXT,
                    invite_link TEXT
                )
            """)
            await db.commit()

    async def add_user(self, user_id: int, username: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                return [row[0] async for row in cursor]

    async def get_total_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def is_admin(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return bool(row[0]) if row else False

    async def set_admin(self, user_id: int, status: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET is_admin = ? WHERE user_id = ?", (1 if status else 0, user_id))
            await db.commit()

    async def add_fsub(self, channel_id: int, name: str, link: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO fsub_channels VALUES (?, ?, ?)", (channel_id, name, link))
            await db.commit()

    async def get_fsub_channels(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT channel_id, channel_name, invite_link FROM fsub_channels") as cursor:
                return [{"id": r[0], "name": r[1], "link": r[2]} async for r in cursor]

    async def update_setting(self, key: str, value: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, value))
            await db.commit()

    async def get_setting(self, key: str, default=None):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else default

    async def is_authorized(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT is_admin, expiry_at FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row: return False
                is_admin, expiry_at = row
                if is_admin: return True
                if expiry_at:
                    expiry = datetime.fromisoformat(expiry_at)
                    return expiry > datetime.now()
                return False

    async def add_authorized_user(self, user_id: int, duration_days: int):
        from datetime import timedelta
        expiry = datetime.now() + timedelta(days=duration_days)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, expiry_at) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET expiry_at = ?
            """, (user_id, expiry.isoformat(), expiry.isoformat()))
            await db.commit()

db = Database()
