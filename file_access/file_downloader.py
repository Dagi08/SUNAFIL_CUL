import shutil
import logging
from pathlib import Path
from config.settings import settings

logger = logging.getLogger(__name__)

def obtener_carpeta_destino(instancia: int, periodo: str | None = None) -> Path:
    """documentos/<periodo>/<instancia>/ dentro del proyecto (documentos/<instancia>/ si no hay periodo)."""
    base = Path(settings.DOWNLOAD_BASE_PATH)
    carpeta = (base / periodo if periodo else base) / str(instancia)
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta

def descargar_archivos(instancia: int, archivos: list[dict], periodo: str | None = None) -> list[dict]:
    carpeta_destino = obtener_carpeta_destino(instancia, periodo)
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

def borrar_archivos(rutas: list[Path]) -> list[Path]:
    """
    Borra copias locales ya procesadas (el original sigue en el file server).
    Por seguridad solo borra dentro de DOWNLOAD_BASE_PATH. Si la carpeta de la instancia queda vacía, también la borra.
    """
    base = Path(settings.DOWNLOAD_BASE_PATH).resolve()
    borrados = []
    for ruta in rutas:
        ruta = Path(ruta).resolve()
        if not ruta.is_relative_to(base) or not ruta.is_file():
            continue
        try:
            ruta.unlink()
            borrados.append(ruta)
            logger.info(f"Borrado (sin CUL ni SUNAFIL): {ruta}")
        except OSError as e:
            logger.warning(f"No se pudo borrar {ruta}: {e}")
    for carpeta in {r.parent for r in borrados}:
        if carpeta != base and not any(carpeta.iterdir()):
            carpeta.rmdir()
    return borrados
