"""NER (Named Entity Recognition) analyzer using Natasha"""
import re
from typing import Dict, List, Set, Any
from natasha import (
    Segmenter,
    NewsEmbedding,
    NewsNERTagger,
    Doc,
    PER,  # Персона
    ORG   # Организация
)
from src.core.logging_config import log


class NERAnalyzer:
    """
    Анализатор именованных сущностей для извлечения компаний и персон из текста новостей
    """
    
    # Организации, которые НЕ считаем коммерческими компаниями
    EXCLUDED_ORGS = {
        # Государственные органы
        'ВСУ', 'Минобороны', 'ПВО', 'МЧС', 'МВД', 'ФСБ', 'СК',
        'Госдума', 'Совет Федерации', 'Правительство', 'Администрация',
        'Минфин', 'Минэкономразвития', 'Роскомнадзор',
        'Генпрокуратура', 'Следственный комитет', 'Минтруд', 'Минздрав',
        'Минобрнауки', 'Минкульт', 'Минпромторг', 'ФАС', 'Росстат',
        'Роспотребнадзор', 'Минцифры', 'Минэнерго', 'Минтранс',
        
        # Военные и силовые структуры
        'Армия', 'Флот', 'ВКС', 'ВМФ', 'Росгвардия', 'ФСО', 'СВР',
        
        # Общие термины
        'Министерство', 'Федеральная', 'Региональная', 'Муниципальная',
        'Департамент', 'Комитет', 'Агентство', 'Служба', 'Управление',
        'Отдел', 'Центр', 'Институт',
        
        # Образовательные учреждения
        'Академия', 'Университет', 'Школа', 'Лицей', 'Колледж',
        'Техникум', 'НИУ ВШЭ', 'МГУ', 'СПбГУ', 'МФТИ',
        
        # Медицинские
        'Больница', 'Поликлиника', 'Клиника', 'Аптека',
        
        # Розничные и общественные места
        'Магазин', 'Супермаркет', 'Ресторан', 'Кафе', 'Бар',
        'Отель', 'Гостиница', 'Хостел', 'Кинотеатр', 'Театр',
        
        # СМИ и соцсети
        'РБК', 'ТАСС', 'Telegram', 'FT', 'Reuters', 'Bloomberg',
        'WhatsApp', 'VK', 'ВКонтакте', 'Одноклассники', 'YouTube',
        
        # Геополитические
        'ООН', 'НАТО', 'ЕС', 'СНГ', 'ЕАЭС', 'БРИКС', 'G7', 'G20',
        'МВФ', 'ВТО', 'ВОЗ', 'ОБСЕ', 'ОПЕК',
    }
    
    # Шаблоны для очистки текста от футеров РБК
    RBC_FOOTER_PATTERNS = [
        r'РБК в Telegram На связи с проверенными новостями.*?(?=РБК|$)',
        r'FT: Трамп поручил подготовиться.*?(?=РБК|$)',
        r'Читайте РБК в Telegram!.*?(?=РБК|$)',
        r'Подпишись на Telegram РБК.*?(?=РБК|$)',
        r'Больше новостей в телеграм-канале.*?(?=РБК|$)',
        r'Оперативные новости и важная информация.*?(?=РБК|$)',
        r'Аналитика, мнения, лонгриды.*?(?=РБК|$)',
    ]
    
    def __init__(self):
        """Инициализация компонентов Natasha"""
        try:
            log.info("Initializing Natasha NER components...")
            self.segmenter = Segmenter()
            self.emb = NewsEmbedding()
            self.ner_tagger = NewsNERTagger(self.emb)
            log.info("Natasha NER initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize Natasha NER: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """Очищает текст от шаблонных футеров РБК и лишних символов"""
        if not text:
            return text
        
        cleaned = str(text)
        
        # Удаляем футеры РБК
        for pattern in self.RBC_FOOTER_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
        
        # Удаляем множественные пробелы и переносы строк
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Извлекает компании и персоны из текста
        
        Returns:
            {
                'companies': ['Компания 1', 'Компания 2', ...],
                'people': ['Персона 1', 'Персона 2', ...],
                'companies_count': int,
                'people_count': int
            }
        """
        if not text or not text.strip():
            return {
                'companies': [],
                'people': [],
                'companies_count': 0,
                'people_count': 0
            }
        
        try:
            # Очищаем текст
            cleaned_text = self.clean_text(text)
            
            # Создаем документ
            doc = Doc(cleaned_text)
            
            # Сегментация
            doc.segment(self.segmenter)
            
            # NER тегирование
            doc.tag_ner(self.ner_tagger)
            
            # Извлекаем сущности
            companies: Set[str] = set()
            people: Set[str] = set()
            
            for span in doc.spans:
                if span.type == PER:
                    # Персона
                    people.add(span.text)
                elif span.type == ORG:
                    # Организация - фильтруем
                    if span.text not in self.EXCLUDED_ORGS:
                        companies.add(span.text)
            
            # Сортируем для консистентности
            companies_list = sorted(list(companies))
            people_list = sorted(list(people))
            
            result = {
                'companies': companies_list,
                'people': people_list,
                'companies_count': len(companies_list),
                'people_count': len(people_list)
            }
            
            if companies_list or people_list:
                log.debug(
                    f"Extracted {len(companies_list)} companies and "
                    f"{len(people_list)} people from text (len={len(cleaned_text)})"
                )
            
            return result
            
        except Exception as e:
            log.error(f"Error extracting entities: {e}")
            return {
                'companies': [],
                'people': [],
                'companies_count': 0,
                'people_count': 0
            }
    
    def analyze_article(
        self,
        title: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Анализирует статью (title + content) и извлекает сущности
        
        Returns:
            {
                'companies': List[str],
                'people': List[str],
                'companies_count': int,
                'people_count': int,
                'companies_str': str,  # Строка для БД: "Компания1; Компания2"
                'people_str': str      # Строка для БД: "Персона1; Персона2"
            }
        """
        # Объединяем заголовок и контент
        full_text = f"{title}\n\n{content}".strip()
        
        # Извлекаем сущности
        entities = self.extract_entities(full_text)
        
        # Добавляем строковые представления для БД
        entities['companies_str'] = '; '.join(entities['companies']) if entities['companies'] else ''
        entities['people_str'] = '; '.join(entities['people']) if entities['people'] else ''
        
        return entities


# Singleton instance
_ner_analyzer_instance = None


def get_ner_analyzer() -> NERAnalyzer:
    """Получить singleton экземпляр NER анализатора"""
    global _ner_analyzer_instance
    if _ner_analyzer_instance is None:
        _ner_analyzer_instance = NERAnalyzer()
    return _ner_analyzer_instance

