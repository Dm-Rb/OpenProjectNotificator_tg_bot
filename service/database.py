import aiosqlite
import sqlite3
from config import config_
import os


class Database:
    """
    Класс для работы с файловой базой данныъ sqlite. Файл базы данных содержит пару:
    login - логин пользователя на таскборде Open Project
    user_tg_id - идентификатор пользователя телеграм
    """

    def __init__(self, db_path: str = "data.db"):

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
        """Добавить пару"""

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
        """Удалить пару"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("DELETE FROM users WHERE user_tg_id = ?", (user_tg_id,)) as cursor:
                await db.commit()
                # количество удаленных строк для проверки
                return cursor.rowcount

    def get_all_users(self):
        """Выбрать всё"""
        with sqlite3.connect(self.db_path) as conn:
            r = conn.execute("SELECT login, user_tg_id FROM users").fetchall()
            return r

    async def get_user_by_tg_id(self, user_tg_id: int):
        """Получить login по его user_tg_id"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_tg_id FROM users WHERE user_tg_id = ?",
                (user_tg_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None


database = Database()
