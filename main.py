"""
Flujo completo por periodo:
  1. Consulta en BD Negocio las solicitudes del periodo (Num_Sol = instancia)
  Por cada instancia:
  2. Consulta en BD Riesgo los archivos de la instancia y filtra por nombre los que no se validan
  3. Arma la ruta de cada archivo en el file server
  4. Copia los archivos a DOWNLOAD_BASE_PATH/<instancia>/
  5. Extrae texto (OCR), guarda .log/.json y registra SUNAFIL | CUL | BOLETA en resultados/validacion_<periodo>.xlsx

Uso:
    python main.py 202607
    python main.py 202607 --limite 5      # solo las primeras 5 solicitudes (para pruebas)
"""
import argparse
import logging
import re
import sys
from pathlib import Path
from config.logging_config import setup_logging
from db.queries import get_archivos_por_instancia, get_solicitudes_por_periodo
from extraction import get_extractor
from extraction.base_extractor import BaseExtractor
from file_access.name_filter import es_archivo_excluido
from file_access.file_locator import listar_archivos_cliente
from file_access.file_downloader import descargar_archivos
from pipeline.orchestrator import procesar_instancia

logger = logging.getLogger(__name__)

def obtener_instancias(periodo: str) -> list[int]:
    """Num_Sol únicos del periodo, en el orden que devuelve la query."""
    solicitudes = get_solicitudes_por_periodo(periodo)
    return list(dict.fromkeys(int(s["Num_Sol"]) for s in solicitudes))

def ejecutar_instancia(instancia: int, periodo: str, extractor: BaseExtractor) -> dict[str, bool] | None:
    print(f"\n{'=' * 70}\nINSTANCIA {instancia}\n{'=' * 70}")

    # 2. Archivos de la instancia + filtro por nombre
    registros = get_archivos_por_instancia(instancia)
    if not registros:
        print("No hay registros de archivos en BD para esta instancia")
        return None

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
    return procesar_instancia(instancia, copiados, extractor, periodo)

def main():
    parser = argparse.ArgumentParser(description="Valida SUNAFIL / CUL / BOLETA de las solicitudes de un periodo")
    parser.add_argument("periodo", help="Cod_Mes en formato YYYYMM, ej. 202607")
    parser.add_argument("--limite", type=int, help="procesar solo las primeras N solicitudes")
    args = parser.parse_args()

    if not re.fullmatch(r"\d{4}(0[1-9]|1[0-2])", args.periodo):
        parser.error(f"periodo inválido '{args.periodo}', se espera YYYYMM (ej. 202607)")

    setup_logging()

    # 1. Instancias del periodo
    instancias = obtener_instancias(args.periodo)
    if args.limite:
        instancias = instancias[:args.limite]
    print(f"Periodo {args.periodo}: {len(instancias)} solicitudes a procesar")
    if not instancias:
        return

    extractor = get_extractor()  # se crea una sola vez para todas las instancias

    fallidas = []
    for n, instancia in enumerate(instancias, start=1):
        print(f"\n({n}/{len(instancias)})", end="")
        try:
            ejecutar_instancia(instancia, args.periodo, extractor)
        except Exception as e:
            logger.exception(f"Error procesando la instancia {instancia}: {e}")
            fallidas.append(instancia)

    print(f"\nProcesadas: {len(instancias) - len(fallidas)}/{len(instancias)}")
    if fallidas:
        print(f"Con error (ver logs/app.log): {fallidas}")
        sys.exit(1)

if __name__ == "__main__":
    main()
