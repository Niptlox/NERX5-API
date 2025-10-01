"""
Тесты производительности
"""
import asyncio
import time
import statistics
import httpx
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

class TestPerformance:
    """Тесты производительности API"""
    
    BASE_URL = "http://localhost:8000"
    
    def test_single_request_latency(self):
        """Тест задержки одного запроса"""
        response_times = []
        
        for _ in range(100):
            start_time = time.time()
            response = requests.post(
                f"{self.BASE_URL}/api/predict",
                json={"input": "сгущенное молоко"}
            )
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_time = statistics.mean(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        
        print(f"Среднее время ответа: {avg_time * 1000:.2f}ms")
        print(f"P95 время ответа: {p95_time * 1000:.2f}ms")
        
        # Требование: среднее время < 50ms
        assert avg_time < 0.05
        # Требование: P95 время < 100ms
        assert p95_time < 0.1
    
    def test_throughput_sequential(self):
        """Тест пропускной способности (последовательно)"""
        num_requests = 100
        start_time = time.time()
        
        successful_requests = 0
        for i in range(num_requests):
            response = requests.post(
                f"{self.BASE_URL}/api/predict",
                json={"input": f"тест {i}"}
            )
            if response.status_code == 200:
                successful_requests += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        rps = successful_requests / total_time
        
        print(f"Последовательный RPS: {rps:.2f}")
        print(f"Время выполнения: {total_time:.2f}s")
        print(f"Успешные запросы: {successful_requests}/{num_requests}")
        
        # Требование: минимум 20 RPS
        assert rps >= 20
        assert successful_requests == num_requests
    
    def test_throughput_concurrent(self):
        """Тест пропускной способности (параллельно)"""
        num_requests = 100
        max_workers = 10
        
        def make_request(i):
            response = requests.post(
                f"{self.BASE_URL}/api/predict",
                json={"input": f"параллельный тест {i}"}
            )
            return response.status_code == 200
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            successful_requests = sum(future.result() for future in as_completed(futures))
        
        end_time = time.time()
        total_time = end_time - start_time
        rps = successful_requests / total_time
        
        print(f"Параллельный RPS: {rps:.2f}")
        print(f"Время выполнения: {total_time:.2f}s")
        print(f"Успешные запросы: {successful_requests}/{num_requests}")
        print(f"Параллельных потоков: {max_workers}")
        
        # Требование: минимум 20 RPS при параллельной обработке
        assert rps >= 20
        assert successful_requests >= num_requests * 0.95  # Допускаем 5% ошибок
    
    @pytest.mark.asyncio
    async def test_async_throughput(self):
        """Тест асинхронной пропускной способности"""
        num_requests = 100
        
        async def make_async_request(session, i):
            try:
                response = await session.post(
                    f"{self.BASE_URL}/api/predict",
                    json={"input": f"async тест {i}"}
                )
                return response.status_code == 200
            except:
                return False
        
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            tasks = [make_async_request(client, i) for i in range(num_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful_requests = sum(1 for result in results if result is True)
        
        end_time = time.time()
        total_time = end_time - start_time
        rps = successful_requests / total_time
        
        print(f"Асинхронный RPS: {rps:.2f}")
        print(f"Время выполнения: {total_time:.2f}s")
        print(f"Успешные запросы: {successful_requests}/{num_requests}")
        
        assert rps >= 20
        assert successful_requests >= num_requests * 0.9
    
    def test_memory_usage(self):
        """Тест потребления памяти"""
        import psutil
        import os
        
        # Получаем процесс API (предполагаем, что он запущен)
        api_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'uvicorn' in proc.info['name'] or any('main:app' in str(cmd) for cmd in proc.info['cmdline']):
                    api_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if not api_processes:
            pytest.skip("API процесс не найден")
        
        # Измеряем память до нагрузки
        initial_memory = sum(proc.memory_info().rss for proc in api_processes) / 1024 / 1024  # MB
        
        # Создаем нагрузку
        for _ in range(1000):
            requests.post(
                f"{self.BASE_URL}/api/predict",
                json={"input": "тест потребления памяти"}
            )
        
        # Измеряем память после нагрузки
        final_memory = sum(proc.memory_info().rss for proc in api_processes) / 1024 / 1024  # MB
        
        memory_increase = final_memory - initial_memory
        
        print(f"Память до нагрузки: {initial_memory:.2f} MB")
        print(f"Память после нагрузки: {final_memory:.2f} MB")
        print(f"Увеличение памяти: {memory_increase:.2f} MB")
        
        # Требование: увеличение памяти не более 100MB
        assert memory_increase < 100
    
    def test_error_handling_performance(self):
        """Тест производительности при обработке ошибок"""
        num_requests = 50
        error_cases = [
            {"input": "x" * 10000},  # Очень длинный текст
            {},  # Пустой запрос
            {"input": None},  # None значение
        ]
        
        start_time = time.time()
        
        for _ in range(num_requests):
            for error_case in error_cases:
                response = requests.post(
                    f"{self.BASE_URL}/api/predict",
                    json=error_case
                )
                # Проверяем, что API не падает и возвращает корректный статус
                assert response.status_code in [200, 400, 422, 500]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"Время обработки {num_requests * len(error_cases)} ошибочных запросов: {total_time:.2f}s")
        
        # Даже с ошибками API должен отвечать быстро
        assert total_time < 10

if __name__ == "__main__":
    pytest.main([__file__, "-v"])