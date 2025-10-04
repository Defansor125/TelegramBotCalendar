import asyncio
import json
import logging
import os
import re
from typing import Any
from gcsa.event import Event
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (Message, CallbackQuery, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import eventsApi as cd  # твой модуль ниже
TOKEN = os.environ["TOKEN"]



bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()


class CreateEvent(StatesGroup):
    waiting_json = State()


def main_menu_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="➕ Добавить событие", callback_data="add"))
    return kb


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Главное меню",
        reply_markup=main_menu_kb().as_markup()
    )


@router.callback_query(F.data == "add")
async def on_add_click(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer() 
    await state.set_state(CreateEvent.waiting_json)

    example = (
        "{\n"
        '  "summary": "Standup",\n'
        '  "description": "Daily sync",\n'
        '  "start": "2025-03-05T09:00:00+01:00",\n'
        '  "end":   "2025-03-05T09:15:00+01:00",\n'
        '  "timezone": "Europe/Vienna",\n'
        '  "all_day": false\n'
        "}"
    )

    await callback.message.answer(
        "Ок, пришли JSON для события.\n"
        "Минимум: <code>summary</code> и <code>start/end</code> (ISO-8601).\n\n"
        f"<b>Пример</b>:\n<pre>{example}</pre>\n"
        "Можно прислать и all-day:\n"
        "<pre>{\n"
        '  "summary": "Conference day 1",\n'
        '  "start": "2025-03-10",\n'
        '  "end":   "2025-03-11",\n'
        '  "all_day": true\n'
        "}</pre>"
    )


@router.message(CreateEvent.waiting_json, F.text)
async def on_json_received(message: Message, state: FSMContext) -> None:
    raw = message.text
    try:
        data = json.loads(raw) 
    except json.JSONDecodeError:
        await message.answer("Неправильный JSON. Пришли объект или массив объектов.")
        return

    created, errors = cd.create_events_from_payload(data)

    parts = []
    if created:
        parts.append(f"✅ Создано событий: {created}")
    if errors:
        parts.append("⚠️ Ошибки:\n" + "\n".join(errors))
    if not parts:
        parts.append("Ничего не создано.")

    await message.answer("\n\n".join(parts), reply_markup=main_menu_kb().as_markup())
    await state.clear()


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu_kb().as_markup())


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
