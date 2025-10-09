
start_cmd_msg = '🔔 Бот уведомляет об измнения, связанных с вашим аккаунтом на <b><a href="https://portal.remzona.by">доске задач</a></b>'
set_login_cmd_msg = '👇🏻 Отправьте боту ваш действующий логин <a href="https://portal.remzona.by">portal.remzona.by</a>'
set_login_done_msg = "Логин установлен, отправка уведомлений включена 👍🏻 "


def generate_msg_with_notif(preparing_data):
    text = f"{preparing_data['update_type']}\n"
    text += f"Задача: <a href='{preparing_data['link']}'>{preparing_data['subject'] if preparing_data['subject'] else '-'}</a>\n"
    text += f"Тип: {preparing_data['type'] if preparing_data['type'] else '-'}\n"
    text += f"Проект: {preparing_data['project'] if preparing_data['project'] else '-'}\n"
    text += f"Статус: 🟣 {preparing_data['status'] if preparing_data['status'] else '-'}\n"
    text += f"Приоритет: {preparing_data['priority'] if preparing_data['priority'] else '-'}\n"

    return text
    
