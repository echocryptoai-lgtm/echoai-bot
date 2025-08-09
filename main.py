import logging
import json
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from langdetect import detect

API_TOKEN = 'os.getenv("API_KEY")'
GROQ_API_KEY = 'os.getenv("GROQ_API_KEY")'
GROQ_MODEL = 'mixtral-8x7b-32768'
ADMIN_ID = 7977349936

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

conversation_history = {}

# 📌 START
@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.answer("👋 Cześć! Jestem EchoAi – Twój asystent oparty na Groq. Zadaj mi pytanie!")

# 📌 FAQ
@dp.message_handler(commands=['faq'])
async def faq(message: Message):
    await message.answer("❓ Najczęstsze pytania:\n- Jak działa bot?\n- Czy mogę zmienić język?\n- Czy pamięta rozmowę?")

# 📌 LANGUAGE
@dp.message_handler(commands=['language'])
async def language(message: Message):
    lang = detect(message.text or "Hello")
    await message.answer(f"🌍 Wykryty język: {lang}")

# 📌 RESET (dla użytkownika)
@dp.message_handler(commands=['reset'])
async def reset(message: Message):
    user_id = str(message.from_user.id)
    conversation_history[user_id] = []
    await message.answer("🔄 Twoja rozmowa została zresetowana.")

# 📌 ADMIN RESET (globalny)
@dp.message_handler(commands=['adminreset'])
async def admin_reset(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Nie masz uprawnień do tej komendy.")
        return
    conversation_history.clear()
    await message.answer("✅ EchoAi został całkowicie zresetowany.")

# 📌 STATS
@dp.message_handler(commands=['stats'])
async def stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Brak dostępu.")
        return
    users = len(conversation_history)
    await message.answer(f"📊 Liczba aktywnych użytkowników: {users}")

# 📌 BROADCAST
@dp.message_handler(commands=['broadcast'])
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ Brak dostępu.")
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("✉️ Podaj treść wiadomości po komendzie.")
        return
    for uid in conversation_history.keys():
        try:
            await bot.send_message(int(uid), f"📢 Wiadomość od EchoAi:\n{text}")
        except:
            continue
    await message.answer("✅ Wiadomość rozesłana.")

# 📌 Główna obsługa wiadomości
@dp.message_handler()
async def handle_message(message: Message):
    user_id = str(message.from_user.id)
    user_text = message.text

    lang = detect(user_text)
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({"role": "user", "content": user_text})

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": conversation_history[user_id]
        }
        async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload) as resp:
            data = await resp.json()
            reply = data["choices"][0]["message"]["content"]
            conversation_history[user_id].append({"role": "assistant", "content": reply})
            await message.answer(reply)

# 📌 Uruchomienie
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
