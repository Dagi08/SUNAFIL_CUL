import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(Path.cwd() / ".env")

class Settings:
    DB_NAME = os.getenv("DB_NAME")
    DB_ENGINE = os.getenv("DB_ENGINE")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_DRIVER = os.getenv("DB_DRIVER")
    DB_EXTRA_PARAMS = os.getenv("DB_EXTRA_PARAMS", "")
    FILE_SERVER_BASE_PATH = os.getenv("FILE_SERVER_BASE_PATH")
    DOWNLOAD_BASE_PATH = os.getenv("DOWNLOAD_BASE_PATH", "documentos")

    FILE_SERVER_TIMEOUT_SECONDS = int(os.getenv("FILE_SERVER_TIMEOUT_SECONDS", 30))

settings = Settings()
