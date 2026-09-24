"""
Prueba el OCR sin pasar por la BD ni el file server.
Uso (desde la raíz del proyecto):
    python -m scripts.test_ocr documentos/CUL.pdf
    python -m scripts.test_ocr documentos
"""
import sys
from pathlib import Path
from config.logging_config import setup_logging
from extraction import get_extractor
from extraction.ocr_extractor import EXTENSIONES_IMAGEN
from storage.log_writer import escribir_extraccion

EXTENSIONES_SOPORTADAS = {".pdf", ".docx"} | EXTENSIONES_IMAGEN

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m scripts.test_ocr <archivo_o_carpeta>")
        sys.exit(1)

    setup_logging()
    objetivo = Path(sys.argv[1])
    if objetivo.is_dir():
        rutas = sorted(p for p in objetivo.iterdir() if p.suffix.lower() in EXTENSIONES_SOPORTADAS)
    else:
        rutas = [objetivo]

    extractor = get_extractor()
    resultados = [extractor.procesar(ruta) for ruta in rutas]
    ruta_log, ruta_json = escribir_extraccion(objetivo.stem or "prueba", resultados)
    print(f"\nExtracción guardada en:\n  {ruta_log}\n  {ruta_json}")

if __name__ == "__main__":
    main()
