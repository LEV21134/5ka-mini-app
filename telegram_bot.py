

import os
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, token: str, webapp_url: str):
        self.token = token
        self.webapp_url = webapp_url
        self.application = Application.builder().token(token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("shop", self.shop_command))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        webapp = WebAppInfo(url=self.webapp_url)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Открыть магазин", web_app=webapp)]
        ])

        welcome_text = f"""
🎉 Добро пожаловать в 5ka Mini App, {user.first_name}!

🛍️ Что можно делать:
- Найти ближайшие магазины Пятёрочка
- Просматривать каталог товаров  
- Добавлять товары в корзину
- Оформлять заказы

Нажмите кнопку ниже, чтобы начать покупки!
        """

        await update.message.reply_text(welcome_text, reply_markup=keyboard)

    async def shop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        webapp = WebAppInfo(url=self.webapp_url)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Перейти в магазин", web_app=webapp)]
        ])

        await update.message.reply_text(
            "🛍️ Нажмите кнопку для перехода в магазин:",
            reply_markup=keyboard
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📖 Помощь по использованию 5ka Mini App

**Команды:**
/start - Запуск бота и приветствие
/shop - Быстрый доступ к магазину  
/help - Эта справка

**Как пользоваться:**
1. Нажмите "Открыть магазин"
2. Введите ваш адрес
3. Выберите ближайший магазин
4. Добавляйте товары в корзину
5. Оформите заказ

По вопросам пишите разработчику.
        """
        await update.message.reply_text(help_text)

    def run(self):
        logger.info("🤖 Запуск Telegram бота...")
        logger.info(f"📱 Webapp URL: {self.webapp_url}")
        self.application.run_polling()


if __name__ == "__main__":
    # Получаем переменные окружения
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7700180865:AAGbjhypgopYF69osFH9QDFhWQsyClmYpSc")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://skidkagram.su")

    if BOT_TOKEN == "your_bot_token_here" or not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не установлен!")
        print("")
        print("📝 Для получения токена:")
        print("1. Найдите @BotFather в Telegram")
        print("2. Отправьте /newbot")
        print("3. Следуйте инструкциям")
        print("4. Скопируйте токен и добавьте в .env файл")
        print("")
        print("💡 Пример .env файла:")
        print("TELEGRAM_BOT_TOKEN=1234567890:ABCDEF...")
        print("WEBAPP_URL=http://localhost:8000")
        exit(1)

    try:
        bot = TelegramBot(BOT_TOKEN, WEBAPP_URL)
        bot.run()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        print("💡 Проверьте правильность токена в .env файле")
