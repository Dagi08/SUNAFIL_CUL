import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from config.settings import settings
from models.document import ResultadoExtraccion

def escribir_extraccion(identificador: str, resultados: list[ResultadoExtraccion]) -> tuple[Path, Path]:
    """
    Guarda lo extraído en logs/extraccion/:
      - <id>_<fecha>.log  → legible, para revisar cómo sale el texto por página
      - <id>_<fecha>.json → estructurado, entrada para la futura clasificación
    """
    carpeta = Path(settings.LOG_DIR) / "extraccion"
    carpeta.mkdir(parents=True, exist_ok=True)
    base = carpeta / f"{identificador}_{datetime.now():%Y%m%d_%H%M%S}"

    lineas = []
    for r in resultados:
        lineas.append("=" * 80)
        lineas.append(f"ARCHIVO: {r.nombre_original or Path(r.archivo).name}")
        lineas.append(f"RUTA:    {r.archivo}")
        if r.error:
            lineas.append(f"ERROR:   {r.error}")
        for p in r.paginas:
            lineas.append(f"--- PÁGINA {p.numero} ({p.metodo}, {len(p.texto)} caracteres) ---")
            lineas.append(p.texto or "<sin texto>")
        lineas.append("")

    ruta_log = base.with_suffix(".log")
    ruta_json = base.with_suffix(".json")
    ruta_log.write_text("\n".join(lineas), encoding="utf-8")
    ruta_json.write_text(
        json.dumps([asdict(r) for r in resultados], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return ruta_log, ruta_json
