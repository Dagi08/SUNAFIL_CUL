import re
import unicodedata
from models.document import ResultadoExtraccion

# Tipo de documento -> frase que lo identifica (se compara sobre texto normalizado: mayúsculas, sin tildes)
PALABRAS_CLAVE = {
    "SUNAFIL": "VERIFICA TU CHAMBA",
    "CUL": "CERTIFICADO UNICO LABORAL",
    "BOLETA": "BOLETA",
}

# Documentos que reemplazan al CUL / SUNAFIL. No son columna del Excel, solo cambian OBSERVACION y MENSAJE.
# - PENSION_MP: boleta de pensión de la Caja de Pensiones Militar Policial (policías y militares en retiro).
PENSION_MP = "PENSION_MP"
FRASE_PENSION_MP = "CAJA DE PENSIONES MILITAR POLICIAL"

# Tipo sustituto -> MENSAJE, en orden de prioridad (si la solicitud tiene varios, va el primero)
MENSAJES_SUSTITUTOS = {
    PENSION_MP: "PENSION MILITAR O POLICIA",
}

def normalizar(texto: str) -> str:
    """Mayúsculas, sin tildes y con saltos de línea/espacios colapsados (la frase puede venir partida en líneas)."""
    texto = unicodedata.normalize("NFKD", texto.upper()).encode("ascii", "ignore").decode("utf-8")
    return re.sub(r"\s+", " ", texto)

def detectar_tipos(resultado: ResultadoExtraccion) -> set[str]:
    """Tipos de documento encontrados en cualquier página del archivo."""
    texto = normalizar(" ".join(p.texto for p in resultado.paginas))
    tipos = {tipo for tipo, frase in PALABRAS_CLAVE.items() if frase in texto}
    if FRASE_PENSION_MP in texto:
        tipos.add(PENSION_MP)
    return tipos

OBS_OK = "OK"
OBS_REGULARIZAR = "Regularizar SUNAFIL / CUL"

def observacion(tipos: dict[str, bool]) -> str:
    """OK si la solicitud tiene CUL, SUNAFIL o un documento que los reemplaza; si no, se debe regularizar."""
    validos = ["CUL", "SUNAFIL", *MENSAJES_SUSTITUTOS]
    return OBS_OK if any(tipos.get(t) for t in validos) else OBS_REGULARIZAR

def mensaje_sustituto(tipos: dict[str, bool]) -> str | None:
    """MENSAJE del documento que reemplaza al CUL / SUNAFIL (pensión militar/policial), si hay."""
    return next((msj for tipo, msj in MENSAJES_SUSTITUTOS.items() if tipos.get(tipo)), None)

def resumir_instancia(resultados: list[ResultadoExtraccion]) -> dict[str, bool]:
    """{"SUNAFIL", "CUL", "BOLETA", "PENSION_MP": bool} considerando todos los archivos de la instancia."""
    encontrados = set().union(*(detectar_tipos(r) for r in resultados))
    return {tipo: tipo in encontrados for tipo in [*PALABRAS_CLAVE, *MENSAJES_SUSTITUTOS]}
