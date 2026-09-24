import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(Path.cwd() / ".env")

def _resolver_tesseract_cmd(ruta: str | None) -> str | None:
    """Acepta la carpeta de instalación o la ruta directa al tesseract.exe."""
    if not ruta:
        return None
    ruta = Path(ruta)
    return str(ruta / "tesseract.exe") if ruta.suffix.lower() != ".exe" else str(ruta)

class Settings:
    DB_NAME = os.getenv("DB_NAME")
    DB_ENGINE = os.getenv("DB_ENGINE")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_DRIVER = os.getenv("DB_DRIVER")
    DB_EXTRA_PARAMS = os.getenv("DB_EXTRA_PARAMS", "")

    # BD de Negocio: solicitudes del periodo (Num_Sol = instancia)
    NEGOCIO_DB_HOST = os.getenv("NEGOCIO_DB_HOST", r"SRVJADBANLT01\SQL01DBA2019")
    NEGOCIO_DB_NAME = os.getenv("NEGOCIO_DB_NAME", "Negocio")

    FILE_SERVER_BASE_PATH = os.getenv("FILE_SERVER_BASE_PATH")
    DOWNLOAD_BASE_PATH = os.getenv("DOWNLOAD_BASE_PATH", "documentos")

    FILE_SERVER_TIMEOUT_SECONDS = int(os.getenv("FILE_SERVER_TIMEOUT_SECONDS", 30))

    # OCR / Extracción
    OCR_ENGINE = os.getenv("OCR_ENGINE", "pytesseract")
    TESSERACT_CMD = _resolver_tesseract_cmd(os.getenv("PATH_TESSERACT"))
    OCR_LANG = os.getenv("OCR_LANG", "spa")
    PDF_DPI = int(os.getenv("PDF_DPI", 300))
    # Si una página PDF tiene menos caracteres de texto nativo que esto, se le aplica OCR
    MIN_CHARS_TEXTO_NATIVO = int(os.getenv("MIN_CHARS_TEXTO_NATIVO", 30))
    # Si el OCR de la página completa da menos que esto, se reintenta con las fotos incrustadas
    MIN_CHARS_OCR_PAGINA = int(os.getenv("MIN_CHARS_OCR_PAGINA", 200))

    # Resultado de la clasificación: <RESULTADOS_DIR>/validacion_<periodo>.xlsx
    RESULTADOS_DIR = os.getenv("RESULTADOS_DIR", "resultados")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = os.getenv("LOG_DIR", "logs")

settings = Settings()
