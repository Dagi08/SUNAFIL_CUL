import re
import unicodedata
from models.document import ResultadoExtraccion

# Tipo de documento -> frase que lo identifica (se compara sobre texto normalizado: mayúsculas, sin tildes)
PALABRAS_CLAVE = {
    "SUNAFIL": "VERIFICA TU CHAMBA",
    "CUL": "CERTIFICADO UNICO LABORAL",
    "BOLETA": "BOLETA",
}

def normalizar(texto: str) -> str:
    """Mayúsculas, sin tildes y con saltos de línea/espacios colapsados (la frase puede venir partida en líneas)."""
    texto = unicodedata.normalize("NFKD", texto.upper()).encode("ascii", "ignore").decode("utf-8")
    return re.sub(r"\s+", " ", texto)

def detectar_tipos(resultado: ResultadoExtraccion) -> set[str]:
    """Tipos de documento encontrados en cualquier página del archivo."""
    texto = normalizar(" ".join(p.texto for p in resultado.paginas))
    return {tipo for tipo, frase in PALABRAS_CLAVE.items() if frase in texto}

OBS_OK = "OK"
OBS_REGULARIZAR = "Regularizar SUNAFIL / CUL"

def observacion(tipos: dict[str, bool]) -> str:
    """OK si la solicitud tiene CUL o SUNAFIL; si no tiene ninguno, se debe regularizar."""
    return OBS_OK if tipos["CUL"] or tipos["SUNAFIL"] else OBS_REGULARIZAR

def resumir_instancia(resultados: list[ResultadoExtraccion]) -> dict[str, bool]:
    """{"SUNAFIL": bool, "CUL": bool, "BOLETA": bool} considerando todos los archivos de la instancia."""
    encontrados = set().union(*(detectar_tipos(r) for r in resultados))
    return {tipo: tipo in encontrados for tipo in PALABRAS_CLAVE}
