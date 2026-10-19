import logging
from pathlib import Path
from classification.rule_classifier import detectar_tipos, resumir_instancia
from extraction import get_extractor
from extraction.base_extractor import BaseExtractor
from extraction.cul_parser import extraer_cul, ruc_empleador_actual
from models.document import ResultadoExtraccion
from storage.cul_writer import guardar_cul_json
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

def procesar_instancia(
    instancia: int,
    archivos: list[tuple[Path, str | None]],
    extractor: BaseExtractor | None = None,
    periodo: str | None = None,
) -> dict[str, bool]:
    """
    archivos: lista de (ruta_local, nombre_original).
    Extrae texto, guarda el .log/.json, detecta SUNAFIL/CUL/BOLETA y registra la fila en el Excel.
    Si hay un CUL, además registra su identidad y experiencia laboral en el mismo Excel.
    Pasar el extractor permite reutilizarlo entre instancias (evita recargar el motor/modelo).
    """
    extractor = extractor or get_extractor()
    resultados = [extractor.procesar(ruta, nombre) for ruta, nombre in archivos]

    ruta_log, ruta_json = escribir_extraccion(str(instancia), resultados)
    tipos = resumir_instancia(resultados)
    culs = extraer_culs(resultados)
    ruc_cul = ruc_empleador_actual(culs)
    ruta_xlsx = registrar_instancia(instancia, tipos, periodo, ruc_cul)

    print(f"\nInstancia {instancia}: " + " | ".join(f"{t}: {'SI' if v else 'NO'}" for t, v in tipos.items())
          + f" | RUC_CUL: {ruc_cul or '-'}")
    for cul in culs:
        ident = cul["identidad"]
        registros = cul["experiencia_laboral"]["registros"]
        print(f"  CUL {cul['archivo']}: {ident.get('nombres')} {ident.get('apellidos')} "
              f"(doc {ident.get('numero_documento')}) - {len(registros)} empleador(es)")
        for reg in registros:
            print(f"      {reg['ruc']} {reg['razon_social']}: {reg['desde']} -> {reg['hasta']}")
        print(f"      JSON: {cul['ruta_json']}")
    print(f"  Log:   {ruta_log}\n  JSON:  {ruta_json}\n  Excel: {ruta_xlsx}")
    return tipos
