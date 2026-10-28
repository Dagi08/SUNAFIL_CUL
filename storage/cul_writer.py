import json
from pathlib import Path

def guardar_json(datos: dict, ruta_archivo: Path, sufijo: str = "") -> Path:
    """Guarda lo extraído junto al archivo de origen: documentos/<instancia>/<archivo><sufijo>.json"""
    ruta = Path(ruta_archivo).with_name(f"{Path(ruta_archivo).stem}{sufijo}.json")
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta

def guardar_cul_json(cul: dict, ruta_pdf: Path) -> Path:
    """documentos/<instancia>/<archivo>.json"""
    return guardar_json(cul, ruta_pdf)

def guardar_sunafil_json(sunafil: dict, ruta_archivo: Path) -> Path:
    """documentos/<instancia>/<archivo>_sunafil.json (un mismo PDF puede traer CUL y SUNAFIL)"""
    return guardar_json(sunafil, ruta_archivo, "_sunafil")
