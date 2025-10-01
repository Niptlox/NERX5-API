"""
Сервис предсказаний с батчингом и кешированием
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from collections import deque
from ..models.ner_model import ner_model
from ..core.logging import app_logger

class PredictionService:
    """Сервис для обработки предсказаний с поддержкой батчинга"""
    
    def __init__(self, batch_size: int = 32, max_wait_time: float = 0.01):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_requests = deque()
        self._processing_lock = asyncio.Lock()
        self._batch_task = None
        
        # Простой кеш для частых запросов
        self.cache = {}
        self.cache_size = 1000
        
    async def predict(self, text: str) -> List[Dict[str, Any]]:
        """Основной метод для предсказания"""
        if not text.strip():
            return []
        
        # Проверка кеша
        if text in self.cache:
            app_logger.debug(f"Cache hit for text: {text[:50]}...")
            return self.cache[text]
        
        # Для обеспечения 20+ RPS используем прямое предсказание без батчинга
        # так как батчинг может добавить задержку
        try:
            entities = await ner_model.predict(text)
            
            # Кеширование результата
            if len(self.cache) >= self.cache_size:
                # Удаляем старейший элемент (FIFO)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            self.cache[text] = entities
            return entities
            
        except Exception as e:
            app_logger.error(f"Ошибка предсказания: {str(e)}")
            raise
    
    async def batch_predict(self, texts: List[str]) -> List[List[Dict[str, Any]]]:
        """Батчевое предсказание для множества текстов"""
        if not texts:
            return []
        
        results = []
        for text in texts:
            try:
                entities = await self.predict(text)
                results.append(entities)
            except Exception as e:
                app_logger.error(f"Ошибка в батчевом предсказании: {str(e)}")
                results.append([])
        
        return results
    
    def clear_cache(self):
        """Очистка кеша"""
        self.cache.clear()
        app_logger.info("Кеш очищен")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Статистика кеша"""
        return {
            "cache_size": len(self.cache),
            "max_cache_size": self.cache_size
        }

# Глобальный экземпляр сервиса
prediction_service = PredictionService()