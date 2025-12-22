from config import config_

"""
Модуль содержит текст ответов и функцию генерации текста сообщения бота
"""

start_cmd_msg = f'🔔 Бот уведомляет об измнения, связанных с вашим аккаунтом на <b><a href="{config_.DOMAIN}">доске задач</a></b>'
set_login_cmd_msg = f'👇🏻 Отправьте боту ваш действующий логин <a href="{config_.DOMAIN}">portal.remzona.by</a>'
set_login_done_msg = "Логин установлен, отправка уведомлений включена 👍🏻\n/set_login - сменить текущий логин\n/wipe_me - удалить из бота все связанные со мною данные"
set_login_error_msg = "❗️ Бот не смог подключится к серверу для проверки введённых вам данных. Пробуйте позже или обратитесь к администратору"
set_login_empty_msg = "❗️ Отправленный вами логин отсутствует в списке существующих учётных записей. Проверьте отправленное на предмет опечаток и попробуйте ещё раз. Если это сообщение повторяется - обратитесь к администатору"
wipe_me_cmd_done = "Все данные, связанные с вами, были удалены ✅"
wipe_me_cmd_empty = "У бота отсутствую какие либо данные связанные с вами, удалять нечего❕"


def generate_notif_msg(preparing_data):
    status_colors = {'Новый': '🟢', 'В работе': '🔵', 'Отменено': '🔴', 'Закрыто': '⚪️'}
    priority_colors = {'Низкий': '⚪️', 'Нормальный': '🔵', 'Высокий': '🟡', 'Срочно': '🟣'}
    text = f"{preparing_data['update_type']}\n"
    text += f"<b>Проект:</b> {preparing_data['project'] if preparing_data['project'] else '-'}\n"
    text += f"<b>Задача:</b> <a href='{preparing_data['link']}'>{preparing_data['subject'] if preparing_data['subject'] else '-'}</a>\n"
    # text += f"Тип: {preparing_data['type'] if preparing_data['type'] else '-'}\n"
    # text += f"<b>Статус:</b> {status_colors.get(preparing_data.get('status', None), '')} {preparing_data['status'] if preparing_data['status'] else '-'}\n"
    # text += f"<b>Приоритет:</b> {priority_colors.get(preparing_data.get('priority', None), '')} {preparing_data['priority'] if preparing_data['priority'] else '-'}\n"
    # text += f"<b>Автор:</b> {preparing_data['author']['name']}\n"
    if preparing_data.get('performer'):
        text += f"<b>Исполнитель:</b> {preparing_data['performer']['name'] if preparing_data['performer']['name'] else ''}\n"
    if preparing_data.get('assignee'):
        text += f"<b>Назначенный:</b> {preparing_data['assignee']['name']}\n"
    # if preparing_data['responsible']:
    #     text += f"<b>Ответственный:</b> {preparing_data['responsible']['name']}\n"
    if "Тикеты" in preparing_data.get('project', ''):
        text += f"<b>Описание задачи:</b>\n{preparing_data['description']}"
    if preparing_data.get('invoice', None):
        text += f"<b>Сумма НДС:</b> {preparing_data['invoice']}\n"
    if preparing_data.get('comment', None):
        text += f"\n<b>Комментарий:</b>\n{preparing_data['comment']}"

    return text
