FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY app/ ./app/
COPY .env .

# Создание директории для модели
RUN mkdir -p /app/best_ner_model

# Копирование модели (если есть в локальной директории)
COPY best_ner_model/ ./best_ner_model/

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app_user
RUN chown -R app_user:app_user /app
USER app_user

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Открытие портов
EXPOSE 8000 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда запуска
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]