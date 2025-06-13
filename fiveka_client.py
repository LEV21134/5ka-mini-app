import httpx
import json
import asyncio
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, quote
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class FiveKaClient:
    """Расширенный клиент для работы с API 5ka.ru"""
    
    def __init__(self):
        self.base_url