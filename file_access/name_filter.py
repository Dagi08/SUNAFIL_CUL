import re
import unicodedata

# Palabras clave que identifican el tipo de documento a excluir
PATRONES_EXCLUIDOS = [
    "hoja resumen",                          # Hoja Resumen Crédito vehicular PN nv2...
    "pagare",                                # Pagare casado / Pagare soltero
    "contrato de credito",                   # Contrato+de+crédito+Consumo+PF...
    "contrato de garantia",                  # Contrato+de+garantía+Legalizado...
    "gpg",                                   # GPG - DNI y Multas
    "cronograma",                            # Cronograma - PN... / Cronograma PN Con conyuge...
    "formulario de conocimiento de familiares", # 3+FORMULARIO+DE+CONOCIMIENTO+DE+FAMILIARES+PEP
    "hunter resumen",                        # Hunter+Resumen+de+condiciones+GPS
    "certificado de condiciones",            # CERTIFICADO+de+condiciones+Qualitas
    "desgravamen",                           # Desgravamen Base Cliente...
    "carta aprobacion",                      # CartaAprobacionINS_817681OP...
    "reporte persona",                       # Reporte_Persona_Natural
]

def _normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r"[+_\-]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def es_archivo_excluido(nombre_original: str) -> bool:
    if not nombre_original:
        return False
    nombre_normalizado = _normalizar(nombre_original)
    return any(patron in nombre_normalizado for patron in PATRONES_EXCLUIDOS)
