"""
Parser del Certificado Único Laboral (CUL) emitido por el MTPE.

Solo se extraen dos apartados:
  - IDENTIDAD: Fuente - RENIEC
  - EXPERIENCIA LABORAL: Fuente - Planillas Electrónicas

El CUL es un PDF digital (texto nativo), pero el orden del texto no sigue el orden visual
(las etiquetas y sus valores salen separados), por eso se trabaja con las coordenadas de cada línea:
  - Identidad: etiqueta a la izquierda, ":" y valor a la derecha en la misma fila.
  - Experiencia laboral: tabla con columnas Ruc | Razón Social | Desde | Hasta, que va desde su
    encabezado hasta la siguiente sección (o hasta CONSIDERACIONES si es la última).
"""
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pymupdf

TITULO_CUL = "CERTIFICADO ÚNICO LABORAL"
FIN_CONTENIDO = "CONSIDERACIONES:"  # desde aquí empieza el texto legal fijo (página 2)
TOLERANCIA_FILA = 4                 # puntos de diferencia en Y para considerar dos líneas en la misma fila
X_VALOR_IDENTIDAD = 165             # los valores de identidad empiezan a la derecha del ":"
TAMANO_MIN_FUENTE = 5               # descarta el sello de firma digital (fuente 4.3)
Y_PIE_PAGINA = 770                  # descarta el párrafo legal del pie de página

RE_SECCION = re.compile(r"^\s*(?P<titulo>.+?):\s*Fuente\s*[-–]\s*(?P<fuente>.+)$")
RE_RUC = re.compile(r"^\d{11}$")
SIN_FECHA_BAJA = "no ha registrado información"  # texto de 'Hasta' cuando el empleador sigue vigente

CAMPOS_IDENTIDAD = {
    "Nombres": "nombres",
    "Apellidos": "apellidos",
    "Nacionalidad (PAÍS)": "nacionalidad",
    "Tipo de documento": "tipo_documento",
    "N° de documento": "numero_documento",
    "Fecha de nacimiento": "fecha_nacimiento",
    "Domicilio": "domicilio",
}

@dataclass
class Linea:
    pagina: int
    x0: float
    y0: float
    texto: str

    @property
    def y_global(self) -> float:
        """Permite ordenar líneas de varias páginas como si fueran una sola."""
        return self.pagina * 10_000 + self.y0

def _leer_lineas(pdf: pymupdf.Document) -> list[Linea]:
    lineas = []
    for page in pdf:
        for bloque in page.get_text("dict")["blocks"]:
            for linea in bloque.get("lines", []):
                spans = linea["spans"]
                texto = "".join(s["text"] for s in spans).strip()
                if not texto or spans[0]["size"] < TAMANO_MIN_FUENTE:
                    continue
                x0, y0, *_ = linea["bbox"]
                lineas.append(Linea(page.number, x0, y0, texto))
    return sorted(lineas, key=lambda l: (l.y_global, l.x0))

def _misma_fila(a: Linea, b: Linea) -> bool:
    return a.pagina == b.pagina and abs(a.y0 - b.y0) <= TOLERANCIA_FILA

def _extraer_identidad(lineas: list[Linea]) -> dict:
    identidad = {}
    for etiqueta in (l for l in lineas if l.pagina == 0 and l.texto in CAMPOS_IDENTIDAD):
        valores = [l.texto for l in lineas if _misma_fila(l, etiqueta) and l.x0 >= X_VALOR_IDENTIDAD]
        identidad[CAMPOS_IDENTIDAD[etiqueta.texto]] = " ".join(valores) or None
    return identidad

def _dividir_secciones(lineas: list[Linea]) -> list[tuple[str, str, list[Linea]]]:
    """Agrupa las líneas del cuerpo en (titulo, fuente, contenido) hasta llegar a CONSIDERACIONES."""
    secciones = []
    for linea in lineas:
        if linea.texto.startswith(FIN_CONTENIDO):
            break
        if linea.y0 >= Y_PIE_PAGINA:
            continue
        if m := RE_SECCION.match(linea.texto):
            secciones.append((m["titulo"].strip(), m["fuente"].strip(), []))
        elif secciones:
            secciones[-1][2].append(linea)
    return secciones

