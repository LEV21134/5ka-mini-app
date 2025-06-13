from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import json
import asyncio
from datetime import datetime
import logging
from urllib.parse import urljoin, quote
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="5ka Proxy API", version="1.0.0")

# CORS middleware для работы с Telegram Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class AddressRequest(BaseModel):
    address: str
    comment: Optional[str] = None

class ProductSearch(BaseModel):
    query: Optional[str] = None
    category_id: Optional[int] = None
    page: int = 1
    limit: int = 20

class CartItem(BaseModel):
    product_id: str
    quantity: int
    price: float
    name: str

class Cart(BaseModel):
    user_id: str
    items: List[CartItem]
    total_price: float
    address: str
    comment: Optional[str] = None

# Хранилище данных (в продакшене использовать Redis или базу данных)
user_sessions = {}
user_carts = {}

class FiveKaAPI:
    """Класс для работы с API 5ka.ru"""
    
    def __init__(self):
        self.base_url = "https://5ka.ru"
        self.api_base = "https://5ka.ru/api"
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
    
    async def get_client(self):
        """Получить HTTP клиент"""
        if not self.session:
            self.session = httpx.AsyncClient(
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True
            )
        return self.session
    
    async def search_address(self, address: str):
        """Поиск адреса и получение информации о магазинах"""
        try:
            client = await self.get_client()
            
            # Ищем адрес через API геокодирования
            geocode_url = f"{self.api_base}/geocode"
            params = {
                'address': address,
                'limit': 10
            }
            
            response = await client.get(geocode_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logger.error(f"Geocode API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching address: {e}")
            return None
    
    async def get_stores_by_location(self, lat: float, lon: float, radius: int = 5000):
        """Получить магазины по координатам"""
        try:
            client = await self.get_client()
            
            stores_url = f"{self.api_base}/stores"
            params = {
                'lat': lat,
                'lon': lon,
                'radius': radius
            }
            
            response = await client.get(stores_url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Stores API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting stores: {e}")
            return []
    
    async def get_categories(self, store_id: Optional[str] = None):
        """Получить категории товаров"""
        try:
            client = await self.get_client()
            
            categories_url = f"{self.api_base}/categories"
            params = {}
            if store_id:
                params['store_id'] = store_id
            
            response = await client.get(categories_url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Categories API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    async def search_products(self, query: str = None, category_id: int = None, 
                            store_id: str = None, page: int = 1, limit: int = 20):
        """Поиск товаров"""
        try:
            client = await self.get_client()
            
            products_url = f"{self.api_base}/products"
            params = {
                'page': page,
                'limit': limit
            }
            
            if query:
                params['q'] = query
            if category_id:
                params['category_id'] = category_id
            if store_id:
                params['store_id'] = store_id
            
            response = await client.get(products_url, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Products API error: {response.status_code}")
                return {'products': [], 'total': 0}
                
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return {'products': [], 'total': 0}
    
    async def get_product_details(self, product_id: str):
        """Получить детальную информацию о товаре"""
        try:
            client = await self.get_client()
            
            product_url = f"{self.api_base}/products/{product_id}"
            response = await client.get(product_url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Product details API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return None

# Инициализация API клиента
fiveka_api = FiveKaAPI()

# Эндпоинты API

@app.get("/")
async def root():
    """Главная страница с Telegram Mini App"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>5ka Mini App</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--tg-theme-bg-color, #ffffff);
                color: var(--tg-theme-text-color, #000000);
                padding: 20px;
            }
            .container {
                max-width: 400px;
                margin: 0 auto;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
            }
            input, textarea {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
            }
            button {
                width: 100%;
                padding: 12px;
                background: var(--tg-theme-button-color, #007AFF);
                color: var(--tg-theme-button-text-color, #ffffff);
                border: none;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
            }
            button:hover {
                opacity: 0.8;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛒 5ka Mini App</h1>
            
            <div id="address-form">
                <div class="form-group">
                    <label for="address">Адрес доставки:</label>
                    <input type="text" id="address" placeholder="Введите ваш адрес" required>
                </div>
                
                <div class="form-group">
                    <label for="comment">Комментарий (необязательно):</label>
                    <textarea id="comment" placeholder="Комментарий к заказу" rows="3"></textarea>
                </div>
                
                <button onclick="submitAddress()">Найти магазины</button>
            </div>
            
            <div id="loading" class="loading">
                <p>Загрузка...</p>
            </div>
            
            <div id="content" style="display: none;">
                <!-- Здесь будет отображаться каталог товаров -->
            </div>
        </div>

        <script>
            // Инициализация Telegram Web App
            const tg = window.Telegram.WebApp;
            tg.ready();
            
            // Применение темы Telegram
            document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';
            document.body.style.color = tg.themeParams.text_color || '#000000';
            
            async function submitAddress() {
                const address = document.getElementById('address').value;
                const comment = document.getElementById('comment').value;
                
                if (!address.trim()) {
                    tg.showAlert('Пожалуйста, введите адрес');
                    return;
                }
                
                document.getElementById('address-form').style.display = 'none';
                document.getElementById('loading').style.display = 'block';
                
                try {
                    const response = await fetch('/api/set-address', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            address: address,
                            comment: comment,
                            user_id: tg.initDataUnsafe?.user?.id || 'demo_user'
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        await loadCatalog();
                    } else {
                        tg.showAlert('Ошибка: ' + result.message);
                        showAddressForm();
                    }
                } catch (error) {
                    console.error('Error:', error);
                    tg.showAlert('Произошла ошибка при обработке запроса');
                    showAddressForm();
                }
            }
            
            async function loadCatalog() {
                try {
                    const response = await fetch('/api/categories');
                    const categories = await response.json();
                    
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('content').style.display = 'block';
                    
                    displayCategories(categories);
                } catch (error) {
                    console.error('Error loading catalog:', error);
                    tg.showAlert('Ошибка загрузки каталога');
                }
            }
            
            function displayCategories(categories) {
                const content = document.getElementById('content');
                let html = '<h2>Выберите категорию:</h2>';
                
                categories.forEach(category => {
                    html += `
                        <div style="padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; cursor: pointer;" 
                             onclick="loadProducts(${category.id}, '${category.name}')">
                            <h3>${category.name}</h3>
                            <p style="color: #666; font-size: 14px;">${category.description || ''}</p>
                        </div>
                    `;
                });
                
                content.innerHTML = html;
            }
            
            async function loadProducts(categoryId, categoryName) {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('content').style.display = 'none';
                
                try {
                    const response = await fetch(`/api/products?category_id=${categoryId}&limit=20`);
                    const data = await response.json();
                    
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('content').style.display = 'block';
                    
                    displayProducts(data.products, categoryName);
                } catch (error) {
                    console.error('Error loading products:', error);
                    tg.showAlert('Ошибка загрузки товаров');
                }
            }
            
            function displayProducts(products, categoryName) {
                const content = document.getElementById('content');
                let html = `
                    <div style="margin-bottom: 20px;">
                        <button onclick="loadCatalog()" style="width: auto; padding: 8px 16px; margin-right: 10px;">← Назад</button>
                        <h2>${categoryName}</h2>
                    </div>
                `;
                
                products.forEach(product => {
                    html += `
                        <div style="padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px;">
                            <div style="display: flex; align-items: center;">
                                ${product.image ? `<img src="${product.image}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px; margin-right: 15px;">` : ''}
                                <div style="flex: 1;">
                                    <h3 style="margin-bottom: 5px;">${product.name}</h3>
                                    <p style="color: #666; font-size: 14px; margin-bottom: 10px;">${product.description || ''}</p>
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="font-size: 18px; font-weight: bold; color: #007AFF;">${product.price} ₽</span>
                                        <button onclick="addToCart('${product.id}', '${product.name}', ${product.price})" 
                                                style="width: auto; padding: 8px 16px; font-size: 14px;">
                                            В корзину
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                content.innerHTML = html;
            }
            
            async function addToCart(productId, productName, price) {
                try {
                    const response = await fetch('/api/cart/add', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            user_id: tg.initDataUnsafe?.user?.id || 'demo_user',
                            product_id: productId,
                            name: productName,
                            price: price,
                            quantity: 1
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        tg.showAlert('Товар добавлен в корзину!');
                        tg.MainButton.setText(`Корзина (${result.cart_count})`);
                        tg.MainButton.show();
                        tg.MainButton.onClick(() => showCart());
                    } else {
                        tg.showAlert('Ошибка добавления в корзину');
                    }
                } catch (error) {
                    console.error('Error adding to cart:', error);
                    tg.showAlert('Ошибка добавления в корзину');
                }
            }
            
            async function showCart() {
                try {
                    const userId = tg.initDataUnsafe?.user?.id || 'demo_user';
                    const response = await fetch(`/api/cart/${userId}`);
                    const cart = await response.json();
                    
                    let html = '<h2>Корзина</h2>';
                    
                    if (cart.items && cart.items.length > 0) {
                        cart.items.forEach(item => {
                            html += `
                                <div style="padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <h4>${item.name}</h4>
                                            <p>Количество: ${item.quantity}</p>
                                        </div>
                                        <div style="text-align: right;">
                                            <p style="font-weight: bold;">${item.price * item.quantity} ₽</p>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                        
                        html += `
                            <div style="margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
                                <h3>Итого: ${cart.total_price} ₽</h3>
                                <button onclick="checkout()" style="margin-top: 10px;">Оформить заказ</button>
                            </div>
                        `;
                    } else {
                        html += '<p>Корзина пуста</p>';
                    }
                    
                    document.getElementById('content').innerHTML = html;
                } catch (error) {
                    console.error('Error loading cart:', error);
                    tg.showAlert('Ошибка загрузки корзины');
                }
            }
            
            function showAddressForm() {
                document.getElementById('address-form').style.display = 'block';
                document.getElementById('loading').style.display = 'none';
                document.getElementById('content').style.display = 'none';
            }
            
            function checkout() {
                tg.showAlert('Функция оформления заказа будет добавлена позже');
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/set-address")
async def set_address(request: dict):
    """Установить адрес пользователя"""
    try:
        user_id = request.get('user_id', 'demo_user')
        address = request.get('address')
        comment = request.get('comment', '')
        
        if not address:
            return {'success': False, 'message': 'Адрес не указан'}
        
        # Поиск адреса и магазинов
        address_data = await fiveka_api.search_address(address)
        
        # Сохраняем данные пользователя
        user_sessions[user_id] = {
            'address': address,
            'comment': comment,
            'address_data': address_data,
            'timestamp': datetime.now().isoformat()
        }
        
        return {'success': True, 'message': 'Адрес установлен'}
        
    except Exception as e:
        logger.error(f"Error setting address: {e}")
        return {'success': False, 'message': 'Ошибка обработки адреса'}

@app.get("/api/categories")
async def get_categories():
    """Получить категории товаров"""
    try:
        categories = await fiveka_api.get_categories()
        return categories
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return []

@app.get("/api/products")
async def get_products(
    query: Optional[str] = None,
    category_id: Optional[int] = None,
    page: int = 1,
    limit: int = 20
):
    """Получить товары"""
    try:
        products = await fiveka_api.search_products(
            query=query,
            category_id=category_id,
            page=page,
            limit=limit
        )
        return products
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return {'products': [], 'total': 0}

@app.post("/api/cart/add")
async def add_to_cart(request: dict):
    """Добавить товар в корзину"""
    try:
        user_id = request.get('user_id', 'demo_user')
        product_id = request.get('product_id')
        name = request.get('name')
        price = request.get('price')
        quantity = request.get('quantity', 1)
        
        if user_id not in user_carts:
            user_carts[user_id] = {
                'items': [],
                'total_price': 0
            }
        
        cart = user_carts[user_id]
        
        # Проверяем, есть ли уже этот товар в корзине
        existing_item = None
        for item in cart['items']:
            if item['product_id'] == product_id:
                existing_item = item
                break
        
        if existing_item:
            existing_item['quantity'] += quantity
        else:
            cart['items'].append({
                'product_id': product_id,
                'name': name,
                'price': price,
                'quantity': quantity
            })
        
        # Пересчитываем общую стоимость
        cart['total_price'] = sum(item['price'] * item['quantity'] for item in cart['items'])
        
        return {
            'success': True,
            'cart_count': len(cart['items']),
            'total_price': cart['total_price']
        }
        
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        return {'success': False, 'message': 'Ошибка добавления в корзину'}

@app.get("/api/cart/{user_id}")
async def get_cart(user_id: str):
    """Получить корзину пользователя"""
    try:
        if user_id not in user_carts:
            return {'items': [], 'total_price': 0}
        
        return user_carts[user_id]
        
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        return {'items': [], 'total_price': 0}

@app.delete("/api/cart/{user_id}")
async def clear_cart(user_id: str):
    """Очистить корзину"""
    try:
        if user_id in user_carts:
            del user_carts[user_id]
        
        return {'success': True, 'message': 'Корзина очищена'}
        
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        return {'success': False, 'message': 'Ошибка очистки корзины'}

@app.get("/api/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(user_sessions),
        'active_carts': len(user_carts)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)