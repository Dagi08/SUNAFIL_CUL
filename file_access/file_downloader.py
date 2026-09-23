import shutil
import logging
from pathlib import Path
from config.settings import settings

logger = logging.getLogger(__name__)

def obtener_carpeta_destino(instancia: int) -> Path:
    """documentos/<instancia>/ dentro del proyecto."""
    carpeta = Path(settings.DOWNLOAD_BASE_PATH) / str(instancia)
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta

def descargar_archivos(instancia: int, archivos: list[dict]) -> list[dict]:
    carpeta_destino = obtener_carpeta_destino(instancia)
    resultado = []

    for archivo in archivos:
        ruta_origen = archivo["ruta"]
        entrada = dict(archivo)

        if not archivo["existe"]:
            entrada["ruta_local"] = None
            entrada["copiado"] = False
            logger.warning(f"No existe en file server, se omite: {ruta_origen}")
            resultado.append(entrada)
            continue

        nombre_archivo = f"{archivo['guid']}.{archivo['extension'].lstrip('.')}"
        ruta_local = carpeta_destino / nombre_archivo

        try:
            shutil.copy2(ruta_origen, ruta_local)
            entrada["ruta_local"] = ruta_local
            entrada["copiado"] = True
            logger.info(f"Copiado: {ruta_origen} -> {ruta_local}")
        except Exception as e:
            entrada["ruta_local"] = None
            entrada["copiado"] = False
            logger.error(f"Error copiando {ruta_origen}: {e}")

        resultado.append(entrada)

    return resultado