def _extraer_experiencia(contenido: list[Linea]) -> list[dict]:
    """Arma la tabla Ruc | Razón Social | Desde | Hasta usando la posición X de los encabezados."""
    encabezados = {l.texto: l.x0 for l in contenido if l.texto in ("Ruc", "Razón Social", "Desde", "Hasta")}
    if len(encabezados) < 4:
        return []
    columnas = sorted(
        [("ruc", encabezados["Ruc"]), ("razon_social", encabezados["Razón Social"]),
         ("desde", encabezados["Desde"]), ("hasta", encabezados["Hasta"])],
        key=lambda c: c[1],
    )

    def columna_de(linea: Linea) -> str:
        nombre = columnas[0][0]
        for col, x in columnas:
            if linea.x0 >= x - 5:
                nombre = col
        return nombre

    # Cada RUC abre una fila; el resto de celdas va a la fila del RUC más cercano por encima
    # (con tolerancia, porque una celda puede quedar unas décimas más arriba que su RUC).
    rucs = [l for l in contenido if columna_de(l) == "ruc" and RE_RUC.match(l.texto)]
    filas = [{"ruc": l.texto, "razon_social": "", "desde": "", "hasta": ""} for l in rucs]
    for linea in contenido:
        if linea.texto in encabezados or linea in rucs:
            continue
        indices = [i for i, r in enumerate(rucs) if r.y_global <= linea.y_global + TOLERANCIA_FILA]
        if not indices:
            continue
        fila, col = filas[indices[-1]], columna_de(linea)
        # Celdas que ocupan varias líneas (p.ej. "El empleador no ha / registrado información.")
        fila[col] = f"{fila[col]} {linea.texto}".strip()
    return [{k: (v or None) for k, v in fila.items()} for fila in filas]

def _sin_fecha_baja(registro: dict) -> bool:
    """El empleador sigue vigente: 'Hasta' dice 'El empleador no ha registrado información.'"""
    return SIN_FECHA_BAJA in (registro.get("hasta") or "").lower()

def _fecha(texto: str | None) -> datetime:
    try:
        return datetime.strptime(texto or "", "%d/%m/%Y")
    except ValueError:
        return datetime.max  # sin fecha válida: queda al final al buscar el más antiguo

def ruc_empleador_actual(culs: list[dict]) -> str | None:
    """
    RUC del registro de experiencia laboral sin fecha de baja; si hay varios, el de 'Desde' más antiguo.
    Si todos tienen fecha de baja, el del primer registro de la tabla (el CUL lista primero el más reciente).
    None si el CUL no tiene experiencia laboral.
    """
    registros = [reg for cul in culs for reg in cul["experiencia_laboral"]["registros"]]
    vigentes = [reg for reg in registros if _sin_fecha_baja(reg)]
    if vigentes:
        return min(vigentes, key=lambda reg: _fecha(reg["desde"]))["ruc"]
    return registros[0]["ruc"] if registros else None

def extraer_cul(ruta: Path) -> dict:
    """Devuelve identidad y experiencia laboral de un CUL. Lanza ValueError si el PDF no es un CUL."""
    with pymupdf.open(ruta) as pdf:
        lineas = _leer_lineas(pdf)

    if not any(l.texto == TITULO_CUL for l in lineas):
        raise ValueError(f"{Path(ruta).name} no parece un Certificado Único Laboral (CUL)")

    resultado = {
        "archivo": Path(ruta).name,
        "identidad": _extraer_identidad(lineas),
        "experiencia_laboral": {"fuente": None, "registros": []},
    }
    # Las demás secciones (antecedentes, trayectoria educativa, ...) solo sirven para delimitar
    # dónde termina la tabla de experiencia laboral.
    for titulo, fuente, contenido in _dividir_secciones(lineas):
        if titulo.upper().startswith("IDENTIDAD"):
            resultado["identidad"]["fuente"] = fuente
        elif titulo.upper().startswith("EXPERIENCIA LABORAL"):
            resultado["experiencia_laboral"] = {"fuente": fuente, "registros": _extraer_experiencia(contenido)}
    return resultado
