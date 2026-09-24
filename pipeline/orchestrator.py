from pathlib import Path
from classification.rule_classifier import resumir_instancia
from extraction import get_extractor
from extraction.base_extractor import BaseExtractor
from storage.excel_writer import registrar_instancia
from storage.log_writer import escribir_extraccion

def procesar_instancia(
    instancia: int,
    archivos: list[tuple[Path, str | None]],
    extractor: BaseExtractor | None = None,
    periodo: str | None = None,
) -> dict[str, bool]:
    """
    archivos: lista de (ruta_local, nombre_original).
    Extrae texto, guarda el .log/.json, detecta SUNAFIL/CUL/BOLETA y registra la fila en el Excel.
    Pasar el extractor permite reutilizarlo entre instancias (evita recargar el motor/modelo).
    """
    extractor = extractor or get_extractor()
    resultados = [extractor.procesar(ruta, nombre) for ruta, nombre in archivos]

    ruta_log, ruta_json = escribir_extraccion(str(instancia), resultados)
    tipos = resumir_instancia(resultados)
    ruta_xlsx = registrar_instancia(instancia, tipos, periodo)

    print(f"\nInstancia {instancia}: " + " | ".join(f"{t}: {'SI' if v else 'NO'}" for t, v in tipos.items()))
    print(f"  Log:   {ruta_log}\n  JSON:  {ruta_json}\n  Excel: {ruta_xlsx}")
    return tipos
