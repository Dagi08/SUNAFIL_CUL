from dataclasses import dataclass, field

@dataclass
class Pagina:
    """Unidad atómica de extracción: 1 página de PDF, 1 imagen, o 1 bloque de un Word."""
    numero: int
    metodo: str   # "texto_nativo" | "ocr"
    texto: str

@dataclass
class ResultadoExtraccion:
    archivo: str
    nombre_original: str | None = None
    paginas: list[Pagina] = field(default_factory=list)
    error: str | None = None
