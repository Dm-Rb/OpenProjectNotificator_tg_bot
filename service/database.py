import aiosqlite
import sqlite3
from config import config_
import os


class Database:
    """
    Class for working with the SQLite file database. The database file contains pairs:
        - login is user's login on the Open Project task board
        - user_tg_id is user's Telegram identifier
    The data.db file will be located at config_.DIR_PATH
    """

    def __init__(self):

        self.db_path = os.path.join(config_.DIR_PATH, "data.db")
        self._ensure_db()

    def _ensure_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f'''
                CREATE TABLE IF NOT EXISTS users (
                    login TEXT,
                    user_tg_id INTEGER)
                '''
            )
            conn.commit()

    async def add_user(self, login: str, user_tg_id: int):
        """Add new row or update exist row"""
        async with aiosqlite.connect(self.db_path) as db:
            # user_tg_id exist in table
            async with db.execute("SELECT 1 FROM users WHERE user_tg_id = ?", (user_tg_id,)) as cursor:
                exists = await cursor.fetchone()
            if exists:
                # update if exists
                await db.execute(
                    "UPDATE users SET login = ? WHERE user_tg_id = ?",
                    (login, user_tg_id)
                )
            else:
                # insert new row if not exists
                await db.execute(
                    "INSERT INTO users (login, user_tg_id) VALUES (?, ?)",
                    (login, user_tg_id)
                )
            await db.commit()

    async def delete_user(self, user_tg_id: int):
        """Delete row """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("DELETE FROM users WHERE user_tg_id = ?", (user_tg_id,)) as cursor:
                await db.commit()
                # number of deleted rows for verification
                return cursor.rowcount

    def get_all_users(self):
        """Get all rows"""
        with sqlite3.connect(self.db_path) as conn:
            r = conn.execute("SELECT login, user_tg_id FROM users").fetchall()
            return r


database = Database()
