# run.py
import asyncio
import uvicorn
import subprocess
import sys
from pathlib import Path


def run_telegram_bot():
    """Запуск Telegram бота в отдельном процессе"""
    subprocess.Popen([sys.executable, "telegram_bot.py"])


def run_fastapi_server():
    """Запуск FastAPI сервера"""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    print("🚀 Запуск 5ka Telegram Mini App...")
    print("📱 Telegram бот запускается...")

    # Запускаем бота
    run_telegram_bot()

    print("🌐 FastAPI сервер запускается на http://localhost:8000")
    print("📋 Документация API: http://localhost:8000/docs")

    # Запускаем сервер (блокирующий вызов)
    run_fastapi_server()