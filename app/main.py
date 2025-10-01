"""
Главное приложение FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .models.ner_model import ner_model
from .monitoring.middleware import MetricsMiddleware
from .core.config import settings
from .core.logging import app_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager для FastAPI приложения"""
    # Startup
    app_logger.info("Запуск NER API сервиса...")
    
    # Загрузка модели
    success = await ner_model.load_model()
    if not success:
        app_logger.error("Не удалось загрузить модель!")
        raise RuntimeError("Модель не загружена")
    
    app_logger.info("Сервис успешно запущен")
    
    yield
    
    # Shutdown
    app_logger.info("Остановка сервиса...")

# Создание FastAPI приложения
app = FastAPI(
    title="NER API Service",
    description="Высокопроизводительный API для извлечения именованных сущностей",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем middleware для метрик
app.add_middleware(
    MetricsMiddleware,
    exclude_paths=["/docs", "/openapi.json", "/redoc", "/favicon.ico"]
)

# Подключение роутов
app.include_router(router)

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Корневой endpoint"""
    return {
        "message": "NER API Service", 
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    
    app_logger.info(f"Запуск сервера на порту {settings.api_port}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        workers=settings.max_workers,
        loop="asyncio",
        access_log=True
    )