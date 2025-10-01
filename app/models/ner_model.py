"""
NER модель - загрузка и обёртка для предсказаний
"""
import os
import json
import asyncio
import torch
import torch.nn as nn
from typing import List, Tuple, Dict, Any
from transformers import AutoModelForTokenClassification, AutoTokenizer, AutoConfig, AutoModel
from ..core.config import settings
from ..core.logging import model_logger

class NERModel(nn.Module):
    """NER модель на основе BERT"""
    
    def __init__(self, model_name: str, num_tags: int, dropout: float = 0.3):
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        self.layer_norm = nn.LayerNorm(self.bert.config.hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_tags)
        
        # Инициализация весов
        nn.init.xavier_uniform_(self.classifier.weight)
        nn.init.zeros_(self.classifier.bias)
    
    def forward(self, input_ids, attention_mask, labels=None, **kwargs):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state
        
        sequence_output = self.layer_norm(sequence_output)
        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)
        
        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss(ignore_index=-100)
            loss = loss_fct(logits.view(-1, logits.shape[-1]), labels.view(-1))
        
        return {'loss': loss, 'logits': logits}

class NERModelWrapper:
    """Обёртка для загруженной модели NER"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.config = None
        self.device = None
        self._lock = asyncio.Lock()
        
        
    async def load_model(self, model_path: str = None) -> bool:
        """Асинхронная загрузка модели"""
        async with self._lock:
            try:
                model_logger.info("Загрузка модели...")                                

                # model_path = r"D:\PythonProjects\!AI\NER-X5TECH-MSK-25\NER-fastapi-service\app\model_weights"
                
                if model_path is None:
                    model_path = settings.model_path  

                with open(model_path+"/config.json", "r", encoding="utf-8") as f:
                    self.saved = json.load(f)
                tag_to_id = self.saved["tag_to_id"]
                id_to_tag = self.saved["id_to_tag"]
                num_labels = len(tag_to_id)

                # Загружаем базовую конфигурацию предобученной модели и обновляем для задачи NER
                # base_model_name = self.saved.get("model", "")
                # base_model_path = r"D:\PythonProjects\!AI\NER-X5TECH-MSK-25\NER-fastapi-service\app\model_weights\bert"
                base_model_name = settings.base_model_path
                config = AutoConfig.from_pretrained(
                    base_model_name,
                    num_labels=num_labels,
                    id2label=id_to_tag,
                    label2id=tag_to_id
                )

                # Загружаем токенизатор и модель весов
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForTokenClassification.from_pretrained(
                    model_path,
                    config=config,
                    trust_remote_code=False
                )
                

                # Переносим на устройство и в режим оценки
                print(f"{torch.cuda.is_available()=}")
                self.device = settings.device if torch.cuda.is_available() and settings.device == "cuda" else "cpu"
                self.model.to(self.device)
                self.model.eval()

            
                model_logger.info(f"Модель успешно загружена на {self.device}")
                return True
                
            except Exception as e:
                model_logger.error(f"Ошибка при загрузке модели: {str(e)}")
                return False
    
    def _clean_bio_tags(self, tags: List[str]) -> List[str]:
        """Очистка BIO тегов"""
        cleaned = []
        prev = 'O'
        for tag in tags:
            if tag.startswith('I-') and not prev.endswith(tag[2:]):
                tag = 'B-' + tag[2:]
            cleaned.append(tag)

            prev = tag
        return cleaned
    
    def _convert_predictions_to_entities(self, text: str, tags: List[str]) -> List[Dict[str, Any]]:
        """Конвертация тегов в сущности с позициями"""
        entities = []
        words = text.split()
        
        current_entity = None
        char_pos = 0
        
        for i, (word, tag) in enumerate(zip(words, tags)):
            word_start = text.find(word, char_pos)
            word_end = word_start + len(word)
            
            if tag.startswith('B-'):
                # Начало новой сущности
                if current_entity:
                    entities.append(current_entity)
                
                current_entity = {
                    'start_index': word_start,
                    'end_index': word_end,
                    'entity': tag
                }
            
            elif tag.startswith('I-') and current_entity:
                # Продолжение сущности
                current_entity['end_index'] = word_end
                current_entity['entity'] = tag
            
            elif tag == 'O':
                # Конец сущности
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
            
            char_pos = word_end + 1  # +1 для пробела
        
        # Добавляем последнюю сущность если есть
        if current_entity:
            entities.append(current_entity)
        
        return entities
    
    async def predict(self, text: str) -> List[Dict[str, Any]]:
        """Асинхронное предсказание сущностей"""
        if not text.strip():
            return []
        
        if not self.model or not self.tokenizer:
            raise RuntimeError("Модель не загружена")
        
        try:
            # words = text.split()
            # if not words:
            #     return []
            
            # # Токенизация
            # encoding = self.tokenizer(
            #     words,
            #     is_split_into_words=True,
            #     padding="max_length",
            #     truncation=True,
            #     max_length=settings.max_sequence_length,
            #     return_tensors="pt"
            # )
            
            # # Перенос на устройство
            # device_encoding = {k: v.to(self.device) for k, v in encoding.items()}
            
            # # Предсказание
            # with torch.no_grad():
            #     outputs = self.model(**device_encoding)
            #     logits = outputs['logits']
            
            # # Получение предсказаний
            # predictions = logits.argmax(dim=-1)[0].cpu().tolist()
            # word_ids = encoding.word_ids(batch_index=0)
            
            # # Маппинг предсказаний на слова
            # result_tags = []
            # prev_word_idx = None
            
            # for token_idx, word_idx in enumerate(word_ids):
            #     if word_idx is not None and word_idx != prev_word_idx:
            #         pred_id = predictions[token_idx]
            #         tag = self.config['id_to_tag'][str(pred_id)]
            #         result_tags.append(tag)
            #         prev_word_idx = word_idx

            id_to_tag = self.saved["id_to_tag"]
            max_length=self.saved.get("max_len", 128)

            words = text.split()    
            enc = self.tokenizer(
                words,
                is_split_into_words=True,
                padding="max_length",
                truncation=True,
                max_length=max_length,
                return_tensors="pt"
            ).to(self.device)

            with torch.no_grad():
                logits = self.model(**enc).logits

            preds = logits.argmax(dim=-1)[0].cpu().tolist()
            word_ids = enc.word_ids(batch_index=0)

            result_tags = []
            result = []
            prev_widx = None
            for idx, widx in enumerate(word_ids):
                if widx is not None and widx != prev_widx:
                    tag = id_to_tag[str(preds[idx])] if isinstance(list(id_to_tag.keys())[0], str) else id_to_tag[preds[idx]]
                    token = words[widx]
                    result.append((token, tag))
                    prev_widx = widx
                    result_tags.append(tag)
            

            # Очистка BIO тегов
            result_tags = self._clean_bio_tags(result_tags)
            
            # model_logger.info(f"result {result} {result_tags}")
            # Конвертация в формат API
            # entities = self._convert_predictions_to_entities(text, result_tags)
            
            return self.format_annotation(text, result_tags)
            
        except Exception as e:
            model_logger.error(f"Ошибка при предсказании: {str(e)}")
            raise
    
    def is_loaded(self) -> bool:
        """Проверка загружена ли модель"""
        return self.model is not None and self.tokenizer is not None
    
    @staticmethod
    def format_annotation(text, tagged_output):        
        ann = []
        idx = 0
        for token, tag in zip(text.split(), tagged_output):
            length = len(token)        
            if tag:
                current_entity = {
                    'start_index': idx,
                    'end_index': idx + length,
                    'entity': tag
                }
                ann.append(current_entity)
            idx += length + 1  # +1 на разделитель пробела

        return ann

# Глобальный экземпляр модели
ner_model = NERModelWrapper()