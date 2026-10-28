"""
Procesa archivos ya descargados en DOWNLOAD_BASE_PATH/<periodo>/<instancia>/ sin consultar la BD ni el file server.
También acepta la estructura anterior DOWNLOAD_BASE_PATH/<instancia>/ (sin periodo).
Igual que main.py, al terminar borra los archivos que no tienen CUL ni SUNAFIL.
Uso (desde la raíz del proyecto):
    python -m scripts.procesar_descargados            # todas las carpetas de instancia
    python -m scripts.procesar_descargados 817681     # solo esas instancias (en cualquier periodo)
"""
import re
import sys
from pathlib import Path
from config.logging_config import setup_logging
from config.settings import settings
from extraction.ocr_extractor import EXTENSIONES_IMAGEN
from pipeline.orchestrator import procesar_instancia

EXTENSIONES_SOPORTADAS = {".pdf", ".docx"} | EXTENSIONES_IMAGEN
RE_PERIODO = re.compile(r"\d{4}(0[1-9]|1[0-2])")

def _subcarpetas_numericas(carpeta: Path) -> list[Path]:
    return sorted(p for p in carpeta.iterdir() if p.is_dir() and p.name.isdigit())

def _carpetas_instancia(base: Path) -> list[tuple[Path, str | None]]:
    """
    (carpeta, periodo) de cada instancia: <base>/<periodo>/<instancia> o <base>/<instancia>.
    Num_Sol y periodo pueden tener ambos 6 dígitos: una carpeta es de periodo si tiene formato YYYYMM
    y contiene subcarpetas de instancia (una de instancia contiene archivos).
    """
    carpetas = []
    for carpeta in _subcarpetas_numericas(base):
        instancias = _subcarpetas_numericas(carpeta)
        if RE_PERIODO.fullmatch(carpeta.name) and instancias:
            carpetas += [(c, carpeta.name) for c in instancias]
        else:
            carpetas.append((carpeta, None))
    return carpetas

def main():
    setup_logging()
    carpetas = _carpetas_instancia(Path(settings.DOWNLOAD_BASE_PATH))
    if len(sys.argv) > 1:
        carpetas = [(c, p) for c, p in carpetas if c.name in sys.argv[1:]]
    if not carpetas:
        print("No se encontraron carpetas de instancia para procesar")

    for carpeta, periodo in carpetas:
        archivos = [
            (ruta, None) for ruta in sorted(carpeta.iterdir())
            if ruta.suffix.lower() in EXTENSIONES_SOPORTADAS
        ]
        procesar_instancia(int(carpeta.name), archivos, periodo=periodo)

if __name__ == "__main__":
    main()
