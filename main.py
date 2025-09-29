import os
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_API_URL = os.getenv("AI_API_URL")
AI_API_KEY = os.getenv("AI_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Привет! Отправь мне фото для анализа.")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file.file_path}"
        
        img_data = requests.get(file_url).content

        headers = {}
        if AI_API_KEY:
            headers["Authorization"] = f"Bearer {AI_API_KEY}"

        # Отправляем фото в нейросеть
        response = requests.post(AI_API_URL, headers=headers, data=img_data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            # ⚠️ ЭТО ВАЖНО: замени эту строку, если знаешь структуру ответа
            answer = str(result)
        else:
            answer = f"Ошибка: {response.status_code}"

        await message.answer(answer)

    except Exception as e:
        await message.answer(f"Ошибка бота: {str(e)}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)