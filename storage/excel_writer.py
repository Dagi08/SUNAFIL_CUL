from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from config.settings import settings
from classification.rule_classifier import PALABRAS_CLAVE
from db.queries import COLUMNAS_SOLICITUD

HOJA_VALIDACION = "Validacion"
# Datos de la solicitud (query del periodo) + resultado de la validación de documentos
ENCABEZADOS = [*COLUMNAS_SOLICITUD, *PALABRAS_CLAVE, "RUC_CUL", "OBSERVACION"]
COL_NUM_SOL = COLUMNAS_SOLICITUD.index("Num_Sol")  # clave de la fila: Num_Sol = instancia

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
    solicitud: dict,
    tipos: dict[str, bool],
    periodo: str | None = None,
    ruc_cul: str | None = None,
    observacion: str | None = None,
) -> Path:
    """
    Agrega (o actualiza, si ya existe) la fila de la solicitud en el Excel del periodo
    (<RESULTADOS_DIR>/validacion_<periodo>.xlsx):
    Cod_Mes | Num_Sol | ... | Ape_Mat   datos de la solicitud (db.queries.COLUMNAS_SOLICITUD)
    | SUNAFIL | CUL | BOLETA            SI / NO
    | RUC_CUL | OBSERVACION             comparación de Ruc_Emp con el CUL (ver cul_parser.validar_ruc)
    """
    ruta = _ruta_excel(periodo)
    wb = _abrir_libro(ruta)
    ws = _hoja(wb, HOJA_VALIDACION, ENCABEZADOS)

    encabezados_actuales = [c.value for c in ws[1]]
    if encabezados_actuales != ENCABEZADOS:
        raise ValueError(
            f"{ruta} tiene columnas de una versión anterior ({encabezados_actuales}): "
            "renómbralo o elimínalo y vuelve a ejecutar"
        )

    num_sol = int(solicitud["Num_Sol"])
    fila = [
        *(num_sol if col == "Num_Sol" else solicitud.get(col) for col in COLUMNAS_SOLICITUD),
        *("SI" if tipos[t] else "NO" for t in PALABRAS_CLAVE),
        ruc_cul,
        observacion,
    ]

    for row in ws.iter_rows(min_row=2):
        if row[COL_NUM_SOL].value == num_sol:
            for celda, valor in zip(row, fila):
                celda.value = valor
            break
    else:
        ws.append(fila)

    _guardar(wb, ruta)
    return ruta
