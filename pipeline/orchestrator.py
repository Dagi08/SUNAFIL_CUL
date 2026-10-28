import logging
from pathlib import Path
from classification.rule_classifier import detectar_tipos, observacion, resumir_instancia
from extraction import get_extractor
from extraction.base_extractor import BaseExtractor
from extraction.cul_parser import extraer_cul, validar_ruc
from extraction.sunafil_parser import extraer_sunafil
from file_access.file_downloader import borrar_archivos
from models.document import ResultadoExtraccion
from storage.cul_writer import guardar_cul_json, guardar_sunafil_json
from storage.excel_writer import registrar_instancia
from storage.log_writer import escribir_extraccion

logger = logging.getLogger(__name__)

def extraer_culs(resultados: list[ResultadoExtraccion]) -> list[dict]:
    """
    Identidad y experiencia laboral de cada archivo detectado como CUL (solo PDF con texto nativo).
    Cada CUL se guarda además como <archivo>.json en la misma carpeta del PDF.
    """
    culs = []
    for r in resultados:
        if "CUL" not in detectar_tipos(r) or Path(r.archivo).suffix.lower() != ".pdf":
            continue
        try:
            cul = extraer_cul(Path(r.archivo))
            cul["nombre_original"] = r.nombre_original
            cul["ruta_json"] = str(guardar_cul_json(cul, Path(r.archivo)))
            culs.append(cul)
        except Exception as e:
            # p.ej. un CUL escaneado: el clasificador lo detecta por OCR, pero no tiene texto nativo que parsear
            logger.warning(f"No se pudo extraer el CUL de {r.nombre_original or r.archivo}: {e}")
    return culs

def archivos_sin_cul_ni_sunafil(resultados: list[ResultadoExtraccion]) -> list[Path]:
    """
    Archivos que no contienen CUL ni SUNAFIL. Los que dieron error al extraer no se incluyen:
    no se sabe qué tienen, así que se conservan para revisarlos.
    """
    return [
        Path(r.archivo) for r in resultados
        if not r.error and not ({"CUL", "SUNAFIL"} & detectar_tipos(r))
    ]

def procesar_instancia(
    instancia: int,
    archivos: list[tuple[Path, str | None]],
    extractor: BaseExtractor | None = None,
    periodo: str | None = None,
    solicitud: dict | None = None,
) -> dict[str, bool]:
    """
    archivos: lista de (ruta_local, nombre_original).
    solicitud: fila de la query del periodo; sus campos van al Excel junto con el resultado.
    Extrae texto, guarda el .log/.json, detecta SUNAFIL/CUL/BOLETA y registra la fila en el Excel.
    Los datos del CUL y de SUNAFIL se guardan en JSON junto a su archivo; al final se borran las copias
    locales de los archivos que no tienen CUL ni SUNAFIL.
    Pasar el extractor permite reutilizarlo entre instancias (evita recargar el motor/modelo).
    """
    extractor = extractor or get_extractor()
    resultados = [extractor.procesar(ruta, nombre) for ruta, nombre in archivos]

    ruta_log, ruta_json = escribir_extraccion(str(instancia), resultados, periodo)
    tipos = resumir_instancia(resultados)
    culs = extraer_culs(resultados)
    solicitud = solicitud or {"Num_Sol": instancia}
    ruc_cul, mensaje = validar_ruc(culs, solicitud.get("Ruc_Emp"))
    sunafil = extraer_sunafil(resultados)
    if sunafil:
        sunafil["ruta_json"] = str(guardar_sunafil_json(sunafil, Path(sunafil["archivo"])))
    ruta_xlsx = registrar_instancia(solicitud, tipos, periodo, ruc_cul, mensaje, sunafil)
    borrados = borrar_archivos(archivos_sin_cul_ni_sunafil(resultados))

    print(f"\nInstancia {instancia}: " + " | ".join(f"{t}: {'SI' if v else 'NO'}" for t, v in tipos.items())
          + f" | Ruc_Emp: {solicitud.get('Ruc_Emp') or '-'} | RUC_CUL: {ruc_cul or '-'}"
          + f" | {observacion(tipos)}" + (f" | {mensaje}" if mensaje else ""))
    if sunafil:
        print(f"  SUNAFIL {Path(sunafil['archivo']).name} (pág. {sunafil['pagina']}): RUC {sunafil['ruc'] or '-'} | "
              f"Ingreso {sunafil['fecha_ingreso'] or '-'} | Verificación {sunafil['fecha_verificacion'] or '-'}")
        print(f"      JSON: {sunafil['ruta_json']}")
    for cul in culs:
        ident = cul["identidad"]
        registros = cul["experiencia_laboral"]["registros"]
        print(f"  CUL {cul['archivo']}: {ident.get('nombres')} {ident.get('apellidos')} "
              f"(doc {ident.get('numero_documento')}) - {len(registros)} empleador(es)")
        for reg in registros:
            print(f"      {reg['ruc']} {reg['razon_social']}: {reg['desde']} -> {reg['hasta']}")
        print(f"      JSON: {cul['ruta_json']}")
    if borrados:
        print(f"  Borrados {len(borrados)} archivo(s) sin CUL ni SUNAFIL (el texto queda en el log de extracción)")
    print(f"  Log:   {ruta_log}\n  JSON:  {ruta_json}\n  Excel: {ruta_xlsx}")
    return tipos
