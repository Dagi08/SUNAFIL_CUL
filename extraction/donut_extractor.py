from pathlib import Path
from extraction.base_extractor import BaseExtractor
from models.document import Pagina

class DonutExtractor(BaseExtractor):
    """Placeholder: se implementará cuando se evalúe el modelo Donut."""

    def extraer(self, ruta: Path) -> list[Pagina]:
        raise NotImplementedError("DonutExtractor aún no está implementado")
