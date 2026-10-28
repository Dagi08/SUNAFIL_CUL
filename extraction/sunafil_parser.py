"""
Parser de la constancia de SUNAFIL "Verifica tu Chamba".

Suele venir como captura o impresión de la web, muchas veces dentro de un PDF con otros documentos
(DNI, multas electorales, ...), así que se trabaja sobre el texto ya extraído (nativo u OCR) de cada página
y solo con las páginas que dicen "VERIFICA TU CHAMBA". Se extrae:
  - fecha_verificacion: de "Resultado de Verificación": "... se le informa que al 07 de mayo de 2026, ..."
  - ruc: el RUC de esa misma frase ("... con número de RUC 20555241811.")
  - fecha_ingreso: columna "Fecha de Ingreso" de la fila de la tabla con ese RUC
  - registros: todas las filas de la tabla (ruc, fecha_ingreso)
"""
import re
from datetime import date, datetime

from classification.rule_classifier import PALABRAS_CLAVE, normalizar
from models.document import ResultadoExtraccion

MESES = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "SETIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12,
}
# Sobre texto normalizado (mayúsculas, sin tildes). Se omite "informa" porque el OCR a veces la deforma.
RE_FECHA_VERIFICACION = re.compile(r"QUE AL (\d{1,2}) DE ([A-Z]+) DE (\d{4})")
RE_RUC_FRASE = re.compile(r"RUC\s*:?\s*(\d{11})")
RE_FILA_RUC = re.compile(r"^\s*(\d{11})\b")  # las filas de la tabla empiezan con el RUC
RE_FECHA = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
FIN_TABLA = "MOSTRANDO REGISTROS"

def _fecha_en_letras(texto: str) -> str | None:
    """'... QUE AL 07 DE MAYO DE 2026 ...' -> '07/05/2026'"""
    m = RE_FECHA_VERIFICACION.search(texto)
    if not m or m[2] not in MESES:
        return None
    try:
        return date(int(m[3]), MESES[m[2]], int(m[1])).strftime("%d/%m/%Y")
    except ValueError:
        return None

def _filas_tabla(lineas: list[str]) -> list[dict]:
    """
    Cada fila empieza con el RUC; su Fecha de Ingreso es la primera fecha dd/mm/aaaa que aparece antes
    de la siguiente fila. Sirve tanto para OCR (fila en una línea) como para texto nativo (una celda por línea).
    """
    filas = []
    for linea in lineas:
        if FIN_TABLA in linea:
            break
        if m := RE_FILA_RUC.match(linea):
            filas.append({"ruc": m[1], "fecha_ingreso": None})
            linea = linea[m.end():]
        if filas and filas[-1]["fecha_ingreso"] is None and (f := RE_FECHA.search(linea)):
            filas[-1]["fecha_ingreso"] = f[1]
    return filas

def _parsear_pagina(texto: str) -> dict:
    lineas = [normalizar(l) for l in texto.splitlines()]
    texto_corrido = " ".join(lineas)

    registros = _filas_tabla(lineas)
    m_ruc = RE_RUC_FRASE.search(texto_corrido)
    ruc = m_ruc[1] if m_ruc else (registros[0]["ruc"] if registros else None)
    fila = next((r for r in registros if r["ruc"] == ruc), registros[0] if registros else None)
    return {
        "ruc": ruc,
        "fecha_ingreso": fila["fecha_ingreso"] if fila else None,
        "fecha_verificacion": _fecha_en_letras(texto_corrido),
        "registros": registros,
    }

def _ordenar_por_fecha(texto: str | None) -> datetime:
    try:
        return datetime.strptime(texto or "", "%d/%m/%Y")
    except ValueError:
        return datetime.min

def extraer_sunafil(resultados: list[ResultadoExtraccion]) -> dict | None:
    """
    Datos de la constancia SUNAFIL entre todos los archivos de la solicitud.
    Si hay más de una, se usa la de fecha de verificación más reciente. None si no hay ninguna.
    """
    frase = PALABRAS_CLAVE["SUNAFIL"]
    encontradas = []
    for r in resultados:
        for pagina in r.paginas:
            if frase in normalizar(pagina.texto):
                datos = _parsear_pagina(pagina.texto)
                encontradas.append({"archivo": r.archivo, "nombre_original": r.nombre_original,
                                    "pagina": pagina.numero, **datos})
    if not encontradas:
        return None
    return max(encontradas, key=lambda s: _ordenar_por_fecha(s["fecha_verificacion"]))
