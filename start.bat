@echo off
REM ===== NER FastAPI Windows launcher =====
chcp 65001 > nul

echo 🚀  Запуск NER-системы…

REM --- Проверка Docker ---
where docker > nul 2>&1
if errorlevel 1 (
    echo ❌  Docker не найден! Установите Docker Desktop.
    pause & exit /b 1
)

where docker-compose > nul 2>&1
if errorlevel 1 (
    echo ❌  Docker Compose не найден! Установите Docker Desktop.
    pause & exit /b 1
)

REM --- Проверка модели ---
if not exist "app\best_ner_model\config.json" (
    echo ❌  Модель не найдена. Скопируйте файлы в best_ner_model\
    pause & exit /b 1
)

REM --- Сборка и запуск ---
echo 🏗️  Сборка контейнеров…
docker-compose down
docker-compose build --no-cache
echo 🔥  Запуск сервисов…
docker-compose up -d

REM --- Ожидание readiness ---
echo ⏳  Ожидание запуска API…
for /l %%i in (1,1,30) do (
    powershell -Command "try { iwr http://localhost:8000/health -UseBasicParsing -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }"
    if not errorlevel 1 goto :ready
    timeout /t 2 > nul
)
echo ❌  API не ответил за 60 с.
docker-compose logs ner-api
pause & exit /b 1

:ready
echo ✅  API запущен!

REM --- Быстрый smoke-тест ---
echo 🧪  Тест запроса…
powershell -Command "$r = iwr http://localhost:8000/api/predict -Method POST -Body '{\"input\":\"сгущенное молоко\"}' -ContentType 'application/json' -UseBasicParsing; $r.Content"
echo 🎉  Система готова!

echo ---------------------------
echo API URL:        http://localhost:8000
echo Документация:   http://localhost:8000/docs
echo Дашборд:        http://localhost:8501
echo ---------------------------
pause
