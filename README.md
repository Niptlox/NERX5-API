# NER FastAPI Distributed System

Высокопроизводительная распределенная система для извлечения именованных сущностей (Named Entity Recognition) на основе FastAPI с поддержкой минимум 20 запросов в секунду.

## Архитектура системы

### Компоненты
- **FastAPI API сервер** - основное API для предсказаний
- **NER модель** - rubert-tiny2 с кастомным классификатором
- **Streamlit дашборд** - мониторинг нагрузки и истории
- **Nginx** - балансировщик нагрузки и прокси
- **Docker** - контейнеризация всех сервисов

### Особенности
- Асинхронная обработка запросов
- Кеширование частых запросов
- Сбор метрик производительности
- Автоматические тесты
- Мониторинг в реальном времени

## API Endpoints

### POST /api/predict
Основной endpoint для извлечения сущностей:

```json
// Запрос
{
    "input": "сгущенное молоко"
}

// Ответ
[
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
```

### GET /health
Проверка состояния сервиса:

```json
{
    "status": "healthy",
    "model_loaded": true,
    "device": "cuda"
}
```

### GET /metrics
Метрики производительности:

```json
{
    "total_requests": 1000,
    "successful_requests": 995,
    "failed_requests": 5,
    "average_response_time": 23.5,
    "requests_per_second": 25.3
}
```

## Установка и запуск

### Подготовка модели
Поместите обученную модель в директорию `best_ner_model/`:
```
best_ner_model/
├── config.json
├── pytorch_model.bin
├── tokenizer.json
└── vocab.txt
```

### Запуск через Docker
```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# Только API сервис
docker run -p 8000:8000 ner-api

# С GPU поддержкой
docker run --gpus all -p 8000:8000 ner-api
```

### Локальная разработка
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск API сервера
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Запуск дашборда
streamlit run app/monitoring/dashboard.py --server.port 8501
```

## Тестирование

### Запуск всех тестов
```bash
pytest tests/ -v
```

### Тесты производительности
```bash
pytest tests/test_performance.py -v
```

### Ручное тестирование API
```bash
# Тест основного endpoint
curl -X POST "http://localhost:8000/api/predict" \
     -H "Content-Type: application/json" \
     -d '{"input": "молоко простоквашино 3.2%"}'

# Тест с пустым вводом
curl -X POST "http://localhost:8000/api/predict" \
     -H "Content-Type: application/json" \
     -d '{"input": ""}'

# Проверка здоровья
curl http://localhost:8000/health

# Метрики
curl http://localhost:8000/metrics
```

## Производительность

### Требования
- **Минимум 20 RPS** - система поддерживает более 20 запросов в секунду
- **Низкая задержка** - среднее время ответа < 50ms
- **Высокая доступность** - uptime > 99%

### Оптимизации
- Асинхронная обработка запросов
- Кеширование результатов предсказаний
- Батчинг для групповых запросов
- Предварительная загрузка модели
- Connection pooling и keep-alive

### Мониторинг
- Real-time метрики через `/metrics`
- Streamlit дашборд на порту 8501
- Логирование всех запросов
- Health checks каждые 30 секунд

## Конфигурация

### Переменные окружения
```bash
DEBUG=False                 # Режим отладки
LOG_LEVEL=INFO             # Уровень логирования
MODEL_PATH=/app/best_ner_model  # Путь к модели
MAX_WORKERS=4              # Количество worker'ов
BATCH_SIZE=32              # Размер батча
MAX_SEQUENCE_LENGTH=128    # Максимальная длина последовательности
DEVICE=cuda                # Устройство (cuda/cpu)
```

### Настройка модели
Файл `best_ner_model/config.json`:
```json
{
    "tag_to_id": {
        "O": 0,
        "B-BRAND": 1,
        "I-BRAND": 2,
        "B-TYPE": 3,
        "I-TYPE": 4,
        "B-VOLUME": 5,
        "I-VOLUME": 6,
        "B-PERCENT": 7,
        "I-PERCENT": 8
    },
    "model": "cointegrated/rubert-tiny2",
    "max_len": 128
}
```

## Структура проекта

```
ner-fastapi/
├── Dockerfile                 # Docker образ
├── docker-compose.yml         # Оркестрация сервисов
├── requirements.txt           # Python зависимости
├── nginx.conf                # Конфигурация Nginx
├── .env                      # Переменные окружения
├── app/
│   ├── main.py              # Главное FastAPI приложение
│   ├── core/
│   │   ├── config.py        # Конфигурация
│   │   └── logging.py       # Настройка логирования
│   ├── models/
│   │   ├── ner_model.py     # NER модель и обёртка
│   │   └── schemas.py       # Pydantic схемы
│   ├── services/
│   │   ├── prediction.py    # Сервис предсказаний
│   │   └── metrics.py       # Сбор метрик
│   ├── api/
│   │   └── routes.py        # API роуты
│   ├── monitoring/
│   │   ├── dashboard.py     # Streamlit дашборд
│   │   └── middleware.py    # Middleware для метрик
│   └── best_ner_model/      # Обученная модель
└── tests/
    ├── test_api.py          # Тесты API
    └── test_performance.py  # Тесты производительности
```

## Использование

### Основной API запрос
```python
import requests

response = requests.post(
    "http://localhost:8000/api/predict",
    json={"input": "молоко простоквашино 3.2%"}
)

entities = response.json()
print(entities)
```

### Батчевая обработка
```python
import requests

batch_requests = [
    {"input": "молоко"},
    {"input": "хлеб бородинский"},
    {"input": ""}
]

response = requests.post(
    "http://localhost:8000/api/predict/batch",
    json=batch_requests
)

results = response.json()
```

### Мониторинг через Python
```python
import requests

# Получение метрик
metrics = requests.get("http://localhost:8000/metrics").json()
print(f"RPS: {metrics['requests_per_second']}")
print(f"Время ответа: {metrics['average_response_time']}ms")

# Проверка здоровья
health = requests.get("http://localhost:8000/health").json()
print(f"Статус: {health['status']}")
```

## Дашборд

Streamlit дашборд доступен по адресу `http://localhost:8501` и предоставляет:

- **Real-time метрики** - RPS, время ответа, успешность запросов
- **Графики производительности** - динамика метрик во времени
- **Тестер API** - возможность отправлять тестовые запросы
- **Нагрузочное тестирование** - инструменты для проверки производительности
- **Статус системы** - информация о модели и сервисе

## Производственное развертывание

### Docker Swarm
```yaml
version: '3.8'
services:
  ner-api:
    image: ner-api:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ner-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: ner-api
        image: ner-api:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            cpu: 1000m
            memory: 2Gi
```

## Лицензия

MIT License

## Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f ner-api`
2. Убедитесь в наличии модели в `best_ner_model/`
3. Проверьте доступность портов 8000 и 8501
4. Запустите health check: `curl http://localhost:8000/health`