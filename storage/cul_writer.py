import json
from pathlib import Path

def guardar_cul_json(cul: dict, ruta_pdf: Path) -> Path:
    """Guarda lo extraído del CUL junto al PDF: documentos/<instancia>/<archivo>.json"""
    ruta = Path(ruta_pdf).with_suffix(".json")
    ruta.write_text(json.dumps(cul, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta
