from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from telegram_bot.messages import start_cmd_msg, set_login_cmd_msg, set_login_done_msg, generate_notif_msg, \
    set_login_error_msg, set_login_empty_msg, wipe_me_cmd_done, wipe_me_cmd_empty
from service.users import users
from service.open_project_service import open_prj_service
import re


"""Module with Telegram bot handlers"""

router = Router()


class LoginState(StatesGroup):
    waiting_login = State()  # Waiting login FSM


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    # Command /start in Telegram
    tg_user_id = message.chat.id
    if not users.cache_tg_id.get(tg_user_id, None):
        await message.answer(start_cmd_msg, parse_mode='HTML')
        await cmd_set_login(message, state)


@router.message(Command("set_login"))
async def cmd_set_login(message: Message, state: FSMContext):
    # Command /set_login in Telegram
    await message.answer(text=set_login_cmd_msg, parse_mode="HTML")
    await state.set_state(LoginState.waiting_login)


@router.message(LoginState.waiting_login)
async def set_login_process(message: Message, state: FSMContext):
    # State for /set_login command
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
    # Command /wipe_me in Telegram
    tg_user_id = message.chat.id
    r = await users.delete_user(tg_user_id)
    if r:
        await message.answer(wipe_me_cmd_done)
    else:
        await message.answer(wipe_me_cmd_empty)


async def send_notifications(bot: Bot, prepared_data: dict):
    """
    The handler receives a dictionary <preparing_data> containing details about a task update on your task board,
    as well as a list of Telegram users who will receive notifications.
    A text message is then generated based on the <preparing_data> and distributed to the users.
    """

    if not prepared_data['notify_users']:
        return
    for user_item in prepared_data['notify_users']:

        user_telegram_id = users.cache_login.get(user_item.get('name', ''), None)
        if not user_telegram_id:
            continue
        msg_text = generate_notif_msg(prepared_data)
        try:
            await bot.send_message(chat_id=user_telegram_id, text=msg_text, parse_mode='HTML')
        except TelegramBadRequest as e:
            if "can't parse entities" in str(e):
                # If an unexpected error occurs while formatting the message due to the <parse_mode='HTML'> option,
                # apply a regular expression that removes all tags except <b>, <i>, <a>
                pattern = r'<(?!\/?(b|i|a)\b)[^>]+>'
                msg_text = re.sub(pattern, '', msg_text)
                msg_text = msg_text.replace('\n\n', '\n')
                await bot.send_message(chat_id=user_telegram_id, text=msg_text, parse_mode='HTML')
            else:
                raise e
        except Exception as _ex:
            await bot.send_message(chat_id=user_telegram_id, text=str(_ex), parse_mode=None)
