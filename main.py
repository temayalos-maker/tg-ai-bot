import os
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiohttp import web

# === Настройки из переменных окружения ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_API_URL = os.getenv("AI_API_URL")
AI_API_KEY = os.getenv("AI_API_KEY")

# Вебхук-путь и URL
WEBHOOK_PATH = f"/webhook/{TELEGRAM_BOT_TOKEN}"
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

# Логирование
logging.basicConfig(level=logging.INFO)

# Создаём бота и устанавливаем его как текущий (обязательно для aiogram v2)
bot = Bot(token=TELEGRAM_BOT_TOKEN)
Bot.set_current(bot)
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Привет! Отправь мне фото еды для анализа.")

# Обработчик фото
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    try:
        # Получаем самое большое фото
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file.file_path}"
        img_data = requests.get(file_url).content

        # Заголовки для API нейросети
        headers = {}
        if AI_API_KEY:
            headers["Authorization"] = f"Bearer {AI_API_KEY}"

        # Отправляем фото в нейросеть
        response = requests.post(AI_API_URL, headers=headers, data=img_data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            answer = str(result)
        else:
            answer = f"Ошибка API ({response.status_code}): {response.text[:200]}"
        await message.answer(answer)

    except Exception as e:
        await message.answer(f"Ошибка бота: {str(e)}")

# Обработчик вебхука
async def webhook_handler(request):
    if request.path == WEBHOOK_PATH:
        update = await request.json()
        await dp.process_update(types.Update(**update))
        return web.Response()
    return web.Response(status=403)

# Установка вебхука при старте
async def on_startup(app):
    logging.info(f"Устанавливаем вебхук: {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)

# Очистка при завершении
async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.close()

# Создаём aiohttp-приложение
app = web.Application()
app.router.add_post(WEBHOOK_PATH, webhook_handler)
app.on_startup.append(on_startup)
app.on_cleanup.append(on_shutdown)

# Запуск сервера
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
