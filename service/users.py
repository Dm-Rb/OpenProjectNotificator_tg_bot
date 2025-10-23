from service.database import database


class Users:
    """
    Service layer class for database operations. Wrapper for an instance of the <Database> class
    """

    def __init__(self):
        # cash
        self.cache_login = {}  # {login: tg_id}
        self.cache_tg_id = {}  # {tg_id: login}

        # Populate with values from the database
        db_answer = database.get_all_users()
        if db_answer:
            self.cache_login = {i[0]: i[1] for i in db_answer}
            self.cache_tg_id = {i[1]: i[0] for i in db_answer}

    async def add_new_user(self, user_login: str, user_tg_id: str):
        user_login = user_login.strip()
        await database.add_user(user_login, user_tg_id)
        self.cache_login[user_login] = user_tg_id
        self.cache_tg_id[user_tg_id] = user_login

    async def delete_user(self, user_tg_id: int):
        user_login = self.cache_tg_id.pop(user_tg_id, None)
        if user_login:
            self.cache_login.pop(user_login, None)
        count_rows = await database.delete_user(user_tg_id)
        if count_rows:
            return True


users = Users()
