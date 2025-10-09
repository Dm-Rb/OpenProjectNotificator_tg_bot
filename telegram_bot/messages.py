
start_cmd_msg = '🔔 Бот уведомляет об измнения, связанных с вашим аккаунтом на <b><a href="https://portal.remzona.by">доске задач</a></b>'
set_login_cmd_msg = '👇🏻 Отправьте боту ваш действующий логин <a href="https://portal.remzona.by">portal.remzona.by</a>'
set_login_done_msg = "Логин установлен, отправка уведомлений включена 👍🏻 "


def generate_msg_with_notif(preparing_data):
    status_colors = {'Новый':'🟢', 'В работе': '🔵', 'Отменено': '🔴', 'Закрыто': '⚪️'}
    priority_colors = {'Низкий':'⚪️', 'Нормальный': '🔵', 'Высокий': '🟡', 'Срочно': '🟣'}
    text = f"{preparing_data['update_type']}\n"
    text += f"<b>Задача:</b> <a href='{preparing_data['link']}'>{preparing_data['subject'] if preparing_data['subject'] else '-'}</a>\n"
    # text += f"Тип: {preparing_data['type'] if preparing_data['type'] else '-'}\n"
    text += f"<b>Проект:</b> {preparing_data['project'] if preparing_data['project'] else '-'}\n"
    text += f"<b>Статус:</b> {status_colors.get(preparing_data.get('status', None), '')} {preparing_data['status'] if preparing_data['status'] else '-'}\n"
    text += f"<b>Приоритет:</b> {priority_colors.get(preparing_data.get('priority', None), '')} {preparing_data['priority'] if preparing_data['priority'] else '-'}\n"
    text += f"\n{preparing_data['description']}"

    return text
    
