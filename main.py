import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.filters import CommandStart

import os
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

conn = sqlite3.connect('members.db')
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS member_counts (user_id INTEGER PRIMARY KEY, count INTEGER)")
conn.commit()

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("👋 أهلاً بيك في بوت عداد الإضافات!")

@dp.message(F.new_chat_members)
async def new_member_handler(message: Message):
    adder_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO member_counts (user_id, count) VALUES (?, 0)", (adder_id,))
    cursor.execute("UPDATE member_counts SET count = count + ? WHERE user_id = ?", (len(message.new_chat_members), adder_id))
    conn.commit()

    cursor.execute("SELECT count FROM member_counts WHERE user_id = ?", (adder_id,))
    count = cursor.fetchone()[0]
    await message.answer(f"👤 <b>{message.from_user.full_name}</b> ضاف <b>{count}</b> عضو 🔥")

    if count % 100 == 0 and adder_id != OWNER_ID:
        await bot.send_message(OWNER_ID, f"🎉 العضو <b>{message.from_user.full_name}</b> وصل لـ <b>{count}</b> إضافة!")

@dp.message(F.text == "/top")
async def top_members(message: Message):
    cursor.execute("SELECT user_id, count FROM member_counts ORDER BY count DESC LIMIT 5")
    top = cursor.fetchall()
    response = "🏆 <b>أفضل 5 أعضاء حسب الإضافات:</b>\n\n"
    for i, (uid, cnt) in enumerate(top, start=1):
        response += f"{i}. <a href='tg://user?id={uid}'>عضو</a> - {cnt} عضو\n"
    await message.answer(response)

@dp.message(F.text == "/myadds")
async def my_adds_handler(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT count FROM member_counts WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    count = result[0] if result else 0
    await message.answer(f"📊 عدد الإضافات الخاصة بك: <b>{count}</b>", parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())