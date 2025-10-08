
start_cmd_msg = "Добро пожаловать нахуй!"
set_login_cmd_msg = 'Отправьте боту ваш логин с https://portal.remzona.by'
set_login_done_msg = "Логин установлен. Теперь вы будете получать уведомления, связанные с вашим аккаунтом на https://portal.remzona.by"


def generate_msg_with_notif(preparing_data):
    text = f"{preparing_data['update_type']}\n"
    text += f"Задача: {preparing_data['subject'] if preparing_data['subject'] else '-'}\n"

    return text
    
