# Основные настройки
SECRET_KEY=your-super-secret-key-here
DEBUG=true
HOST=0.0.0.0
PORT=8000

# База данных (опционально, можно использовать SQLite)
DATABASE_URL=postgresql://postgres:password@localhost:5432/fiveka_proxy
# или для SQLite:
# DATABASE_URL=sqlite:///./fiveka.db

# Redis для кэширования (опционально)
REDIS_URL=redis://localhost:6379

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN=7700180865:AAGbjhypgopYF69osFH9QDFhWQsyClmYpSc
TELEGRAM_WEBHOOK_URL=https://skidkagram.su

# Настройки прокси для 5ka.ru
FIVEKA_BASE_URL=https://5ka.ru
FIVEKA_API_URL=https://5ka.ru/api

# Логирование
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

DEBUG=true
HOST=0.0.0.0
PORT=8000
WEBAPP_URL=https://skidkagram.su
DATABASE_URL=sqlite:///./fiveka.db
LOG_LEVEL=INFO