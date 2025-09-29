# main.py
import os
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

# === Настройки ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_API_URL = os.getenv("AI_API_URL")
AI_API_KEY = os.getenv("AI_API_KEY")

# Вебхук-путь и URL
WEBHOOK_PATH = f"/webhook/{TELEGRAM_BOT_TOKEN}"
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

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

        response = requests.post(AI_API_URL, headers=headers, data=img_data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            answer = str(result)
        else:
            answer = f"Ошибка API ({response.status_code}): {response.text[:200]}"

        await message.answer(answer)

    except Exception as e:
        await message.answer(f"Ошибка бота: {str(e)}")

# --- Вебхук ---
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Вебхук установлен: {WEBHOOK_URL}")

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.close()

async def webhook_handler(request):
    if request.path == WEBHOOK_PATH:
        update = await request.json()
        await dp.process_update(types.Update(**update))
        return web.Response()
    return web.Response(status=403)

# --- Запуск ---
if __name__ == "__main__":
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_shutdown)

    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
