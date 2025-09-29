import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from aiohttp import web
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
NEURAL_API_KEY = os.getenv('NEURAL_API_KEY')
NEURAL_API_URL = 'https://api.neural-network.com/process'  # Замените на реальный URL API нейросети
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Например, https://your-service-name.onrender.com

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text('Привет! Я бот для обработки изображений с помощью нейросети. '
                                   'Отправь мне фото, и я обработаю его по заданному промту!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text('Отправь мне изображение, и я обработаю его с помощью нейросети. '
                                   'Используй /start для начала и /help для справки.')

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик входящих изображений"""
    if update.message.photo:
        # Получаем файл самого высокого качества
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = file.file_path

        # Загружаем изображение
        try:
            response = requests.get(file_path)
            response.raise_for_status()
            image_data = response.content

            # Подготавливаем данные для API нейросети (заглушка для промта)
            prompt = "Пока заглушка, замените на ваш промт"  # Замените на реальный промт позже
            headers = {
                'Authorization': f'Bearer {NEURAL_API_KEY}',
                'Content-Type': 'application/json'
            }
            payload = {
                'image': image_data.hex(),  # Предполагаем, что API принимает изображение в формате hex
                'prompt': prompt
            }

            # Отправляем запрос к API нейросети
            neural_response = requests.post(NEURAL_API_URL, json=payload, headers=headers)
            neural_response.raise_for_status()
            result = neural_response.json()

            # Предполагаем, что API возвращает обработанное изображение или текст
            if 'processed_image' in result:
                import base64
                processed_image = base64.b64decode(result['processed_image'])
                await update.message.reply_photo(photo=processed_image)
            else:
                await update.message.reply_text(result.get('text', 'Обработка завершена, но результат неясен.'))
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения: {e}")
            await update.message.reply_text('Произошла ошибка при обработке изображения. Попробуйте снова.')
    else:
        await update.message.reply_text('Пожалуйста, отправьте изображение.')

async def webhook(request):
    """Обработчик вебхуков для Render"""
    try:
        update = Update.de_json(await request.json(), app.bot)
        await app.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Ошибка в вебхуке: {e}")
        return web.Response(status=500)

async def init_webhook():
    """Инициализация вебхука"""
    global app
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Настройка вебхука
    if WEBHOOK_URL:
        await app.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
        logger.info(f"Вебхук установлен на {WEBHOOK_URL}/{BOT_TOKEN}")
    else:
        logger.error("WEBHOOK_URL не установлен")
        raise ValueError("WEBHOOK_URL не установлен")

def main():
    """Основная функция для запуска бота"""
    if not BOT_TOKEN or not NEURAL_API_KEY or not WEBHOOK_URL:
        logger.error("BOT_TOKEN, NEURAL_API_KEY или WEBHOOK_URL не установлены")
        return

    # Инициализация aiohttp сервера
    web_app = web.Application()
    web_app.router.add_post(f"/{BOT_TOKEN}", webhook)
    
    # Запуск приложения на порту, указанном Render
    port = int(os.getenv('PORT', 10000))  # Render по умолчанию использует порт 10000
    web.run_app(web_app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Инициализация вебхука при старте
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_webhook())
    main()
