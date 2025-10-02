"""
Тесты API endpoints
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAPIEndpoints:
    """Тесты основных API endpoints"""
    
    def test_root_endpoint(self):
        """Тест корневого endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
    
    def test_health_endpoint(self):
        """Тест health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "device" in data
    
    def test_predict_endpoint_empty_input(self):
        """Тест предсказания с пустым вводом"""
        response = client.post("/api/predict", json={"input": ""})
        assert response.status_code == 200
        data = response.json()        
        assert data == []
    
    def test_predict_endpoint_normal_input(self):
        """Тест предсказания с обычным текстом"""
        response = client.post("/api/predict", json={"input": "сгущенное молоко"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    
    def test_predict_endpoint_invalid_input(self):
        """Тест предсказания с некорректными данными"""
        response = client.post("/api/predict", json={})
        assert response.status_code == 422  # Validation error
    
    def test_metrics_endpoint(self):
        """Тест metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "successful_requests" in data
        assert "failed_requests" in data
        assert "average_response_time" in data
        assert "requests_per_second" in data
    
    def test_batch_predict_endpoint(self):
        """Тест батчевого предсказания"""
        requests_data = [
            {"input": "молоко"},
            {"input": "хлеб"},
            {"input": ""}
        ]
        response = client.post("/api/predict/batch", json=requests_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(isinstance(item, list) for item in data)
    
    def test_cache_endpoints(self):
        """Тест cache endpoints"""
        # Получение статистики кеша
        response = client.get("/cache/stats")
        assert response.status_code == 200
        
        # Очистка кеша
        response = client.delete("/cache")
        assert response.status_code == 200
        assert "message" in response.json()

class TestEntityStructure:
    """Тесты структуры сущностей"""
    
    def test_entity_structure(self):
        """Тест корректности структуры сущностей"""
        response = client.post("/api/predict", json={"input": "молоко простоквашино"})
        assert response.status_code == 200
        data = response.json()
        
        for entity in data:
            assert "start_index" in entity
            assert "end_index" in entity
            assert "entity" in entity
            assert isinstance(entity["start_index"], int)
            assert isinstance(entity["end_index"], int)
            assert isinstance(entity["entity"], str)
            assert entity["start_index"] >= 0
            assert entity["end_index"] > entity["start_index"]

@pytest.mark.asyncio
class TestAsyncPerformance:
    """Тесты производительности"""
    
    async def test_concurrent_requests(self):
        """Тест параллельных запросов"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
            tasks = []
            for i in range(10):
                task = ac.post("/api/predict", json={"input": f"тест {i}"})
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            
            # Все запросы должны быть успешными
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
    
    async def test_response_time(self):
        """Тест времени ответа"""
        import time
        
        async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
            start_time = time.time()
            response = await ac.post("/api/predict", json={"input": "сгущенное молоко"})
            end_time = time.time()
            
            assert response.status_code == 200
            # Время ответа должно быть менее 800ms для одного запроса
            assert (end_time - start_time) < 0.8

if __name__ == "__main__":
    pytest.main([__file__])