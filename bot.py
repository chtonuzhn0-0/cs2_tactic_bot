# ============================================================
# CS2 Tactics Bot — финальная версия (иконки-кнопки)
# ============================================================

import asyncio
import json
import logging
import os
import random
from pathlib import Path

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ---------- 1. Токен ----------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Токен не найден! Проверь файл .env")

# ---------- 2. Бот и диспетчер ----------
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML"),
)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# ---------- 3. Пути ----------
BASE_DIR = Path(__file__).parent
TACTICS_FILE = BASE_DIR / "tactics.json"

# ---------- 4. Загрузка тактик ----------
def load_tactics() -> dict:
    with open(TACTICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

TACTICS = load_tactics()

# ---------- 5. Названия ----------
MAP_NAMES = {
    "mirage": "Mirage", "inferno": "Inferno", "dust2": "Dust 2",
    "anubis": "Anubis", "nuke": "Nuke", "ancient": "Ancient", "vertigo": "Vertigo",
}
SIDE_NAMES = {"t": "T", "ct": "CT"}
BUY_NAMES = {
    "pistol": "Пистолетка", "eco": "Эко",
    "force": "Форс", "full": "Фулл-бай",
}

# ---------- 6. Клавиатуры ----------

def kb_maps() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for map_key in TACTICS.keys():
        builder.button(
            text=MAP_NAMES.get(map_key, map_key),
            callback_data=f"map:{map_key}",
        )
    builder.adjust(2)
    return builder.as_markup()

def kb_sides(map_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for side_key in TACTICS[map_key].keys():
        builder.button(
            text=SIDE_NAMES.get(side_key, side_key),
            callback_data=f"side:{map_key}:{side_key}",
        )
    builder.button(text="⬅ Назад", callback_data="back:maps")
    builder.adjust(2)
    return builder.as_markup()

def kb_buys(map_key: str, side_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for buy_key in TACTICS[map_key][side_key].keys():
        count = len(TACTICS[map_key][side_key][buy_key])
        builder.button(
            text=f"{BUY_NAMES.get(buy_key, buy_key)} ({count})",
            callback_data=f"buy:{map_key}:{side_key}:{buy_key}:0",
        )
    builder.button(text="⬅ Назад", callback_data=f"back:sides:{map_key}")
    builder.adjust(2)
    return builder.as_markup()

def kb_after_tactic(map_key: str, side_key: str, buy_key: str, index: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total = len(TACTICS[map_key][side_key][buy_key])

    if total > 1:
        prev_index = (index - 1) % total
        next_index = (index + 1) % total
        builder.button(
            text="⬅",
            callback_data=f"buy:{map_key}:{side_key}:{buy_key}:{prev_index}",
        )
        builder.button(
            text="➡",
            callback_data=f"buy:{map_key}:{side_key}:{buy_key}:{next_index}",
        )
        builder.button(
            text="🎲",
            callback_data=f"random:{map_key}:{side_key}:{buy_key}:{index}",
        )

    builder.button(
        text="🔁 Другой бай",
        callback_data=f"back:buys:{map_key}:{side_key}",
    )
    builder.button(text="🗺 Другая карта", callback_data="back:maps")
    builder.adjust(3, 2)
    return builder.as_markup()

# ---------- 7. Форматирование ----------

def format_tactic(map_key: str, side_key: str, buy_key: str, index: int) -> str:
    tactics = TACTICS[map_key][side_key][buy_key]
    tactic = tactics[index]

    total = len(tactics)
    counter = f" ({index + 1}/{total})" if total > 1 else ""

    source_line = ""
    if tactic.get("source"):
        source_line = f"\n\n🏷 {tactic['source']}"

    divider = "━━━━━━━━━━━━━━━━━━━━"

    return (
        f"🎯 <b>{MAP_NAMES.get(map_key, map_key)} — "
        f"{SIDE_NAMES.get(side_key, side_key)} — "
        f"{BUY_NAMES.get(buy_key, buy_key)}</b>{counter}\n\n"
        f"{divider}\n"
        f"👥 <b>{tactic['split']}</b>\n"
        f"{divider}\n\n"
        f"📌 <b>{tactic['name']}</b>\n\n"
        f"🧨 {tactic['utility']}\n\n"
        f"💡 {tactic['idea']}"
        f"{source_line}"
    )

# ---------- 8. Экран баёв ----------

def buys_screen(map_key: str, side_key: str) -> tuple[str, InlineKeyboardMarkup]:
    text = (
        f"Карта: <b>{MAP_NAMES.get(map_key, map_key)}</b>\n"
        f"Сторона: <b>{SIDE_NAMES.get(side_key, side_key)}</b>\n"
        f"Выбери бай:"
    )
    return text, kb_buys(map_key, side_key)

# ---------- 9. Команды ----------

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для тактик CS2. 🎯\n\n"
        "Выбери карту, сторону и бай — я выдам тактику.\n\n"
        "Команда: /tactic — открыть меню."
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Команды:\n"
        "/start — приветствие\n"
        "/tactic — выбрать тактику\n"
        "/help — эта справка"
    )

@dp.message(Command("tactic"))
async def cmd_tactic(message: types.Message):
    await message.answer("Выбери карту:", reply_markup=kb_maps())

# ---------- 10. Обработчики ----------

@dp.callback_query(F.data.startswith("map:"))
async def on_map(callback: types.CallbackQuery):
    map_key = callback.data.split(":")[1]
    await callback.message.edit_text(
        f"Карта: <b>{MAP_NAMES.get(map_key, map_key)}</b>\nВыбери сторону:",
        reply_markup=kb_sides(map_key),
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("side:"))
async def on_side(callback: types.CallbackQuery):
    _, map_key, side_key = callback.data.split(":")
    text, kb = buys_screen(map_key, side_key)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("buy:"))
async def on_buy(callback: types.CallbackQuery):
    _, map_key, side_key, buy_key, index = callback.data.split(":")
    index = int(index)
    text = format_tactic(map_key, side_key, buy_key, index)
    await callback.message.edit_text(
        text,
        reply_markup=kb_after_tactic(map_key, side_key, buy_key, index),
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("random:"))
async def on_random(callback: types.CallbackQuery):
    _, map_key, side_key, buy_key, current_index = callback.data.split(":")
    current_index = int(current_index)

    tactics = TACTICS[map_key][side_key][buy_key]
    total = len(tactics)

    if total > 1:
        candidates = [i for i in range(total) if i != current_index]
        new_index = random.choice(candidates)
    else:
        new_index = current_index

    text = format_tactic(map_key, side_key, buy_key, new_index)
    await callback.message.edit_text(
        text,
        reply_markup=kb_after_tactic(map_key, side_key, buy_key, new_index),
    )
    await callback.answer("🎲 Случайная тактика!")

# ---------- 11. Назад ----------

@dp.callback_query(F.data == "back:maps")
async def back_to_maps(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери карту:", reply_markup=kb_maps())
    await callback.answer()

@dp.callback_query(F.data.startswith("back:sides:"))
async def back_to_sides(callback: types.CallbackQuery):
    map_key = callback.data.split(":")[2]
    await callback.message.edit_text(
        f"Карта: <b>{MAP_NAMES.get(map_key, map_key)}</b>\nВыбери сторону:",
        reply_markup=kb_sides(map_key),
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("back:buys:"))
async def back_to_buys(callback: types.CallbackQuery):
    _, _, map_key, side_key = callback.data.split(":")
    text, kb = buys_screen(map_key, side_key)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

# ---------- 12. Запуск ----------

async def main():
    print("Бот запущен! Иди в Telegram и напиши /tactic")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())