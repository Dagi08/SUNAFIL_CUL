"""
Flujo completo por instancia:
  1. Consulta en BD los archivos de la instancia
  2. Filtra por nombre los documentos que no se validan
  3. Arma la ruta de cada archivo en el file server
  4. Copia los archivos a DOWNLOAD_BASE_PATH/<instancia>/
  5. Extrae texto (OCR), guarda .log/.json y registra SUNAFIL | CUL | BOLETA en el .xlsx

Uso:
    python main.py 817681
    python main.py 817681 817682 817683
"""
import logging
import sys
from pathlib import Path
from config.logging_config import setup_logging
from db.queries import get_archivos_por_instancia
from extraction import get_extractor
from extraction.base_extractor import BaseExtractor
from file_access.name_filter import es_archivo_excluido
from file_access.file_locator import listar_archivos_cliente
from file_access.file_downloader import descargar_archivos
from pipeline.orchestrator import procesar_instancia

logger = logging.getLogger(__name__)

def ejecutar_instancia(instancia: int, extractor: BaseExtractor) -> dict[str, bool] | None:
    print(f"\n{'=' * 70}\nINSTANCIA {instancia}\n{'=' * 70}")

    # 1. Consulta en BD
    registros = get_archivos_por_instancia(instancia)
    if not registros:
        print("No hay registros en BD para esta instancia")
        return None

    # 2. Filtro por nombre
    excluidos = [r for r in registros if es_archivo_excluido(r["nombre_original"])]
    print(f"[1/4] Registros en BD: {len(registros)} | Excluidos por nombre: {len(excluidos)}")
    for r in excluidos:
        print(f"        - {r['nombre_original']}")

    # 3. Rutas en file server (solo los no excluidos)
    archivos = listar_archivos_cliente(instancia, registros)
    if not archivos:
        print("No quedaron archivos por procesar")
        return None
    print(f"[2/4] Rutas generadas: {len(archivos)} (existen: {sum(a['existe'] for a in archivos)})")

    # 4. Copia local
    descargados = descargar_archivos(instancia, archivos)
    print(f"[3/4] Descarga:")
    for a in descargados:
        estado = "COPIADO" if a["copiado"] else "FALLÓ/NO EXISTE"
        print(f"        [{estado}] {a['nombre_original']} -> {a.get('ruta_local') or a['ruta']}")

    copiados = [(Path(a["ruta_local"]), a["nombre_original"]) for a in descargados if a["copiado"]]
    if not copiados:
        print("No se copió ningún archivo, no hay nada que extraer")
        return None

    # 5. OCR + clasificación + Excel
    print(f"[4/4] Extrayendo texto de {len(copiados)} archivos...")
    return procesar_instancia(instancia, copiados, extractor)

def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <instancia> [<instancia> ...]")
        sys.exit(1)

    setup_logging()
    instancias = [int(arg) for arg in sys.argv[1:]]
    extractor = get_extractor()  # se crea una sola vez para todas las instancias

    fallidas = []
    for instancia in instancias:
        try:
            ejecutar_instancia(instancia, extractor)
        except Exception as e:
            logger.exception(f"Error procesando la instancia {instancia}: {e}")
            fallidas.append(instancia)

    print(f"\nProcesadas: {len(instancias) - len(fallidas)}/{len(instancias)}")
    if fallidas:
        print(f"Con error (ver logs/app.log): {fallidas}")
        sys.exit(1)

if __name__ == "__main__":
    main()
