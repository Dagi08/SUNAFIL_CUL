from datetime import datetime
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet
from config.settings import settings
from classification.rule_classifier import PALABRAS_CLAVE, observacion
from db.queries import COLUMNAS_SOLICITUD

HOJA_VALIDACION = "Validacion"
# Datos de la solicitud (query del periodo) + resultado de la validación de documentos
COLUMNAS_SUNAFIL = ["RUC_SUNAFIL", "FECHA_INGRESO_SUNAFIL", "FECHA_VERIFICACION_SUNAFIL"]
ENCABEZADOS = [*COLUMNAS_SOLICITUD, *PALABRAS_CLAVE, "RUC_CUL", *COLUMNAS_SUNAFIL, "OBSERVACION", "MENSAJE"]
COL_NUM_SOL = COLUMNAS_SOLICITUD.index("Num_Sol")  # clave de la fila: Num_Sol = instancia
COLS_FECHA_SUNAFIL = [ENCABEZADOS.index(c) for c in COLUMNAS_SUNAFIL[1:]]
FORMATO_FECHA = "dd/mm/yyyy"

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

def _a_fecha(texto: str | None):
    """'17/02/2025' -> fecha de Excel (si no se puede leer, se deja el texto tal cual)."""
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except (TypeError, ValueError):
        return texto

def registrar_instancia(
    solicitud: dict,
    tipos: dict[str, bool],
    periodo: str | None = None,
    ruc_cul: str | None = None,
    mensaje: str | None = None,
    sunafil: dict | None = None,
) -> Path:
    """
    Agrega (o actualiza, si ya existe) la fila de la solicitud en el Excel del periodo
    (<RESULTADOS_DIR>/validacion_<periodo>.xlsx):
    Cod_Mes | Num_Sol | ... | Ape_Mat   datos de la solicitud (db.queries.COLUMNAS_SOLICITUD)
    | SUNAFIL | CUL | BOLETA            SI / NO
    | RUC_CUL | MENSAJE                 comparación de Ruc_Emp con el CUL (ver cul_parser.validar_ruc)
    | RUC_SUNAFIL | FECHA_INGRESO_SUNAFIL | FECHA_VERIFICACION_SUNAFIL   constancia SUNAFIL (ver sunafil_parser)
    | OBSERVACION                       OK si tiene CUL, SUNAFIL o boleta de pensión militar/policial
                                      (ver rule_classifier.observacion)
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
        sunafil and sunafil["ruc"],
        _a_fecha(sunafil and sunafil["fecha_ingreso"]),
        _a_fecha(sunafil and sunafil["fecha_verificacion"]),
        observacion(tipos),
        mensaje,
    ]

    for row in ws.iter_rows(min_row=2):
        if row[COL_NUM_SOL].value == num_sol:
            for celda, valor in zip(row, fila):
                celda.value = valor
            break
    else:
        ws.append(fila)
        row = ws[ws.max_row]
    for col in COLS_FECHA_SUNAFIL:
        row[col].number_format = FORMATO_FECHA

    _guardar(wb, ruta)
    return ruta
