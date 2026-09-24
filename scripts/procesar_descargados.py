"""
Procesa archivos ya descargados en DOWNLOAD_BASE_PATH/<instancia>/ sin consultar la BD ni el file server.
Uso (desde la raíz del proyecto):
    python -m scripts.procesar_descargados            # todas las carpetas de instancia
    python -m scripts.procesar_descargados 817681     # solo esas instancias
"""
import sys
from pathlib import Path
from config.logging_config import setup_logging
from config.settings import settings
from extraction.ocr_extractor import EXTENSIONES_IMAGEN
from pipeline.orchestrator import procesar_instancia

EXTENSIONES_SOPORTADAS = {".pdf", ".docx"} | EXTENSIONES_IMAGEN

def main():
    setup_logging()
    base = Path(settings.DOWNLOAD_BASE_PATH)

    if len(sys.argv) > 1:
        carpetas = [base / arg for arg in sys.argv[1:]]
    else:
        carpetas = sorted(p for p in base.iterdir() if p.is_dir() and p.name.isdigit())

    for carpeta in carpetas:
        if not carpeta.is_dir():
            print(f"No existe la carpeta {carpeta}, se omite")
            continue
        archivos = [
            (ruta, None) for ruta in sorted(carpeta.iterdir())
            if ruta.suffix.lower() in EXTENSIONES_SOPORTADAS
        ]
        procesar_instancia(int(carpeta.name), archivos)

if __name__ == "__main__":
    main()
