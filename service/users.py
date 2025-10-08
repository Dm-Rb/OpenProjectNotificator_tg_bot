from service.database import database


class Users:

    def __init__(self):

        self.cache_login = {}
        self.cache_tg_id = {}

        db_answer = database.get_all_users()
        if db_answer:
            self.cache_login = {i[0]: i[1] for i in db_answer}
            self.cache_tg_id = {i[1]: i[0] for i in db_answer}

    async def add_new_user(self, user_login: str, user_tg_id:str):
        await database.add_user(user_login, user_tg_id)
        self.cache_login[user_login] = user_tg_id
        self.cache_tg_id[user_tg_id] = user_login


users = Users()
