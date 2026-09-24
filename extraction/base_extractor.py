import logging
from abc import ABC, abstractmethod
from pathlib import Path
from models.document import Pagina, ResultadoExtraccion

logger = logging.getLogger(__name__)

class BaseExtractor(ABC):
    """Interfaz común: cualquier motor (OCR, Donut, ...) recibe un archivo y devuelve sus páginas."""

    @abstractmethod
    def extraer(self, ruta: Path) -> list[Pagina]:
        ...

    def procesar(self, ruta: Path, nombre_original: str | None = None) -> ResultadoExtraccion:
        """Extrae un archivo sin cortar el lote si falla: el error queda en el resultado."""
        resultado = ResultadoExtraccion(archivo=str(ruta), nombre_original=nombre_original)
        try:
            resultado.paginas = self.extraer(ruta)
            logger.info(f"Extraído: {ruta.name} ({len(resultado.paginas)} páginas)")
        except Exception as e:
            resultado.error = str(e)
            logger.error(f"Error extrayendo {ruta}: {e}")
        return resultado
