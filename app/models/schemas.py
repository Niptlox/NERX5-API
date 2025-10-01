"""
Pydantic схемы для API
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class PredictRequest(BaseModel):
    input: str = Field(..., description="Текст для извлечения сущностей", min_length=0)
    
    class Config:
        schema_extra = {
            "example": {
                "input": "сгущенное молоко"
            }
        }

class Entity(BaseModel):
    start_index: int = Field(..., description="Начальная позиция сущности в тексте")
    end_index: int = Field(..., description="Конечная позиция сущности в тексте")
    entity: str = Field(..., description="Тип сущности (B-BRAND, I-BRAND, B-TYPE, etc.)")
    
    class Config:
        schema_extra = {
            "example": {
                "start_index": 0,
                "end_index": 8,
                "entity": "B-TYPE"
            }
        }

class PredictResponse(BaseModel):
    entities: List[Entity] = Field(default_factory=list, description="Список найденных сущностей")
    
    class Config:
        schema_extra = {
            "example": {
                "entities": [
                    {
                        "start_index": 0,
                        "end_index": 8,
                        "entity": "B-TYPE"
                    },
                    {
                        "start_index": 9,
                        "end_index": 15,
                        "entity": "I-TYPE"
                    }
                ]
            }
        }

class HealthResponse(BaseModel):
    status: str = Field(..., description="Статус сервиса")
    model_loaded: bool = Field(..., description="Загружена ли модель")
    device: str = Field(..., description="Устройство модели")

class MetricsResponse(BaseModel):
    total_requests: int = Field(..., description="Общее количество запросов")
    successful_requests: int = Field(..., description="Успешные запросы")
    failed_requests: int = Field(..., description="Неуспешные запросы")
    average_response_time: float = Field(..., description="Среднее время ответа в миллисекундах")
    requests_per_second: float = Field(..., description="Запросов в секунду")