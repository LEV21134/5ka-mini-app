from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI(title="5ka Telegram Mini App", version="1.0.0")

# CORS для Telegram Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    html_content = '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>5ka Mini App</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0; padding: 20px;
                background: var(--tg-theme-bg-color, #ffffff);
                color: var(--tg-theme-text-color, #000000);
            }
            .container { max-width: 400px; margin: 0 auto; }
            h1 { text-align: center; color: #007AFF; }
            .status { 
                padding: 15px; background: #f0f8ff; 
                border-radius: 8px; margin: 20px 0; 
            }
            button {
                width: 100%;
                padding: 12px;
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                margin: 10px 0;
            }
            input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin: 10px 0;
                box-sizing: border-box;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛒 5ka Mini App</h1>
            <div class="status">
                <h3>✅ Сервер работает!</h3>
                <p>📱 Telegram Mini App готов к работе</p>

                <div style="margin-top: 20px;">
                    <h4>🏪 Поиск магазинов:</h4>
                    <input type="text" id="address" placeholder="Введите адрес" />
                    <button onclick="searchStores()">Найти магазины</button>
                </div>

                <div style="margin-top: 20px;">
                    <h4>📚 Ссылки:</h4>
                    <p>📋 <a href="/docs" target="_blank">API Документация</a></p>
                    <p>🔧 <a href="/api/health" target="_blank">Health Check</a></p>
                </div>
            </div>
        </div>

        <script>
            // Инициализация Telegram Web App
            if (window.Telegram && window.Telegram.WebApp) {
                const tg = window.Telegram.WebApp;
                tg.ready();
                console.log('Telegram WebApp initialized');

                // Применяем тему Telegram
                document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';
                document.body.style.color = tg.themeParams.text_color || '#000000';
            }

            function searchStores() {
                const address = document.getElementById('address').value;
                if (address) {
                    alert('Поиск магазинов для адреса: ' + address);
                } else {
                    alert('Введите адрес для поиска');
                }
            }
        </script>
    </body>
    </html>
    '''
    return HTMLResponse(content=html_content)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "5ka Mini App API is running",
        "version": "1.0.0"
    }


@app.get("/api/stores")
async def get_stores():
    # Заглушка для магазинов
    return {
        "stores": [
            {
                "id": "1",
                "name": "Пятёрочка на Тверской",
                "address": "ул. Тверская, 15",
                "coordinates": [37.6176, 55.7558],
                "working_hours": "08:00-23:00"
            },
            {
                "id": "2",
                "name": "Пятёрочка на Арбате",
                "address": "ул. Арбат, 25",
                "coordinates": [37.6001, 55.7522],
                "working_hours": "08:00-22:00"
            }
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"🚀 Запуск сервера на http://{host}:{port}")
    print(f"📚 API документация: http://{host}:{port}/docs")

    uvicorn.run(app, host=host, port=port, reload=True)
