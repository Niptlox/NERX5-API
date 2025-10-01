"""
Middleware для мониторинга производительности
"""
import time
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..services.metrics import metrics_collector
from ..core.logging import app_logger

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware для сбора метрик HTTP запросов"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/docs", "/openapi.json", "/redoc"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Исключаем определенные пути из мониторинга
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            success = response.status_code < 400
            
            # Записываем метрики асинхронно
            response_time = time.time() - start_time
            asyncio.create_task(
                metrics_collector.record_request(
                    endpoint=request.url.path,
                    response_time=response_time,
                    success=success
                )
            )
            
            # Добавляем заголовки ответа
            response.headers["X-Response-Time"] = f"{response_time * 1000:.2f}ms"
            return response
            
        except Exception as e:
            # Записываем ошибку в метрики
            response_time = time.time() - start_time
            asyncio.create_task(
                metrics_collector.record_request(
                    endpoint=request.url.path,
                    response_time=response_time,
                    success=False,
                    error_type=type(e).__name__
                )
            )
            raise

class CORSMiddleware:
    """Простой CORS middleware"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            await response(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", []))
                message["headers"].append((b"Access-Control-Allow-Origin", b"*"))
                message["headers"].append((b"Access-Control-Allow-Methods", b"GET, POST, PUT, DELETE, OPTIONS"))
                message["headers"].append((b"Access-Control-Allow-Headers", b"Content-Type, Authorization"))
            await send(message)
        
        await self.app(scope, receive, send_wrapper)