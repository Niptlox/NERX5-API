"""
Конфигурация приложения
"""
import os
from typing import Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    debug: bool = False
    log_level: str = "INFO"
    model_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model_weights")
    base_model_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cointegrated/rubert-tiny2")
    # base_model_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model_weights/bert")

    # model_path: str = "app/best_ner_model"

    max_workers: int = 4
    batch_size: int = 32
    max_sequence_length: int = 128
    device: str = "cuda"
    prometheus_port: int = 8001
    streamlit_port: int = 8501
    api_port: int = 8000
    
    # Тэги NER модели
    tag_to_id: Dict[str, int] = {
        'O': 0,
        'B-BRAND': 1,
        'I-BRAND': 2,
        'B-TYPE': 3,
        'I-TYPE': 4,
        'B-VOLUME': 5,
        'I-VOLUME': 6,
        'B-PERCENT': 7,
        'I-PERCENT': 8,
        '0': 9
    }
    

    @property
    def id_to_tag(self) -> Dict[int, str]:
        return {v: k for k, v in self.tag_to_id.items()}
    
    class Config:
        env_file = ".env"

settings = Settings()