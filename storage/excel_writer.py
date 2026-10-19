from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from config.settings import settings
from classification.rule_classifier import PALABRAS_CLAVE

HOJA_VALIDACION = "Validacion"
ENCABEZADOS = ["instancia", *PALABRAS_CLAVE, "RUC_CUL"]

def _ruta_excel(periodo: str | None) -> Path:
    ruta = Path(settings.RESULTADOS_DIR) / f"validacion_{periodo or 'sin_periodo'}.xlsx"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta

def _abrir_libro(ruta: Path) -> Workbook:
    if ruta.exists():
        return load_workbook(ruta)
    wb = Workbook()
    wb.active.title = HOJA_VALIDACION
    wb.active.append(ENCABEZADOS)
    return wb

def _hoja(wb: Workbook, nombre: str, encabezados: list[str]) -> Worksheet:
    """Devuelve la hoja por nombre (no wb.active, que cambia si alguien guarda el Excel en otra pestaña)."""
    if nombre in wb.sheetnames:
        return wb[nombre]
    ws = wb.create_sheet(nombre)
    ws.append(encabezados)
    return ws

def _guardar(wb: Workbook, ruta: Path) -> None:
    try:
        wb.save(ruta)
    except PermissionError:
        raise PermissionError(f"No se pudo guardar {ruta}: ciérralo en Excel y vuelve a ejecutar") from None

def registrar_instancia(
    instancia: int, tipos: dict[str, bool], periodo: str | None = None, ruc_cul: str | None = None
) -> Path:
    """
    Agrega (o actualiza, si ya existe) la fila de la instancia en el Excel del periodo
    (<RESULTADOS_DIR>/validacion_<periodo>.xlsx):
    instancia | SUNAFIL | CUL | BOLETA  con valores SI / NO
              | RUC_CUL  RUC del empleador vigente según el CUL (ver cul_parser.ruc_empleador_actual)
    """
    ruta = _ruta_excel(periodo)
    wb = _abrir_libro(ruta)
    ws = _hoja(wb, HOJA_VALIDACION, ENCABEZADOS)
    for col, encabezado in enumerate(ENCABEZADOS, start=1):  # Excel de corridas anteriores sin RUC_CUL
        ws.cell(1, col).value = encabezado

    fila = [instancia, *("SI" if tipos[t] else "NO" for t in PALABRAS_CLAVE), ruc_cul]

    for row in ws.iter_rows(min_row=2):
        if row[0].value == instancia:
            for celda, valor in zip(row, fila):
                celda.value = valor
            break
    else:
        ws.append(fila)

    _guardar(wb, ruta)
    return ruta
