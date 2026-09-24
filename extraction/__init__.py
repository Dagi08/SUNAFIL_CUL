from config.settings import settings
from extraction.base_extractor import BaseExtractor

def get_extractor() -> BaseExtractor:
    """Devuelve el motor de extracción configurado en OCR_ENGINE."""
    if settings.OCR_ENGINE == "donut":
        from extraction.donut_extractor import DonutExtractor
        return DonutExtractor()
    from extraction.ocr_extractor import OcrExtractor
    return OcrExtractor()
