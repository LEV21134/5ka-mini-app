#!/usr/bin/env python3
"""
Универсальный скрипт запуска 5ka Telegram Mini App
Автоматически определяет окружение и запускает нужные компоненты
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path
from typing import Optional
import psutil

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FiveKaAppManager:
    def __init__(self):
        self.processes = []
        self.is_development = os.getenv('DEBUG', 'true').lower() == 'true'
        self.base_dir = Path(__file__).parent
        
    def check_dependencies(self) -> bool:
        """Проверка зависимостей"""
        logger.info("🔍 Проверка зависимостей...")
        
        # Проверка Python пакетов
        required_packages = ['fastapi', 'uvicorn', 'httpx', 'python-telegram-bot']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
            logger.info("📦 Установите их командой: pip install -r requirements.txt")
            return False
        
        # Проверка .env файла
        env_file = self.base_dir / '.env'
        if not env_file.exists():
            logger.error("❌ Файл .env не найден")
            logger.info("📝 Создайте файл .env по примеру .env.example")
            return False
        
        # Проверка Telegram токена
        from dotenv import load_dotenv
        load_dotenv()
        
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not telegram_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен в .env")
            return False
        
        logger.info("✅ Все зависимости в порядке")
        return True
    
    def check_ports(self) -> bool:
        """Проверка доступности портов"""
        ports_to_check = [8000]  # FastAPI порт
        
        for port in ports_to_check:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    logger.error(f"❌ Порт {port} уже занят")
                    logger.info(f"💡 Остановите процесс на порту {port} или измените PORT в .env")
                    return False
        
        logger.info("✅ Порты свободны")
        return True
    
    def create_directories(self):
        """Создание необходимых директорий"""
        directories = ['logs', 'static', 'static/images']
        
        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(exist_ok=True)
            logger.debug(f"📁 Создана директория: {directory}")
    
    def start_fastapi(self) -> subprocess.Popen:
        """Запуск FastAPI сервера"""
        logger.info("🌐 Запуск FastAPI сервера...")
        
        if self.is_development:
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "main:app", 
                "--reload", 
                "--host", "0.0.0.0", 
                "--port", "8000",
                "--log-level", "info"
            ]
        else:
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "main:app", 
                "--host", "0.0.0.0", 
                "--port", "8000",
                "--workers", "4"
            ]
        
        process = subprocess.Popen(
            cmd,
            cwd=self.base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Ждем запуска сервера
        time.sleep(3)
        
        if process.poll() is None:
            logger.info("✅ FastAPI сервер запущен на http://localhost:8000")
            return process
        else:
            logger.error("❌ Не удалось запустить FastAPI сервер")
            return None
    
    def start_telegram_bot(self) -> subprocess.Popen:
        """Запуск Telegram бота"""
        logger.info("🤖 Запуск Telegram бота...")
        
        bot_file = self.base_dir / 'telegram_bot.py'
        if not bot_file.exists():
            logger.error("❌ Файл telegram_bot.py не найден")
            return None
        
        process = subprocess.Popen(
            [sys.executable, str(bot_file)],
            cwd=self.base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        time.sleep(2)
        
        if process.poll() is None:
            logger.info("✅ Telegram бот запущен")
            return process
        else:
            logger.error("❌ Не удалось запустить Telegram бота")
            return None
    
    def start_development(self):
        """Запуск в режиме разработки"""
        logger.info("🚀 Запуск в режиме разработки...")
        
        # Запуск FastAPI с автоперезагрузкой
        fastapi_process = self.start_fastapi()
        if fastapi_process:
            self.processes.append(fastapi_process)
        
        # Запуск Telegram бота
        bot_process = self.start_telegram_bot()
        if bot_process:
            self.processes.append(bot_process)
        
        if self.processes:
            logger.info("🎉 Приложение запущено!")
            logger.info("📱 Telegram: Найдите вашего бота и отправьте /start")
            logger.info("🌐 API: http://localhost:8000")
            logger.info("📚 Документация: http://localhost:8000/docs")
            logger.info("⏹️  Для остановки нажмите Ctrl+C")
    
    def start_production(self):
        """Запуск в продакшене через Docker"""
        logger.info("🏭 Запуск в режиме продакшена...")
        
        # Проверка Docker
        try:
            subprocess.run(['docker', '--version'], check=True, capture_output=True)
            subprocess.run(['docker-compose', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ Docker или Docker Compose не установлен")
            logger.info("📦 Установите Docker: https://docs.docker.com/get-docker/")
            return
        
        # Запуск через Docker Compose
        compose_file = self.base_dir / 'docker-compose.yml'
        if not compose_file.exists():
            logger.error("❌ Файл docker-compose.yml не найден")
            return
        
        try:
            subprocess.run(
                ['docker-compose', 'up', '--build', '-d'],
                cwd=self.base_dir,
                check=True
            )
            logger.info("✅ Приложение запущено через Docker")
            logger.info("📊 Статус: docker-compose ps")
            logger.info("📋 Логи: docker-compose logs -f")
        except subprocess.CalledProcessError:
            logger.error("❌ Ошибка запуска Docker Compose")
    
    def stop_all(self):
        """Остановка всех процессов"""
        logger.info("🛑 Остановка приложения...")
        
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        self.processes.clear()
        logger.info("✅ Все процессы остановлены")
    
    def run(self):
        """Главная функция запуска"""
        def signal_handler(signum, frame):
            self.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Проверки
        if not self.check_dependencies():
            sys.exit(1)
        
        if not self.check_ports():
            sys.exit(1)
        
        # Создание директорий
        self.create_directories()
        
        # Запуск в зависимости от режима
        if self.is_development:
            self.start_development()
            
            # Ожидание в режиме разработки
            try:
                while True:
                    time.sleep(1)
                    # Проверяем, что процессы еще живы
                    for process in self.processes[:]:
                        if process.poll() is not None:
                            logger.warning(f"⚠️  Процесс завершился неожиданно: PID {process.pid}")
                            self.processes.remove(process)
            except KeyboardInterrupt:
                pass
        else:
            self.start_production()

def main():
    """Точка входа"""
    print("""
    🛒 5ka Telegram Mini App
    ========================
    """)
    
    # Проверка аргументов командной строки
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'dev':
            os.environ['DEBUG'] = 'true'
        elif command == 'prod':
            os.environ['DEBUG'] = 'false'
        elif command == 'check':
            manager = FiveKaAppManager()
            if manager.check_dependencies() and manager.check_ports():
                print("✅ Все проверки пройдены успешно")
                sys.exit(0)
            else:
                print("❌ Обнаружены проблемы")
                sys.exit(1)
        elif command == 'stop':
            try:
                subprocess.run(['docker-compose', 'down'], check=True)
                print("✅ Docker контейнеры остановлены")
            except subprocess.CalledProcessError:
                print("❌ Ошибка остановки Docker")
            sys.exit(0)
        else:
            print(f"""
Использование:
    python startup.py          # Автоопределение режима
    python startup.py dev       # Режим разработки
    python startup.py prod      # Продакшен (Docker)
    python startup.py check     # Проверка зависимостей
    python startup.py stop      # Остановка Docker
            """)
            sys.exit(1)
    
    # Запуск приложения
    manager = FiveKaAppManager()
    manager.run()

if __name__ == "__main__":
    main()