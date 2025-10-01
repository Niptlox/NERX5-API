"""
Сбор метрик приложения
"""
import time
import asyncio
from typing import Dict, Any
from collections import defaultdict, deque
from ..core.logging import metrics_logger

class MetricsCollector:
    """Сборщик метрик приложения"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.request_times = deque(maxlen=window_size)
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self._lock = asyncio.Lock()
        
        # Детальные метрики
        self.response_times_by_endpoint = defaultdict(lambda: deque(maxlen=100))
        self.error_types = defaultdict(int)
        
    async def record_request(self, endpoint: str, response_time: float, success: bool, error_type: str = None):
        """Записать метрики запроса"""
        async with self._lock:
            self.request_times.append(response_time)
            self.response_times_by_endpoint[endpoint].append(response_time)
            self.request_count += 1
            
            if success:
                self.success_count += 1
            else:
                self.error_count += 1
                if error_type:
                    self.error_types[error_type] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получить текущие метрики"""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # Среднее время ответа
        avg_response_time = (
            sum(self.request_times) / len(self.request_times) * 1000 
            if self.request_times else 0.0
        )
        
        # RPS за последние секунды
        recent_requests = [
            t for t in self.request_times 
            if current_time - t <= 1.0
        ]
        rps = len(recent_requests) if recent_requests else 0.0
        
        # P95 время ответа
        if self.request_times:
            sorted_times = sorted(self.request_times)
            p95_index = int(len(sorted_times) * 0.95)
            p95_response_time = sorted_times[p95_index] * 1000 if p95_index < len(sorted_times) else 0.0
        else:
            p95_response_time = 0.0
        
        return {
            "total_requests": self.request_count,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "average_response_time": avg_response_time,
            "p95_response_time": p95_response_time,
            "requests_per_second": rps,
            "uptime_seconds": uptime,
            "error_rate": self.error_count / max(self.request_count, 1) * 100,
            "error_types": dict(self.error_types)
        }
    
    def get_endpoint_metrics(self, endpoint: str) -> Dict[str, Any]:
        """Метрики для конкретного endpoint"""
        times = self.response_times_by_endpoint[endpoint]
        if not times:
            return {"requests": 0, "avg_time": 0.0}
        
        avg_time = sum(times) / len(times) * 1000
        return {
            "requests": len(times),
            "avg_time": avg_time,
            "min_time": min(times) * 1000,
            "max_time": max(times) * 1000
        }
    
    async def reset_metrics(self):
        """Сброс метрик"""
        async with self._lock:
            self.request_times.clear()
            self.response_times_by_endpoint.clear()
            self.request_count = 0
            self.success_count = 0
            self.error_count = 0
            self.error_types.clear()
            self.start_time = time.time()
            metrics_logger.info("Метрики сброшены")

# Глобальный сборщик метрик
metrics_collector = MetricsCollector()