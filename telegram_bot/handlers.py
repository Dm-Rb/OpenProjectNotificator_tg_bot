from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from telegram_bot.messages import start_cmd_msg, set_login_cmd_msg, set_login_done_msg, generate_msg_with_notif, \
    set_login_error_msg, set_login_empty_msg, wipe_me_cmd_done, wipe_me_cmd_empty
from service.users import users
from service.open_project_service import open_prj_service
import re


router = Router()


class LoginState(StatesGroup):
    waiting_login = State()  # Waiting login


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    tg_user_id = message.chat.id
    if not users.cache_tg_id.get(tg_user_id, None):
        await message.answer(start_cmd_msg, parse_mode='HTML')
        await cmd_set_login(message, state)


@router.message(Command("set_login"))
async def cmd_set_login(message: Message, state: FSMContext):
    await message.answer(text=set_login_cmd_msg, parse_mode="HTML")
    await state.set_state(LoginState.waiting_login)


@router.message(LoginState.waiting_login)
async def set_login_process(message: Message, state: FSMContext):
    tg_user_id = message.chat.id
    user_login = message.text
    user_login = user_login.strip()
    try:
        all_users = await open_prj_service.get_all_users()
        if not all_users:
            await message.answer(set_login_error_msg, parse_mode='HTML')
            return
        if user_login not in all_users:
            await message.answer(set_login_empty_msg, parse_mode='HTML')
            return

        await users.add_new_user(user_login, tg_user_id)
        await message.answer(set_login_done_msg, parse_mode='HTML')
        await state.clear()
    except ValueError as ex:
        await message.answer(str(ex), parse_mode=None)


@router.message(Command("wipe_me"))
async def cmd_wipe_me(message: Message):
    tg_user_id = message.chat.id
    r = await users.delete_user(tg_user_id)
    if r:
        await message.answer(wipe_me_cmd_done)
    else:
        await message.answer(wipe_me_cmd_empty)


async def send_notifications(bot: Bot, preparing_data: dict):
    if not preparing_data['notify_users']:
        return
    for user_item in preparing_data['notify_users']:

        user_telegram_id = users.cache_login.get(user_item.get('name', ''), None)
        if not user_telegram_id:
            continue
        msg_text = generate_msg_with_notif(preparing_data)
        try:
            await bot.send_message(chat_id=user_telegram_id, text=msg_text, parse_mode='HTML')
        except TelegramBadRequest as e:
            if "can't parse entities" in str(e):
                # если не удалось распарсить HTML, применяем регулярку, которая вытирает все теги кроме b,i,a
                pattern = r'<(?!\/?(b|i|a)\b)[^>]+>'
                msg_text = re.sub(pattern, '', msg_text)
                msg_text = msg_text.replace('\n\n', '\n')
                await bot.send_message(chat_id=user_telegram_id, text=msg_text, parse_mode='HTML')
            else:
                raise e
        except Exception as _ex:
            await bot.send_message(chat_id=user_telegram_id, text=str(_ex), parse_mode=None)
