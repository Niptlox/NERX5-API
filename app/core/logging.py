"""
Настройка логирования
"""
import logging
import sys
from typing import Optional

def setup_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    format_str: Optional[str] = None
) -> logging.Logger:
    """
    Настройка логгера с форматированием
    """
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(format_str))        
        logger.addHandler(handler)
        file_handller=logging.FileHandler("app.log")
        file_handller.setFormatter(logging.Formatter(format_str))        
        file_handller.setLevel(logging.WARNING)
        logger.addHandler(file_handller)
        logger.setLevel(getattr(logging, level.upper()))
        # Save log
    
    return logger

# Основной логгер приложения
app_logger = setup_logger("ner_api")
model_logger = setup_logger("ner_model")
metrics_logger = setup_logger("metrics")