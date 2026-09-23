from pathlib import Path
from config.settings import settings
from db.queries import get_archivos_por_instancia
from file_access.name_filter import es_archivo_excluido

def construir_ruta_completa(ruta_relativa: str, guid: str, extension: str) -> Path:
    extension = extension.lstrip(".")
    nombre_archivo = f"{guid}.{extension}"
    return Path(settings.FILE_SERVER_BASE_PATH) / ruta_relativa.strip("/\\") / nombre_archivo

def listar_archivos_cliente(instancia: int) -> list[dict]:
    registros = get_archivos_por_instancia(instancia)
    resultado = []

    for reg in registros:
        if es_archivo_excluido(reg["nombre_original"]):
            continue

        ruta_completa = construir_ruta_completa(
            reg["ruta_relativa"], reg["guid"], reg["extension"]
        )
        resultado.append({
            "ruta": ruta_completa,
            "existe": ruta_completa.exists(),
            "guid": reg["guid"],
            "extension": reg["extension"],
            "nombre_original": reg["nombre_original"],
        })

    return resultado
