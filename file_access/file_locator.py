from pathlib import Path
from config.settings import settings
from db.queries import get_archivos_por_instancia

def construir_ruta_completa(ruta_relativa: str, guid: str, extension: str) -> Path:
    """
    Arma: <base>/<Ruta_Relativa_FileSystem>/<Nombre_Fisico_GUID>.<Extension>
    """
    extension = extension.lstrip(".")
    nombre_archivo = f"{guid}.{extension}"
    return Path(settings.FILE_SERVER_BASE_PATH) / ruta_relativa.strip("/\\") / nombre_archivo

def listar_archivos_cliente(instancia: int) -> list[dict]:
    """
    Devuelve lista de dicts: {"ruta": Path, "existe": bool, "guid": str, "extension": str}
    """
    registros = get_archivos_por_instancia(instancia)
    resultado = []

    for reg in registros:
        ruta_completa = construir_ruta_completa(
            reg["ruta_relativa"], reg["guid"], reg["extension"]
        )
        resultado.append({
            "ruta": ruta_completa,
            "existe": ruta_completa.exists(),
            "guid": reg["guid"],
            "extension": reg["extension"],
        })

    return resultado
