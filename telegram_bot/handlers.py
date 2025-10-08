from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from telegram_bot.messages import start_cmd_msg, set_login_cmd_msg, set_login_done_msg, generate_msg_with_notif
from service.users import users


router = Router()


class LoginState(StatesGroup):
    waiting_login = State()  # Waiting login


@router.message(Command("start"))
async def cmd_set_logint(message: Message, state: FSMContext):
    tg_user_id = message.chat.id
    if not users.cache_tg_id.get(tg_user_id, None):
        await message.answer(start_cmd_msg, parse_mode='HTML')
        await cmd_set_logint(message, state)


@router.message(Command("set_login"))
async def cmd_set_logint(message: Message, state: FSMContext):
    await message.answer(text=set_login_cmd_msg, parse_mode="HTML")
    await state.set_state(LoginState.waiting_login)


@router.message(LoginState.waiting_login)
async def set_logint(message: Message, state: FSMContext):
    tg_user_id = message.chat.id
    user_login = message.text
    await state.clear()
    await users.add_new_user(user_login, tg_user_id)
    await message.answer(set_login_done_msg, parse_mode='HTML')


# async def send_notification(bot: Bot, user_id: int, msg_text: str):
#     await bot.send_message(chat_id=user_id, text=msg_text, parse_mode='HTML')


async def send_notifications(bot: Bot, preparing_data: dict):
    if not preparing_data['notify_users']:
        return
    for user_item in preparing_data['notify_users']:

        user_telegram_id = users.cache_login[user_item['name']]
        msg_text = generate_msg_with_notif(preparing_data)
        await bot.send_message(chat_id=user_telegram_id, text=msg_text, parse_mode='HTML')




