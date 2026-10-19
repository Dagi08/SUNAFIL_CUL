"""
Flujo completo por periodo:
  1. Consulta en BD Negocio las solicitudes del periodo (Num_Sol = instancia)
  Por cada instancia:
  2. Consulta en BD Riesgo los archivos de la instancia y filtra por nombre los que no se validan
  3. Arma la ruta de cada archivo en el file server
  4. Copia los archivos a DOWNLOAD_BASE_PATH/<instancia>/
  5. Extrae texto (OCR), guarda .log/.json y registra en resultados/validacion_<periodo>.xlsx los campos de la
     solicitud + SUNAFIL | CUL | BOLETA (una fila por solicitud, aunque no tenga archivos)
  6. Si hay un CUL, extrae IDENTIDAD y EXPERIENCIA LABORAL: el RUC del empleador vigente va a la columna RUC_CUL
     del Excel y el detalle completo a documentos/<instancia>/<archivo>.json (junto al PDF)

Uso:
    python main.py 202607
    python main.py 202607 --limite 5      # solo las primeras 5 solicitudes (para pruebas)
"""
import argparse
import logging
import re
import sys
from pathlib import Path
from classification.rule_classifier import PALABRAS_CLAVE
from config.logging_config import setup_logging
from db.queries import get_archivos_por_instancia, get_solicitudes_por_periodo
from extraction import get_extractor
from extraction.base_extractor import BaseExtractor
from extraction.cul_parser import OBS_REGULARIZAR
from file_access.name_filter import es_archivo_excluido
from file_access.file_locator import listar_archivos_cliente
from file_access.file_downloader import descargar_archivos
from pipeline.orchestrator import procesar_instancia
from storage.excel_writer import registrar_instancia

logger = logging.getLogger(__name__)

def obtener_solicitudes(periodo: str) -> list[dict]:
    """Una solicitud por Num_Sol (la primera que devuelve la query), en el orden de la query."""
    solicitudes = {}
    for s in get_solicitudes_por_periodo(periodo):
        solicitudes.setdefault(int(s["Num_Sol"]), s)
    return list(solicitudes.values())

def registrar_sin_documentos(solicitud: dict, periodo: str) -> None:
    """La solicitud igual queda en el Excel, con SUNAFIL / CUL / BOLETA en NO."""
    registrar_instancia(solicitud, {t: False for t in PALABRAS_CLAVE}, periodo, observacion=OBS_REGULARIZAR)

def ejecutar_instancia(solicitud: dict, periodo: str, extractor: BaseExtractor) -> dict[str, bool] | None:
    instancia = int(solicitud["Num_Sol"])
    print(f"\n{'=' * 70}\nINSTANCIA {instancia}\n{'=' * 70}")

    # 2. Archivos de la instancia + filtro por nombre
    registros = get_archivos_por_instancia(instancia)
    if not registros:
        print("No hay registros de archivos en BD para esta instancia")
        registrar_sin_documentos(solicitud, periodo)
        return None

    excluidos = [r for r in registros if es_archivo_excluido(r["nombre_original"])]
    print(f"[1/4] Registros en BD: {len(registros)} | Excluidos por nombre: {len(excluidos)}")
    for r in excluidos:
        print(f"        - {r['nombre_original']}")

    # 3. Rutas en file server (solo los no excluidos)
    archivos = listar_archivos_cliente(instancia, registros)
    if not archivos:
        print("No quedaron archivos por procesar")
        registrar_sin_documentos(solicitud, periodo)
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
        registrar_sin_documentos(solicitud, periodo)
        return None

    # 5. OCR + clasificación + Excel
    print(f"[4/4] Extrayendo texto de {len(copiados)} archivos...")
    return procesar_instancia(instancia, copiados, extractor, periodo, solicitud)

def main():
    parser = argparse.ArgumentParser(description="Valida SUNAFIL / CUL / BOLETA de las solicitudes de un periodo")
    parser.add_argument("periodo", help="Cod_Mes en formato YYYYMM, ej. 202607")
    parser.add_argument("--limite", type=int, help="procesar solo las primeras N solicitudes")
    args = parser.parse_args()

    if not re.fullmatch(r"\d{4}(0[1-9]|1[0-2])", args.periodo):
        parser.error(f"periodo inválido '{args.periodo}', se espera YYYYMM (ej. 202607)")

    setup_logging()

    # 1. Solicitudes del periodo
    solicitudes = obtener_solicitudes(args.periodo)
    if args.limite:
        solicitudes = solicitudes[:args.limite]
    print(f"Periodo {args.periodo}: {len(solicitudes)} solicitudes a procesar")
    if not solicitudes:
        return

    extractor = get_extractor()  # se crea una sola vez para todas las instancias

    fallidas = []
    for n, solicitud in enumerate(solicitudes, start=1):
        print(f"\n({n}/{len(solicitudes)})", end="")
        try:
            ejecutar_instancia(solicitud, args.periodo, extractor)
        except Exception as e:
            instancia = int(solicitud["Num_Sol"])
            logger.exception(f"Error procesando la instancia {instancia}: {e}")
            fallidas.append(instancia)

    print(f"\nProcesadas: {len(solicitudes) - len(fallidas)}/{len(solicitudes)}")
    if fallidas:
        print(f"Con error (ver logs/app.log): {fallidas}")
        sys.exit(1)

if __name__ == "__main__":
    main()
