import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.sqlite"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 3,
                total_packs INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS sticker_packs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                pack_name TEXT,
                pack_title TEXT,
                sticker_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

async def add_user(user_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
            (user_id, username)
        )
        await db.commit()

async def decrease_balance(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE users SET balance = balance - 1, total_packs = total_packs + 1 WHERE user_id = ? AND balance > 0',
            (user_id,)
        )
        await db.commit()

async def get_user_pack_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT COUNT(*) FROM sticker_packs WHERE user_id = ?', (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def save_sticker_pack(user_id: int, pack_name: str, pack_title: str, sticker_count: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO sticker_packs (user_id, pack_name, pack_title, sticker_count) VALUES (?, ?, ?, ?)',
            (user_id, pack_name, pack_title, sticker_count)
        )
        await db.commit()
