"""
API роуты
"""
import time
import asyncio
from typing import List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from ..models.schemas import PredictRequest, PredictResponse, Entity, HealthResponse, MetricsResponse
from ..services.prediction import prediction_service
from ..services.metrics import metrics_collector
from ..models.ner_model import ner_model
from ..core.logging import app_logger

router = APIRouter()

@router.post("/api/predict", response_model=PredictResponse, tags=["prediction"])
async def predict(request: PredictRequest) -> PredictResponse:
    """
    Извлечение именованных сущностей из текста
    """
    start_time = time.time()
    success = False
    error_type = None
    
    try:
        # Проверка пустого ввода
        if not request.input.strip():
            # Для пустого ввода возвращаем пустой список согласно требованиям
            entities = []
        else:
            # Предсказание сущностей
            entities = await prediction_service.predict(request.input)
            # entities = [Entity(**entity) for entity in entities_data]
        
        response = PredictResponse(root=entities)
        success = True
        return response
        
    except Exception as e:
        error_type = type(e).__name__
        app_logger.error(f"Ошибка в /api/predict: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке запроса: {str(e)}")
    
    finally:
        # Записываем метрики асинхронно
        response_time = time.time() - start_time
        asyncio.create_task(
            metrics_collector.record_request("/api/predict", response_time, success, error_type)
        )

@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    Проверка состояния сервиса
    """
    start_time = time.time()
    success = False
    
    try:
        model_loaded = ner_model.is_loaded()
        device = str(ner_model.device) if ner_model.device else "unknown"
        
        status = "healthy" if model_loaded else "unhealthy"
        
        response = HealthResponse(
            status=status,
            model_loaded=model_loaded,
            device=device
        )
        success = True
        return response
        
    except Exception as e:
        app_logger.error(f"Ошибка в /health: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при проверке состояния")
    
    finally:
        response_time = time.time() - start_time
        asyncio.create_task(
            metrics_collector.record_request("/health", response_time, success)
        )

@router.get("/metrics", response_model=MetricsResponse, tags=["monitoring"])
async def get_metrics() -> MetricsResponse:
    """
    Получение метрик производительности
    """
    start_time = time.time()
    success = False
    
    try:
        metrics_data = metrics_collector.get_metrics()
        
        response = MetricsResponse(
            total_requests=metrics_data["total_requests"],
            successful_requests=metrics_data["successful_requests"],
            failed_requests=metrics_data["failed_requests"],
            average_response_time=metrics_data["average_response_time"],
            requests_per_second=metrics_data["requests_per_second"]
        )
        success = True
        return response
        
    except Exception as e:
        app_logger.error(f"Ошибка в /metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при получении метрик")
    
    finally:
        response_time = time.time() - start_time
        asyncio.create_task(
            metrics_collector.record_request("/metrics", response_time, success)
        )

@router.post("/api/predict/batch", tags=["prediction"])
async def predict_batch(requests: List[PredictRequest]) -> List[PredictResponse]:
    """
    Батчевое извлечение сущностей
    """
    start_time = time.time()
    success = False
    
    try:
        if not requests:
            return []
        
        texts = [req.input for req in requests]
        batch_results = await prediction_service.batch_predict(texts)
        
        responses = []
        for entities_data in batch_results:            
            responses.append(PredictResponse(entities_data))
        
        success = True
        return responses
        
    except Exception as e:
        app_logger.error(f"Ошибка в /api/predict/batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при батчевой обработке: {str(e)}")
    
    finally:
        response_time = time.time() - start_time
        asyncio.create_task(
            metrics_collector.record_request("/api/predict/batch", response_time, success)
        )

@router.delete("/cache", tags=["admin"])
async def clear_cache():
    """
    Очистка кеша предсказаний
    """
    try:
        prediction_service.clear_cache()
        return {"message": "Кеш очищен"}
    except Exception as e:
        app_logger.error(f"Ошибка при очистке кеша: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при очистке кеша")

@router.get("/cache/stats", tags=["admin"])
async def get_cache_stats():
    """
    Статистика кеша
    """
    try:
        stats = prediction_service.get_cache_stats()
        return stats
    except Exception as e:
        app_logger.error(f"Ошибка при получении статистики кеша: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при получении статистики")