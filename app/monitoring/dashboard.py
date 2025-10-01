"""
Streamlit дашборд для мониторинга
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import time
import asyncio
from datetime import datetime, timedelta

# Конфигурация страницы
st.set_page_config(
    page_title="NER API Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Константы
API_BASE_URL = "http://localhost:8000"
REFRESH_INTERVAL = 2  # секунды

class Dashboard:
    """Главный класс дашборда"""
    
    def __init__(self):
        self.setup_session_state()
    
    def setup_session_state(self):
        """Инициализация состояния сессии"""
        if 'metrics_history' not in st.session_state:
            st.session_state.metrics_history = []
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()
    
    def fetch_metrics(self):
        """Получение метрик из API"""
        try:
            response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            st.error(f"Ошибка при получении метрик: {str(e)}")
        return None
    
    def fetch_health(self):
        """Получение информации о здоровье сервиса"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            st.error(f"Ошибка при получении статуса здоровья: {str(e)}")
        return None
    
    def test_prediction_api(self, text: str):
        """Тестирование API предсказаний"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/predict",
                json={"input": text},
                timeout=10
            )
            if response.status_code == 200:
                return response.json(), response.elapsed.total_seconds() * 1000
            else:
                return {"error": f"HTTP {response.status_code}"}, None
        except Exception as e:
            return {"error": str(e)}, None
    
    def render_header(self):
        """Отрисовка заголовка"""
        st.title("🤖 NER API Dashboard")
        st.markdown("---")
        
        # Информация о последнем обновлении
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**Последнее обновление:** {datetime.now().strftime('%H:%M:%S')}")
        with col3:
            if st.button("🔄 Обновить", type="primary"):
                st.rerun()
    
    def render_health_status(self):
        """Отрисовка статуса здоровья"""
        st.subheader("🏥 Статус сервиса")
        
        health_data = self.fetch_health()
        if health_data:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_color = "🟢" if health_data['status'] == 'healthy' else "🔴"
                st.metric("Статус", f"{status_color} {health_data['status'].upper()}")
            
            with col2:
                model_status = "✅" if health_data['model_loaded'] else "❌"
                st.metric("Модель", f"{model_status} {'Загружена' if health_data['model_loaded'] else 'Не загружена'}")
            
            with col3:
                device_icon = "🚀" if "cuda" in health_data['device'].lower() else "💻"
                st.metric("Устройство", f"{device_icon} {health_data['device']}")
    
    def render_metrics(self):
        """Отрисовка метрик производительности"""
        st.subheader("📊 Метрики производительности")
        
        metrics_data = self.fetch_metrics()
        if metrics_data:
            # Добавляем метрики в историю
            current_time = datetime.now()
            metrics_data['timestamp'] = current_time
            st.session_state.metrics_history.append(metrics_data)
            
            # Ограничиваем историю последними 100 записями
            if len(st.session_state.metrics_history) > 100:
                st.session_state.metrics_history = st.session_state.metrics_history[-100:]
            
            # Основные метрики
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Всего запросов", metrics_data['total_requests'])
            
            with col2:
                st.metric("RPS", f"{metrics_data['requests_per_second']:.1f}")
            
            with col3:
                st.metric("Среднее время (мс)", f"{metrics_data['average_response_time']:.1f}")
            
            with col4:
                success_rate = (
                    metrics_data['successful_requests'] / max(metrics_data['total_requests'], 1) * 100
                )
                st.metric("Успешность (%)", f"{success_rate:.1f}%")
            
            # Графики
            if len(st.session_state.metrics_history) > 1:
                self.render_performance_charts()
    
    def render_performance_charts(self):
        """Отрисовка графиков производительности"""
        df = pd.DataFrame(st.session_state.metrics_history)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # График RPS
            fig_rps = px.line(
                df, 
                x='timestamp', 
                y='requests_per_second',
                title='Запросы в секунду (RPS)',
                labels={'requests_per_second': 'RPS', 'timestamp': 'Время'}
            )
            fig_rps.update_layout(height=300)
            st.plotly_chart(fig_rps, use_container_width=True)
        
        with col2:
            # График времени ответа
            fig_time = px.line(
                df, 
                x='timestamp', 
                y='average_response_time',
                title='Среднее время ответа (мс)',
                labels={'average_response_time': 'Время (мс)', 'timestamp': 'Время'}
            )
            fig_time.update_layout(height=300)
            st.plotly_chart(fig_time, use_container_width=True)
        
        # График ошибок
        if 'error_rate' in df.columns:
            fig_errors = px.bar(
                df.tail(20), 
                x='timestamp', 
                y=['successful_requests', 'failed_requests'],
                title='Успешные vs Неуспешные запросы',
                labels={'value': 'Количество', 'timestamp': 'Время'}
            )
            fig_errors.update_layout(height=300)
            st.plotly_chart(fig_errors, use_container_width=True)
    
    def render_api_tester(self):
        """Отрисовка тестера API"""
        st.subheader("🧪 Тестирование API")
        
        with st.form("api_test_form"):
            test_input = st.text_area(
                "Введите текст для тестирования:",
                value="сгущенное молоко",
                height=100
            )
            submit_button = st.form_submit_button("Отправить запрос", type="primary")
        
        if submit_button and test_input:
            with st.spinner("Выполняется запрос..."):
                result, response_time = self.test_prediction_api(test_input)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if 'error' not in result:
                    st.success("✅ Запрос успешен!")
                    st.json(result)
                else:
                    st.error(f"❌ Ошибка: {result['error']}")
            
            with col2:
                if response_time:
                    st.metric("Время ответа", f"{response_time:.1f} мс")
    
    def render_load_testing(self):
        """Отрисовка инструментов нагрузочного тестирования"""
        st.subheader("⚡ Нагрузочное тестирование")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            num_requests = st.number_input("Количество запросов", min_value=1, max_value=100, value=10)
        
        with col2:
            concurrent_requests = st.number_input("Параллельных запросов", min_value=1, max_value=20, value=5)
        
        with col3:
            test_text = st.text_input("Текст для тестирования", value="молоко простоквашино")
        
        if st.button("🚀 Запустить нагрузочный тест", type="primary"):
            progress_bar = st.progress(0)
            results_placeholder = st.empty()
            
            # Имитация нагрузочного тестирования
            response_times = []
            errors = 0
            
            for i in range(num_requests):
                result, response_time = self.test_prediction_api(test_text)
                
                if response_time:
                    response_times.append(response_time)
                else:
                    errors += 1
                
                progress_bar.progress((i + 1) / num_requests)
                
                # Обновляем результаты в реальном времени
                if response_times:
                    avg_time = sum(response_times) / len(response_times)
                    min_time = min(response_times)
                    max_time = max(response_times)
                    
                    results_placeholder.metric(
                        f"Прогресс: {i+1}/{num_requests}",
                        f"Среднее время: {avg_time:.1f}мс | Ошибки: {errors}"
                    )
            
            # Финальные результаты
            if response_times:
                st.success(f"✅ Тест завершен! Среднее время: {sum(response_times)/len(response_times):.1f}мс")
                
                # График результатов
                fig = px.histogram(
                    x=response_times,
                    nbins=20,
                    title="Распределение времени ответа"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def run(self):
        """Запуск дашборда"""
        self.render_header()
        
        # Боковая панель с настройками
        with st.sidebar:
            st.header("⚙️ Настройки")
            auto_refresh = st.checkbox("Автообновление", value=True)
            
            if auto_refresh:
                refresh_rate = st.slider("Интервал обновления (сек)", 1, 10, 2)
                # Автообновление страницы
                time.sleep(refresh_rate)
                st.rerun()
            
            st.markdown("---")
            st.markdown("### 📋 Информация")
            st.markdown(f"**API URL:** {API_BASE_URL}")
            st.markdown(f"**Версия:** 1.0.0")
        
        # Основной контент
        self.render_health_status()
        st.markdown("---")
        self.render_metrics()
        st.markdown("---")
        self.render_api_tester()
        st.markdown("---")
        self.render_load_testing()

# Запуск дашборда
if __name__ == "__main__":
    dashboard = Dashboard()
    dashboard.run()