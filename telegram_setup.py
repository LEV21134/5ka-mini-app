# telegram_bot.py - Настройка Telegram бота для Mini App

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
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("shop", self.shop_command))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Создаем кнопку для открытия Mini App
        webapp = WebAppInfo(url=self.webapp_url)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Открыть магазин", web_app=webapp)]
        ])
        
        welcome_text = f"""
🎉 Добро пожаловать в 5ka Mini App, {user.first_name}!

Этот бот позволяет заказывать товары из магазинов Пятёрочка прямо в Telegram.

🛍️ Что можно делать:
• Найти ближайшие магазины по вашему адресу
• Просматривать каталог товаров
• Добавлять товары в корзину
• Оформлять заказы

Нажмите кнопку ниже, чтобы начать покупки!
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 <b>Помощь по использованию 5ka Mini App</b>

<b>Основные команды:</b>
/start - Запуск бота и открытие магазина
/shop - Быстрый доступ к каталогу
/help - Эта справка

<b>Как пользоваться:</b>
1️⃣ Нажмите "Открыть магазин"
2️⃣ Введите ваш адрес для поиска ближайших магазинов
3️⃣ Выберите категорию товаров
4️⃣ Добавьте товары в корзину
5️⃣ Оформите заказ

<b>Возникли проблемы?</b>
Напишите @your_support_username
        """
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def shop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрое открытие магазина"""
        webapp = WebAppInfo(url=self.webapp_url)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Перейти в магазин", web_app=webapp)]
        ])
        
        await update.message.reply_text(
            "🛍️ Нажмите кнопку для перехода в магазин:",
            reply_markup=keyboard
        )
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск Telegram бота...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    # Получаем токен и URL из переменных окружения  
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "https://yourdomain.com")
    
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
    
    # Создаем и запускаем бота
    bot = TelegramBot(BOT_TOKEN, WEBAPP_URL)
    bot.run()